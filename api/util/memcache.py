import time
import json
from pymemcache.client.base import PooledClient
from util.logger import logger, timed
from const import MEMCACHE_LIMIT
import util.defaults as default


class JsonSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return value.encode("utf-8"), 1
        return json.dumps(value).encode("utf-8"), 2

    def deserialize(self, key, value, flags):
        if flags == 1:
            return value.decode("utf-8")
        if flags == 2:
            return json.loads(value.decode("utf-8"))
        raise Exception("Unknown serialization format")


try:
    MEMCACHE = PooledClient(
        ("memcached", 11211), serde=JsonSerde(), timeout=10, max_pool_size=250
    )
    MEMCACHE.get("test")
    logger.info("Connected to memcached docker container")
except:
    MEMCACHE = PooledClient(
        ("localhost", 11211), serde=JsonSerde(), timeout=10, max_pool_size=250
    )
    MEMCACHE.get("test")
    logger.info("Connected to memcached on localhost")
MEMCACHE.cache_memlimit = MEMCACHE_LIMIT


def set_coins(data):
    update("coins", data, 86400)


def get_coins():
    data = get("coins")
    return data


def set_coins_config(data):
    update("coins_config", data, 86400)


def get_coins_config():
    data = get("coins_config")
    return data


def set_gecko_source(data):
    update("gecko_source", data, 900)


def get_gecko_source():
    data = get("gecko_source")
    return data


def set_last_traded(data):
    update("generic_last_traded", data, 900)


def get_last_traded():
    data = get("generic_last_traded")
    return data


def set_tickers(data):
    update("generic_tickers", data, 900)


def get_tickers():
    data = get("generic_tickers")
    return data


def set_adex_fortnite(data):
    update("adex_fortnite", data, 900)


def get_adex_fortnite():
    data = get("adex_fortnite")
    return data


def set_statsapi_summary(data):
    update("statsapi_summary", data, 900)


def get_statsapi_summary():
    data = get("statsapi_summary")
    return data


def set_fixer_rates(data):
    update("fixer_rates", data, 900)


def get_fixer_rates():
    return get("fixer_rates")


def get(key):
    i = 0
    while i < 7:
        cached = None
        try:
            cached = MEMCACHE.get(key)
        except OSError:
            time.sleep(0.1)
        if cached is not None:
            # logger.info(f"Using cache for '{key}'")
            return cached
        i += 1
    if "orderbook" not in key:
        logger.warning(f"Failed to get '{key}' from memcache")
    return None


@timed
def update(key, value, expiry):
    if value is not None:
        MEMCACHE.set(key, value, expiry)
        default.result(data=None, msg=f"{key} memcache updated", loglevel="cache")
    default.result(
        data=None, msg=f"{key} memcache not updated, data is empty", loglevel="warning"
    )
