#!/usr/bin/env python3
from decimal import Decimal
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from util.cron import cron
from typing import List
import db.sqldb as db
from lib.cache import Cache
from lib.cache_calc import CacheCalc
from lib.pair import Pair
from models.generic import ErrorMessage
from models.stats_api import (
    StatsApiAtomicdexIo,
    StatsApiSummary,
    StatsApiOrderbook,
    StatsApiTradeInfo,
)
from util.logger import logger
import util.memcache as memcache
import util.transform as transform
import util.validate as validate
from util.transform import (
    deplatform,
    derive,
    invert,
    sortdata,
    convert
)

router = APIRouter()
cache = Cache()


@router.get(
    "/atomicdexio",
    description="Simple summary statistics for the Komodo Defi network.",
    response_model=StatsApiAtomicdexIo,
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def atomicdexio():
    try:
        cache = Cache(netid="ALL")
        tickers_data = cache.get_item(name="generic_tickers").data
        # TODO: Move to new DB
        query = db.SqlQuery()
        counts = query.swap_counts()
        counts.update({"current_liquidity": tickers_data["combined_liquidity_usd"]})
        return counts

    except Exception as e:  # pragma: no cover
        err = {"error": f"Error in [/api/v3/stats-api/atomicdexio]: {e}"}
        logger.warning(err)
        return JSONResponse(status_code=400, content=err)


# TODO: Cache this
@router.get("/atomicdex_fortnight")
def atomicdex_fortnight():
    """Extra Summary Statistics over last 2 weeks"""
    try:
        pass
        # return memcache.get_adex_fortnite()
    except Exception as e:  # pragma: no cover
        msg = f"{type(e)} Error in [/api/v3/stats-api/atomicdex_fortnight]: {e}"
        logger.warning(msg)
        return {"error": msg}


# TODO: Cache this
@router.get(
    "/summary",
    description="Pair summary for last 24 hours for all pairs traded in last 7 days.",
    responses={406: {"model": ErrorMessage}},
    response_model=List[StatsApiSummary],
    status_code=200,
)
def summary():
    try:
        data = CacheCalc().stats_api_summary()
        return data
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/stats-api/summary]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/stats-api/atomicdexio]: {e}"}


@router.get(
    "/ticker",
    description="Simple last price and liquidity for each market pair, traded in last 7 days.",
)
def ticker():
    try:
        data = memcache.get_tickers()
        resp = []
        for i in data["data"]:
            resp.append(transform.ticker_to_market_ticker(i))
        return resp
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/stats-api/ticker]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/stats-api/ticker]: {e}"}


@router.get(
    "/orderbook/{pair_str}",
    description="Returns live orderbook for a compatible pair (e.g. `KMD_LTC` ).",
    response_model=StatsApiOrderbook,
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def orderbook(
    pair_str: str = "KMD_LTC",
    depth: int = 100,
):
    try:
        depair = deplatform.pair(pair_str)
        is_reversed = pair_str != sortdata.pair_by_market_cap(pair_str)
        if is_reversed:
            cache_name = f"orderbook_{invert.pair(depair)}_ALL"
        else:
            cache_name = f"orderbook_{depair}_ALL"

        data = memcache.get(cache_name)
        if data is None:
            pair = Pair(pair_str=pair_str)
            data = pair.orderbook(pair_str=pair_str, depth=depth, no_thread=True)["ALL"]
        if Decimal(data["liquidity_usd"]) > 0:
            if is_reversed:
                data = invert.pair_orderbook(data)

        data = convert.orderbook_to_gecko(data)
        return data
    except Exception as e:  # pragma: no cover
        err = {"error": f"{e}"}
        logger.warning(err)
        return JSONResponse(status_code=400, content=err)


@router.get(
    "/trades/{ticker_id}",
    description="Trade history for CoinGecko compatible pairs. Use format `KMD_LTC`",
    response_model=List[StatsApiTradeInfo],
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def trades(
    ticker_id: str = "KMD_LTC", limit: int = 100, start_time: int = 0, end_time: int = 0
):
    try:
        for value, name in [
            (limit, "limit"),
            (start_time, "start_time"),
            (end_time, "end_time"),
        ]:
            validate.positive_numeric(value, name)
        if start_time == 0:
            start_time = int(cron.now_utc() - 86400)
        if end_time == 0:
            end_time = int(cron.now_utc())
        if start_time > end_time:
            raise ValueError("start_time must be less than end_time")
        pair = Pair(pair_str=ticker_id)
        data = pair.historical_trades(
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )["ALL"]
        resp = data["buy"] + data["sell"]
        resp = sortdata.dict_lists(resp, "timestamp", True)
        return resp
    except Exception as e:  # pragma: no cover
        err = {"error": f"{e}"}
        logger.warning(err)
        return JSONResponse(status_code=400, content=err)


@router.get(
    "/last_price/{pair_str}",
    description="Price of last trade for pair. Use format `KMD_LTC`",
    response_model=float,
    responses={406: {"model": ErrorMessage}},
    status_code=200,
)
def last_price_for_pair(pair_str="KMD_LTC"):
    """Last trade price for a given pair."""
    try:
        pairs_last_trade_cache = memcache.get_pair_last_traded()
        data = derive.last_trade_info(
            pair_str, pairs_last_trade_cache=pairs_last_trade_cache
        )
        return data["last_swap_price"]
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v1/last_price/{pair_str}]: {e}")
        return {"error": f"{type(e)} Error in [/api/v1/atomicdexio]: {e}"}
