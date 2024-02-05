#!/usr/bin/env python3
from util.logger import logger, timed
from util.transform import clean, sortdata, sumdata, derive
import db.sqldb as db
import util.cron as cron
import util.defaults as default
import util.helper as helper
import util.memcache as memcache
import util.transform as transform
from lib.pair import Pair


class CacheCalc:
    def __init__(self) -> None:
        self.coins_config = memcache.get_coins_config()
        self.last_traded_cache = memcache.get_last_traded()
        self.gecko_source = memcache.get_gecko_source()
        self.pg_query = db.SqlQuery()

    # FOUNDATIONAL CACHE
    @timed
    def last_traded(self):
        try:
            if self.gecko_source is None:
                self.gecko_source = memcache.get_gecko_source()
            data = self.pg_query.pair_last_trade()
            price_status_dict = derive.price_status_dict(data.keys(), self.gecko_source)
            for i in data:
                data[i] = clean.decimal_dicts(data[i])
                data[i].update(
                    {"priced": helper.get_pair_priced_status(i, price_status_dict)}
                )

            msg = "pairs_last_traded complete!"
            return default.result(data, msg, loglevel="loop")
        except Exception as e:  # pragma: no cover
            msg = f"pairs_last_traded failed! {e}"
            logger.warning(msg)

    @timed
    def coin_volumes_24hr(self):
        try:
            if self.gecko_source is None:
                self.gecko_source = memcache.get_gecko_source()
            vols = self.pg_query.coin_trade_volumes()
            vols_usd = self.pg_query.coin_trade_volumes_usd(vols, self.gecko_source)
            for coin in vols_usd["volumes"]:
                for variant in vols_usd["volumes"][coin]:
                    vols_usd["volumes"][coin][variant] = clean.decimal_dicts(
                        vols_usd["volumes"][coin][variant]
                    )
            vols_usd = clean.decimal_dicts(vols_usd)
            msg = "coin_volumes_24hr complete!"
            return default.result(vols_usd, msg, loglevel="loop")
        except Exception as e:  # pragma: no cover
            msg = f"coin_volumes_24hr failed! {e}"
            logger.warning(msg)

    @timed
    def pair_volumes_24hr(self):
        try:
            if self.gecko_source is None:
                self.gecko_source = memcache.get_gecko_source()
            vols = self.pg_query.pair_trade_volumes()
            vols_usd = self.pg_query.pair_trade_volumes_usd(vols, self.gecko_source)
            for pair_str in vols_usd["volumes"]:
                for variant in vols_usd["volumes"][pair_str]:
                    vols_usd["volumes"][pair_str][variant] = clean.decimal_dicts(
                        vols_usd["volumes"][pair_str][variant]
                    )
            vols_usd = clean.decimal_dicts(vols_usd)
            msg = "pair_volumes_24hr complete!"
            return default.result(vols_usd, msg, loglevel="loop")
        except Exception as e:  # pragma: no cover
            msg = f"pair_volumes_24hr failed! {e}"
            logger.warning(msg)

    # REVIEW
    @timed
    def tickers(
        self,
        trades_days: int = 1,
        pairs_days: int = 30,
        from_memcache: bool = False,
        all_variants: bool = False,
    ):
        try:
            if trades_days > pairs_days:
                pairs_days = trades_days
            # Skip if cache not available yet
            if self.last_traded_cache is None:
                self.last_traded_cache = memcache.get_last_traded()
                msg = "skipping cache_calc.tickers, last_traded_cache is None"
                return default.result(msg=msg, loglevel="warning", data=None)

            # Skip if cache not available yet
            if self.coins_config is None:
                self.coins_config = memcache.get_coins_config()
                msg = "skipping cache_calc.tickers, coins_config is None"
                return default.result(msg=msg, loglevel="warning", data=None)

            suffix = transform.get_suffix(trades_days)
            ts = cron.now_utc() - pairs_days * 86400
            # Filter out pairs older than requested time
            pairs = sorted(
                [
                    i
                    for i in self.last_traded_cache
                    if self.last_traded_cache[i]["last_swap_time"] > ts
                ]
            )
            if from_memcache == 1:
                # Disabled for now
                # TODO: test if performance boost with this or not
                data = []
                key = "ticker_info"
                for i in pairs:
                    cache_name = derive.pair_cachename(
                        key, self.as_str, suffix, all_variants
                    )
                    cache_data = memcache.get(cache_name)
                    if cache_data is not None:
                        data.append(cache_data)
            else:
                data = [
                    Pair(
                        pair_str=i,
                        last_traded_cache=self.last_traded_cache,
                        coins_config=self.coins_config,
                    ).ticker_info(trades_days, all_variants=False)
                    for i in pairs
                ]

                data = [i for i in data if i is not None]
                data = clean.decimal_dict_lists(data, to_string=True, rounding=10)
                data = sortdata.dict_lists(data, "ticker_id")
                data = {
                    "last_update": int(cron.now_utc()),
                    "pairs_count": len(data),
                    "swaps_count": int(sumdata.json_key(data, f"trades_{suffix}")),
                    "combined_volume_usd": sumdata.json_key_10f(
                        data, "combined_volume_usd"
                    ),
                    "combined_liquidity_usd": sumdata.json_key_10f(
                        data, "liquidity_in_usd"
                    ),
                    "data": data,
                }
                msg = f"Traded_tickers complete! {len(pairs)} pairs traded"
                msg += f" in last {pairs_days} days"
            return default.result(data, msg, loglevel="calc")
        except Exception as e:  # pragma: no cover
            msg = "tickers failed!"
            return default.error(e, msg)
