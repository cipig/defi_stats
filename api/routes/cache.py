#!/usr/bin/env python3
import time
import inspect
from fastapi import APIRouter
from fastapi_utils.tasks import repeat_every
from lib.cache import Cache
from lib.cache_item import CacheItem
from db.sqlitedb import update_master_sqlite_dbs
from util.enums import NetId
from lib.external import FixerAPI, CoinGeckoAPI
from const import NODE_TYPE
from util.logger import get_trace, StopWatch

get_stopwatch = StopWatch

router = APIRouter()

# Pure Upstream Data Sourcing


@router.on_event("startup")
@repeat_every(seconds=60)
def coins():  # pragma: no cover
    start = int(time.time())
    stack = inspect.stack()[0]
    context = get_trace(stack)
    try:
        coins_cache = CacheItem("coins")
        coins_cache.save()
        coins_config_cache = CacheItem("coins_config")
        coins_config_cache.save()
    except Exception as e:
        error = f"{type(e)}: {e}"
        context = get_trace(stack, error)
        get_stopwatch(start, error=True, context=f"CacheLoop.coins | {context}")
        return
    get_stopwatch(start, loop=True, context="CacheLoop.coins | complete!")


@router.on_event("startup")
@repeat_every(seconds=60)
def gecko_data():  # pragma: no cover
    start = int(time.time())
    stack = inspect.stack()[0]
    context = get_trace(stack)
    try:
        cache = Cache()
        gecko_cache = cache.get_item("gecko_source")
        data = CoinGeckoAPI().get_gecko_source()
        gecko_cache.save(data)
    except Exception as e:
        error = f"{type(e)}: {e}"
        context = get_trace(stack, error)
        get_stopwatch(start, error=True, context=f"gecko_data | {context}")
        return
    get_stopwatch(
        start,
        loop=True,
        context="CacheLoop.gecko_data | complete!",
    )


@router.on_event("startup")
@repeat_every(seconds=60)
def prices_service():  # pragma: no cover
    start = int(time.time())
    stack = inspect.stack()[0]
    context = get_trace(stack)
    try:
        cache = Cache()
        prices_tickers_v1_cache = cache.get_item("prices_tickers_v1")
        prices_tickers_v1_cache.save()
    except Exception as e:
        error = f"{type(e)}: {e}"
        context = get_trace(stack, error)
        get_stopwatch(start, error=True, context=context)
        return
    try:
        cache = Cache()
        prices_tickers_v2_cache = cache.get_item("prices_tickers_v2")
        prices_tickers_v2_cache.save()
    except Exception as e:
        error = f"{type(e)}: {e}"
        context = get_trace(stack, error)
        get_stopwatch(start, error=True, context=context)
        return
    get_stopwatch(
        start,
        loop=True,
        context="CacheLoop.prices_service | prices service updated",
    )


@router.on_event("startup")
@repeat_every(seconds=600)
def fixer_rates():  # pragma: no cover
    start = int(time.time())
    stack = inspect.stack()[0]
    try:
        cache = Cache()
        fixer = FixerAPI()
        fixer_rates_cache = cache.get_item("fixer_rates")
        fixer_rates_cache.save(fixer.latest())
    except Exception as e:
        error = f"{type(e)}: {e}"
        context = get_trace(stack, error)
        get_stopwatch(start, error=True, context=context)
        return
    get_stopwatch(
        start,
        loop=True,
        context="CacheLoop.fixer_rates | fixer source updated",
    )


# Derived Cache data for Gecko endpoints


@router.on_event("startup")
@repeat_every(seconds=10)
def gecko_pairs():
    start = int(time.time())
    stack = inspect.stack()[0]
    try:
        cache = Cache(netid="ALL")
        gecko_pairs_cache = cache.get_item("gecko_pairs")
        data = cache.calc.traded_pairs(days=7)
        resp = gecko_pairs_cache.save(data)

    except Exception as e:
        error = f"{type(e)}: {e}"
        context = get_trace(stack, error)
        get_stopwatch(start, error=True, context=context)
        return
    get_stopwatch(
        start,
        loop=True,
        context=f"CacheLoop.gecko_pairs | updated with {resp[1]} pairs",
    )


@router.on_event("startup")
@repeat_every(seconds=10)
def gecko_tickers():
    start = int(time.time())
    stack = inspect.stack()[0]
    try:
        cache = Cache(netid="ALL")
        gecko_tickers_cache = CacheItem(name="gecko_tickers", netid="ALL")
        data = cache.calc.traded_tickers(pairs_days=7)
        resp = gecko_tickers_cache.save(data)
        context = f"{resp[1]} pairs"
    except Exception as e:
        error = f"{type(e)}: {e}"
        context = get_trace(stack, error)
        get_stopwatch(start, error=True, context=context)
        return
    get_stopwatch(
        start,
        loop=True,
        context=f"CacheLoop.gecko_tickers | updated with {resp[1]} pairs",
    )


# Stats-API Cache

"""
@router.on_event("startup")
@repeat_every(seconds=60)
def gecko_data():  # pragma: no cover
    try:
        cache.save.gecko_data()
    except Exception as e:
        logger.warning(f"{type(e)} Error in [gecko_data]: {e}")


@router.on_event("startup")
@repeat_every(seconds=60)
def summary():  # pragma: no cover
    try:
        cache.save.summary()
    except Exception as e:
        logger.warning(f"{type(e)} Error in [summary_data]: {e}")


@router.on_event("startup")
@repeat_every(seconds=60)
def ticker():  # pragma: no cover
    try:
        cache.save.ticker()
    except Exception as e:
        logger.warning(f"{type(e)} Error in [ticker_data]: {e}")


@router.on_event("startup")
@repeat_every(seconds=600)  # caching data every 10 minutes
def atomicdexio():  # pragma: no cover
    try:
        cache.save.atomicdexio()
    except Exception as e:
        logger.warning(f"{type(e)} Error in [atomicdex_io]: {e}")


@router.on_event("startup")
@repeat_every(seconds=600)  # caching data every 10 minutes
def atomicdex_fortnight():  # pragma: no cover
    try:
        cache.save.atomicdex_fortnight()
    except Exception as e:
        logger.warning(f"{type(e)} in [atomicdex_io_fortnight]: {e}")
"""

# Derived Cache data for Markets endpoints


@router.on_event("startup")
@repeat_every(seconds=10)
def markets_last_trade():
    # This one is fast, so can do all netids in seq in same func
    start = int(time.time())
    stack = inspect.stack()[0]
    for netid in NetId:
        try:
            cache = Cache(netid=netid.value)
            cache_item = CacheItem("markets_last_trade")
            data = cache.calc.pairs_last_trade()
            resp = cache_item.save(data)
            if resp is None:
                get_stopwatch(
                    start,
                    warning=True,
                    context=f"CacheLoop.markets_last_trade | empty resp for {netid.value}",
                )
            else:
                context = f"{resp[1]} pairs"
                get_stopwatch(
                    start,
                    loop=True,
                    context=f"CacheLoop.markets_last_trade | updated for netid {netid.value}",
                )

        except Exception as e:
            error = f"{type(e)}: {e} [CacheLoop.markets_last_trade] ({netid})]"
            context = get_trace(stack, error)
            get_stopwatch(start, error=True, context=context)


@router.on_event("startup")
@repeat_every(seconds=10)
def markets_pairs(netid):
    start = int(time.time())
    stack = inspect.stack()[0]
    try:
        cache = Cache(netid=netid)
        cache_item = CacheItem(name="markets_pairs", netid=netid)
        data = cache.calc.traded_pairs(days=120)
        if len(data) > 0:
            resp = cache_item.save(data)
            get_stopwatch(
                start,
                loop=True,
                context=f"updated markets_pairs_{netid} cache with {resp[1]} pairs",
            )
            return
    except Exception as e:
        error = f"{type(e)}: {e}"
        context = get_trace(stack, error)
        get_stopwatch(start, error=True, context=context)
        return
    get_stopwatch(
        start,
        warning=True,
        context=f"CacheLoop.markets_pairs_{netid} | No data from cache.calc_markets_pairs()",
    )


@router.on_event("startup")
@repeat_every(seconds=10)
def markets_pairs_7777():
    markets_pairs("7777")


@router.on_event("startup")
@repeat_every(seconds=10)
def markets_pairs_8762():
    markets_pairs("8762")


@router.on_event("startup")
@repeat_every(seconds=10)
def markets_pairs_ALL():
    markets_pairs("ALL")


def markets_tickers(netid):
    start = int(time.time())
    stack = inspect.stack()[0]
    try:
        cache = Cache(netid=netid)
        cache_item = CacheItem(name="markets_tickers", netid=netid)
        data = cache.calc.traded_tickers(pairs_days=120)
        if data is not None:
            context = (
                f"{len(data)} results from cache.calc.markets_tickers() [netid {netid}]"
            )
        else:
            context = f"{data} data from cache.calc.markets_tickers() [netid {netid}]"
            get_stopwatch(start, info=True, context=context)
        resp = cache_item.save(data)
        context = f"CacheLoop.markets_tickers_{netid} | "
        context += f"updated markets_tickers_{netid} cache with {resp[1]} pairs"
        get_stopwatch(start, loop=True, context=context)
    except Exception as e:
        error = f"{type(e)}: {e} [netid {netid}]"
        context = get_trace(stack, error)
        get_stopwatch(start, error=True, context=context)
        return


@router.on_event("startup")
@repeat_every(seconds=10)
def markets_tickers_7777():
    markets_tickers("7777")


@router.on_event("startup")
@repeat_every(seconds=10)
def markets_tickers_8762():
    markets_tickers("8762")


@router.on_event("startup")
@repeat_every(seconds=10)
def markets_tickers_all():
    markets_tickers("ALL")


# Processing Loops


@router.on_event("startup")
@repeat_every(seconds=60)
def import_dbs():
    start = int(time.time())
    stack = inspect.stack()[0]
    context = get_trace(stack)
    if NODE_TYPE != "serve":
        try:
            update_master_sqlite_dbs()
        except Exception as e:
            error = f"CacheLoop.import_dbs | {type(e)}: {e}"
            context = get_trace(stack, error)
            get_stopwatch(start, error=True, context=context)
            return
        get_stopwatch(
            start,
            loop=True,
            context="CacheLoop.import_dbs | Source database imports complete!",
        )
        return
    get_stopwatch(
        start,
        muted=True,
        context="CacheLoop.import_dbs | Node type is serve, not importing databases",
    )
