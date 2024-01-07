#!/usr/bin/env python3
from fastapi import APIRouter
from fastapi_utils.tasks import repeat_every
from const import MARKETS_PAIRS_DAYS
from db.sqlitedb_merge import SqliteMerge
from lib.cache import Cache
from lib.cache_item import CacheItem
from lib.external import FixerAPI, CoinGeckoAPI
from lib.generics import Generics
from lib.markets import Markets
from util.defaults import default_error, default_result
from util.logger import timed, logger
from util.validate import validate_loop_data
from const import GENERIC_PAIRS_DAYS


router = APIRouter()


@router.on_event("startup")
@repeat_every(seconds=300)
@timed
def check_cache():  # pragma: no cover
    try:
        cache = Cache()
        for i in [
            "coins_config",
            "gecko_source",
            "coins",
            "generic_pairs",
            "generic_last_traded",
            "fixer_rates",
            "prices_tickers_v1",
            "prices_tickers_v2",
        ]:
            item = cache.get_item(i)
            since_updated = item.since_updated_min()
            logger.loop(f"[{i}] last updated: {since_updated} min")
    except Exception as e:
        return default_error(e)


# Pure Upstream Data Sourcing


@router.on_event("startup")
@repeat_every(seconds=86400)
@timed
def coins():  # pragma: no cover
    try:
        logger.loop("Init coins source update")
        for i in ["coins", "coins_config"]:
            cache_item = CacheItem("coins")
            cache_item.save()
    except Exception as e:
        return default_error(e)
    return default_result("Coins update loop complete!", loglevel="loop")


@router.on_event("startup")
@repeat_every(seconds=300)
@timed
def gecko_data():  # pragma: no cover
    try:
        logger.loop("Init gecko source update")
        cache = Cache()
        cache_item = cache.get_item("gecko_source")
        data = CoinGeckoAPI().get_gecko_source()
        cache_item.save(data)
    except Exception as e:
        return default_error(e)
    msg = "Gecko data update loop complete!"
    return default_result(msg=msg, loglevel="loop")


@router.on_event("startup")
@repeat_every(seconds=60)
@timed
def prices_service():  # pragma: no cover
    try:
        logger.loop("Init prices_service source update")
        for i in ["prices_tickers_v1", "prices_tickers_v2"]:
            cache_item = CacheItem(i)
            cache_item.save()
    except Exception as e:
        return default_error(e)
    msg = "Prices update loop complete!"
    return default_result(msg=msg, loglevel="loop")


@router.on_event("startup")
@repeat_every(seconds=900)
@timed
def fixer_rates():  # pragma: no cover
    try:
        logger.loop("Init fixer_rates source update")
        cache = Cache()
        fixer = FixerAPI()
        cache_item = cache.get_item("fixer_rates")
        cache_item.save(fixer.latest())
    except Exception as e:
        return default_error(e)
    msg = "Fixer rates update loop complete!"
    return default_result(msg=msg, loglevel="loop")


# Derived Cache data for Gecko endpoints


@router.on_event("startup")
@repeat_every(seconds=60)
@timed
def gecko_tickers():
    try:
        logger.loop("Init gecko_tickers source update")
        cache = Cache(netid="ALL")
        cache_item = cache.get_item(name="gecko_tickers")
        generics = Generics(netid="ALL")
        data = generics.traded_tickers(pairs_days=7)
        if validate_loop_data(data, cache_item, "ALL"):
            cache_item.save(data)
    except Exception as e:
        return default_error(e)
    msg = "Gecko tickers (ALL) loop complete!"
    return default_result(msg=msg, loglevel="loop")


# Derived Cache data for Markets endpoints


@timed
def markets_pairs(netid):
    try:
        cache = Cache(netid=netid)
        cache_item = cache.get_item(name="markets_pairs")
        markets = Markets(netid=netid)
        data = markets.pairs(days=MARKETS_PAIRS_DAYS)
        if validate_loop_data(data, cache_item, netid):
            cache_item.save(data)
    except Exception as e:
        msg = f"Markets pairs update failed! ({netid}): {e}"
        return default_error(e, msg)


@timed
def markets_tickers(netid):
    try:
        cache = Cache(netid=netid)
        cache_item = cache.get_item(name="markets_tickers")
        markets = Markets(netid=netid)
        data = markets.tickers(pairs_days=MARKETS_PAIRS_DAYS)
        if validate_loop_data(data, cache_item, netid):
            cache_item.save(data)
    except Exception as e:
        msg = f"Failed for netid {netid}!"
        return default_error(e, msg)
    return default_result(
        msg=f"Market Tickers for netid {netid} Updated!", loglevel="loop"
    )


@router.on_event("startup")
@repeat_every(seconds=60)
@timed
def markets_tickers_7777():
    markets_tickers("7777")
    msg = "Market tickers (7777) loop complete!"
    return default_result(msg=msg, loglevel="loop")


@router.on_event("startup")
@repeat_every(seconds=60)
@timed
def markets_tickers_8762():
    markets_tickers("8762")
    msg = "Market tickers (8762) loop complete!"
    return default_result(msg=msg, loglevel="loop")


@router.on_event("startup")
@repeat_every(seconds=60)
@timed
def markets_tickers_all():
    markets_tickers("ALL")
    msg = "Market tickers (all) loop complete!"
    return default_result(msg=msg, loglevel="loop")


# Processing Loops


@router.on_event("startup")
@repeat_every(seconds=60)
@timed
def generic_last_traded():
    try:
        cache = Cache(netid="ALL")
        cache_item = cache.get_item(name="generic_last_traded")
        generics = Generics(netid="ALL")
        data = generics.last_traded()
        if validate_loop_data(data, cache_item, "ALL"):
            cache_item.save(data)
    except Exception as e:
        return default_error(e)
    msg = "Generic tickers (ALL) loop complete!"
    return default_result(msg=msg, loglevel="loop")


@router.on_event("startup")
@repeat_every(seconds=60)
@timed
def generic_pairs():
    try:
        cache = Cache(netid="ALL")
        cache_item = cache.get_item(name="generic_pairs")
        generics = Generics(netid="ALL")
        data = generics.traded_pairs_info(days=GENERIC_PAIRS_DAYS)
        if validate_loop_data(data, cache_item, "ALL"):
            cache_item.save(data)
    except Exception as e:
        return default_error(e)
    msg = "Generic tickers (ALL) loop complete!"
    return default_result(msg=msg, loglevel="loop")


@router.on_event("startup")
@repeat_every(seconds=600)
@timed
def import_dbs():
    NODE_TYPE = "noserve"
    if NODE_TYPE != "serve":
        try:
            merge = SqliteMerge()
            merge.import_source_databases()
        except Exception as e:
            return default_error(e)
        msg = "Import source databases loop complete!"
        return default_result(msg=msg, loglevel="loop")
