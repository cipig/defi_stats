#!/usr/bin/env python3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from decimal import Decimal
from datetime import datetime, timedelta
import time
from typing import List, Dict
from const import MARKETS_DAYS
from db.sqlitedb import get_sqlite_db
from lib.models import ErrorMessage
from lib.models_markets import (
    MarketsUsdVolume,
    MarketsCurrentLiquidity,
    MarketsFiatRatesItem,
    MarketsAtomicdexIo,
    MarketsOrderbookItem,
    MarketsPairLastTradeItem,
    MarketsSwaps24,
    PairTrades,
    MarketsSummaryItem,
    MarketsSummaryForTicker,
)
from lib.cache import Cache, CacheItem
from lib.generics import Generics
from lib.pair import Pair
from util.enums import TradeType, NetId
from util.logger import logger
from util.transform import (
    ticker_to_market_ticker,
    ticker_to_market_ticker_summary,
    sort_dict_list,
    to_summary_for_ticker_item,
    sum_json_key_10f,
    sum_json_key,
)
from util.transform import clean_decimal_dict


router = APIRouter()
cache = Cache()


@router.get(
    "/atomicdexio",
    description="Returns atomic swap counts over a variety of periods",
    response_model=MarketsAtomicdexIo,
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def atomicdex_info_api(netid: NetId = NetId.ALL):
    db = get_sqlite_db(netid=netid.value)
    return db.query.swap_counts()


# New endpoint
@router.get(
    "/current_liquidity",
    response_model=MarketsCurrentLiquidity,
    description="Global liquidity on the orderbook for all pairs.",
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def current_liquidity(netid: NetId = NetId.ALL):
    try:
        cache = Cache(netid=netid.value)
        data = cache.get_item(name="markets_tickers").data
        return {"current_liquidity": data["combined_liquidity_usd"]}

    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/markets/current_liquidity]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/markets/current_liquidity]: {e}"}


@router.get(
    "/fiat_rates",
    description="Coin prices in USD (where available)",
    response_model=Dict[str, MarketsFiatRatesItem],
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def fiat_rates():
    data = CacheItem("gecko_source").data
    return data


@router.get(
    "/orderbook/{market_pair}",
    description="Get Orderbook for a market pair in `KMD_LTC` format.",
    response_model=MarketsOrderbookItem,
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def orderbook(market_pair: str = "KMD_LTC", netid: NetId = NetId.ALL, depth: int = 100):
    try:
        generics = Generics(netid=netid.value)
        return generics.get_orderbook(pair_str=market_pair, depth=depth)
    except Exception as e:  # pragma: no cover
        err = {"error": f"{e}"}
        logger.warning(err)
        return JSONResponse(status_code=406, content=err)


@router.get(
    "/pairs_last_trade",
    description="Returns last trade info for all pairs matching the filter",
    response_model=List[MarketsPairLastTradeItem],
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def pairs_last_trade(
    netid: NetId = NetId.ALL,
    start_time: int = 0,
    end_time: int = int(time.time()),
    min_swaps: int = 5,
) -> list:
    data = CacheItem("markets_last_trade", netid=netid.value).data
    filtered_data = []
    for i in data:
        if data[i]["swap_count"] > min_swaps:
            if data[i]["last_swap"] > start_time:
                if data[i]["last_swap"] < end_time:
                    data[i].update({"pair": i})
                    filtered_data.append(data[i])
    return filtered_data


# Migrated from https://stats.testchain.xyz/api/v1/summary
@router.get(
    "/summary",
    description=f"24-hour price & volume for each market pair traded in last {MARKETS_DAYS} days.",
    response_model=List[MarketsSummaryItem],
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def summary(netid: NetId = NetId.ALL):
    try:
        cache = Cache(netid=netid.value)
        data = cache.get_item(name="markets_tickers").data
        resp = []
        for i in data["data"]:
            resp.append(ticker_to_market_ticker_summary(i))
        return resp
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/market/tickers]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/market/tickers]: {e}"}


# Migrated from https://stats.testchain.xyz/api/v1/summary_for_ticker/KMD
@router.get(
    "/summary_for_ticker/{coin}",
    description="24h price & volume for market pairs with a specific coin traded in last 7 days",
    response_model=MarketsSummaryForTicker,
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def summary_for_ticker(coin: str = "KMD", netid: NetId = NetId.ALL):
    # TODO: Segwit not merged in this endpoint yet
    try:
        if "_" in coin:
            return {"error": "Coin value '{coin}' looks like a pair."}
        cache = Cache(netid=netid.value)
        last_trades = cache.get_item(name="markets_last_trade").data
        resp = cache.get_item(name="markets_tickers").data
        new_data = []
        for i in resp["data"]:
            if coin in [i["base_currency"], i["target_currency"]]:
                if i["last_trade"] == 0:
                    if i["ticker_id"] in last_trades:
                        i["last_trade"] = last_trades[i["ticker_id"]]["last_swap"]
                        i["last_price"] = last_trades[i["ticker_id"]]["last_swap"]

                new_data.append(to_summary_for_ticker_item(i))

        logger.info(new_data[0])
        resp.update(
            {
                "pairs_count": len(new_data),
                "swaps_count": int(sum_json_key(new_data, "trades_24hr")),
                "liquidity_usd": sum_json_key_10f(new_data, "liquidity_usd"),
                "volume_usd_24hr": sum_json_key_10f(new_data, "volume_usd_24hr"),
                "data": new_data,
            }
        )
        return resp
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/market/summary_for_ticker]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/market/summary_for_ticker]: {e}"}


@router.get(
    "/swaps24/{ticker}",
    description="Total swaps involving a specific ticker (e.g. `KMD`) in the last 24hrs.",
    response_model=MarketsSwaps24,
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def swaps24(ticker: str = "KMD", netid: NetId = NetId.ALL) -> dict:
    try:
        cache = Cache(netid=netid.value)
        data = cache.get_item(name="markets_tickers").data
        trades = 0
        for i in data["data"]:
            if ticker in [i["base_currency"], i["target_currency"]]:
                trades += int(i["trades_24hr"])
        return {"ticker": ticker, "swaps_amount_24h": trades}
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/market/swaps24]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/market/swaps24]: {e}"}


@router.get(
    "/ticker",
    description="Simple last price and liquidity for each market pair, traded in last 7 days.",
)
def ticker(netid: NetId = NetId.ALL):
    try:
        data = cache.load_markets_tickers(netid=netid.value)
        resp = []
        for i in data["data"]:
            resp.append(ticker_to_market_ticker(i))
        return resp
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/market/ticker]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/market/ticker]: {e}"}


@router.get(
    "/ticker_for_ticker",
    description="Simple last price and liquidity for each market pair for a specific ticker.",
)
def ticker_for_ticker(ticker, netid: NetId = NetId.ALL):
    try:
        cache = Cache(netid=netid.value)
        data = cache.get_item(name="markets_tickers").data
        resp = []
        for i in data["data"]:
            if ticker in [i["base_currency"], i["target_currency"]]:
                resp.append(ticker_to_market_ticker(i))
        return resp
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/market/ticker_for_ticker]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/market/ticker_for_ticker]: {e}"}


@router.get(
    "/tickers_summary",
    description="Total swaps and volume involving for each active ticker in the last 24hrs.",
)
def tickers_summary(netid: NetId = NetId.ALL):
    try:
        data = cache.load_markets_tickers(netid=netid.value)
        resp = {}
        for i in data["data"]:
            base = i["base_currency"]
            rel = i["target_currency"]
            for ticker in [base, rel]:
                if ticker not in resp:
                    resp.update({ticker: {"trades_24h": 0, "volume_24h": 0}})
                resp[ticker]["trades_24h"] += int(i["trades_24hr"])
                if ticker == base:
                    resp[ticker]["volume_24h"] += Decimal(i["base_volume"])
                elif ticker == rel:
                    resp[ticker]["volume_24h"] += Decimal(i["target_volume"])
        resp = clean_decimal_dict(resp)
        with_action = {}
        tickers = list(resp.keys())
        tickers.sort()
        for ticker in tickers:
            if resp[ticker]["trades_24h"] > 0:
                with_action.update({ticker: resp[ticker]})
        return with_action
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/market/swaps_by_ticker_24h]: {e}")
        return {
            "error": f"{type(e)} Error in [/api/v3/market/swaps_by_ticker_24h]: {e}"
        }


@router.get(
    "/trades/{market_pair}/{days_in_past}",
    response_model=List[PairTrades],
    description="Summary of trades for the last 'x' days.",
)
def trades(
    market_pair: str = "KMD_LTC", days_in_past: int = 1, netid: NetId = NetId.ALL
):
    cache = Cache(netid=netid.value)
    data = cache.get_item(name="market_pairs").data
    try:
        if netid.value == "ALL":
            resp = []
            for x in NetId:
                if x.value != "ALL":
                    pair = Pair(pair_str=market_pair, netid=x.value)
                    data = pair.historical_trades(
                        trade_type="all",
                        start_time=int(time.time() - 86400) * days_in_past,
                        end_time=int(time.time()),
                    )
                    resp += data["buy"]
                    resp += data["sell"]
        else:
            pair = Pair(pair_str=market_pair, netid=netid.value)
            data = pair.historical_trades(
                trade_type="all",
                start_time=int(time.time() - 86400) * days_in_past,
                end_time=int(time.time()),
            )
            resp += data["buy"]
            resp += data["sell"]

        sorted_trades = sort_dict_list(resp, "timestamp", reverse=True)
        return sorted_trades
    except Exception as e:
        err = {"error": f"{e}"}
        logger.warning(err)
        return JSONResponse(status_code=406, content=err)


# Migrated from https://stats.testchain.xyz/api/v1/usd_volume_24h
@router.get(
    "/usd_volume_24h",
    response_model=MarketsUsdVolume,
    description="24-hour price & volume for each market pair traded in last 7 days.",
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def usd_volume_24h(netid: NetId = NetId.ALL):
    try:
        cache = Cache(netid=netid.value)
        data = cache.get_item(name="markets_tickers").data
        return {"usd_volume_24h": data["combined_volume_usd"]}
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/markets/usd_volume_24h]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/markets/usd_volume_24h]: {e}"}


# TODO: get volumes for x days for ticker
@router.get(
    "/volumes_ticker/{ticker}/{days_in_past}",
    description="Daily volume of a ticker traded for the last 'x' days.",
)
def volumes_history_ticker(
    ticker="KMD",
    days_in_past=1,
    trade_type: TradeType = TradeType.ALL,
    netid: NetId = NetId.ALL,
):
    db = get_sqlite_db(netid=netid.value)
    volumes_dict = {}
    for i in range(0, int(days_in_past)):
        db = get_sqlite_db(netid=netid.value)
        d = datetime.today() - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        day_ts = int(int(d.strftime("%s")) / 86400) * 86400
        # TODO: Align with midnight
        start_time = int(day_ts) - 86400
        end_time = int(day_ts)
        volumes_dict[d_str] = db.get_volume_for_ticker(
            ticker=ticker,
            trade_type=trade_type.value,
            start_time=start_time,
            end_time=end_time,
        )
        return volumes_dict
