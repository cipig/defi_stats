#!/usr/bin/env python3
from util.exceptions import CacheFilenameNotFound, CacheItemNotFound
from util.files import Files
from util.logger import logger, timed
from util.urls import Urls
from util.cron import cron
import util.defaults as default
import util.memcache as memcache
import util.validate as validate
import lib.cache_calc as cache_calc
import lib.external as external
import lib.stats_api as stats_api


class Cache:  # pragma: no cover
    def __init__(self, **kwargs):
        try:
            self.kwargs = kwargs
            self.options = []
            default.params(self, self.kwargs, self.options)
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to init Cache: {e}")

    def get_item(self, name):
        try:
            return CacheItem(name, **self.kwargs)
        except Exception as e:  # pragma: no cover
            msg = f"{type(e)} Error in [Cache.load_cache]: {e}"
            raise CacheItemNotFound(msg)

    def healthcheck(self, to_console=False):  # pragma: no cover
        try:
            updated = {}
            for i in [
                "coins",
                "coins_config",
                "fixer_rates",
                "gecko_source",
                "adex_fortnite",
                "pair_last_traded",
                "pair_volumes_24hr",
                "coin_volumes_24hr",
                "pair_orderbook_extended",
                "generic_summary",
                "generic_tickers",
                "prices_tickers_v1",
                "prices_tickers_v2",
            ]:
                item = self.get_item(i)
                since_updated = item.since_updated_min()
                updated.update({i: since_updated})
                if to_console:
                    logger.loop(f"[{i}] last updated: {since_updated} min")
            return updated
        except Exception as e:  # pragma: no cover
            logger.warning(e)


class CacheItem:
    def __init__(self, name, from_memcache: bool = False, **kwargs) -> None:
        try:
            self.name = name
            self.kwargs = kwargs
            self.from_memcache = from_memcache
            self.options = []
            self._data = {}
            default.params(self, self.kwargs, self.options)
            self.files = Files()
            self.filename = self.files.get_cache_fn(name)
            if self.filename is None:
                raise CacheFilenameNotFound(
                    f"Unable to find cache filename for '{name}'. Does it exist?"
                )

            self.urls = Urls()
            self.source_url = self.urls.get_cache_url(name)
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to init CacheItem '{name}': {e}")

    @property
    def data(self):  # pragma: no cover
        if len(self._data) is None:
            self.update_data()
        elif len(self._data) == 0:
            self.update_data()
        return self._data

    def get_data(self):
        data = self.files.load_jsonfile(self.filename)
        if data is None:  # pragma: no cover
            data = self.save()
            return {}
        if "last_updated" in data:
            since_updated = int(cron.now_utc()) - data["last_updated"]
            since_updated_min = int(since_updated / 60)
            if since_updated_min > self.cache_expiry:
                msg = f"{self.name} has not been updated for over {since_updated_min} minutes"
                logger.muted(msg)
        if "data" in data:
            return data["data"]
        return data

    def since_updated_min(self):  # pragma: no cover
        data = self.files.load_jsonfile(self.filename)
        if data is not None:
            if "last_updated" in data:
                since_updated = int(cron.now_utc()) - data["last_updated"]
                return int(since_updated / 60)
        return "unknown"

    def update_data(self):
        self._data = self.get_data()  # pragma: no cover

    @property
    def cache_expiry(self):
        expiry_limits = {
            "coins": 1440,
            "coins_config": 1440,
            "pair_last_traded": 5,
            "gecko_source": 15,
            "fixer_rates": 15,
            "pair_volumes_24hr": 15,
            "coin_volumes_24hr": 15,
            "pair_orderbook_extended": 15,
        }
        if self.name in expiry_limits:
            return expiry_limits[self.name]
        return 5

    # TODO: Cache orderbooks to file? Volumes / prices? Liquidity? Swaps?
    # The reason to do this is to reduce population times on restarts.
    @timed
    def save(self, data=None):  # pragma: no cover
        try:
            # EXTERNAL SOURCE CACHE
            if self.source_url is not None:
                data = self.files.download_json(self.source_url)
                if self.name == "coins_config":
                    memcache.set_coins_config(data)
                if self.name == "coins":
                    memcache.set_coins(data)
            else:
                # EXTERNAL SOURCE CACHE
                if self.name == "fixer_rates":
                    data = external.FixerAPI().latest()
                    memcache.set_fixer_rates(data)

                if self.name == "gecko_source":
                    data = external.CoinGeckoAPI().get_gecko_source()
                    memcache.set_gecko_source(data)

                # FOUNDATIONAL CACHE
                if self.name == "adex_fortnite":
                    data = stats_api.StatsAPI().adex_fortnite()
                    memcache.set_adex_fortnite(data)

                if self.name == "coin_volumes_24hr":
                    data = cache_calc.CacheCalc().coin_volumes_24hr()
                    memcache.set_coin_volumes_24hr(data)

                if self.name == "pair_last_traded":
                    data = cache_calc.CacheCalc().pair_last_traded()
                    memcache.set_pair_last_traded(data)

                if self.name == "pair_orderbook_extended":
                    data = cache_calc.CacheCalc().pair_orderbook_extended()
                    memcache.set_pair_orderbook_extended(data)
                    
                if self.name == "pair_volumes_24hr":
                    data = cache_calc.CacheCalc().pair_volumes_24hr()
                    memcache.set_pair_volumes_24hr(data)
                    
                # REVIEW

                if self.name == "generic_summary":
                    data = stats_api.StatsAPI().pair_summaries()
                    memcache.set_summary(data)

                if self.name == "generic_tickers":
                    data = cache_calc.CacheCalc().tickers()
                    memcache.set_tickers(data)

                if self.name == "generic_tickers_14d":
                    data = cache_calc.CacheCalc().tickers(trades_days=14)
                    memcache.set_tickers_14d(data)

            if data is not None:
                if validate.loop_data(data, self):
                    data = {"last_updated": int(cron.now_utc()), "data": data}
                    r = self.files.save_json(self.filename, data)
                    msg = f"{self.filename} saved."
                    return default.result(
                        data=data, msg=r["msg"], loglevel=r["loglevel"]
                    )
                else:
                    logger.warning(
                        f"failed to save {self.name}, data failed validation: {data}"
                    )
            else:
                logger.warning(f"failed to save {self.name}, data is 'None'")

        except Exception as e:  # pragma: no cover
            msg = f"{self.filename} Failed. {type(e)}: {e}"
            return default.error(e, msg=msg)
