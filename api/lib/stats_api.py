#!/usr/bin/env python3
from db.sqlitedb import get_sqlite_db, get_sqlite_db_paths
from util.logger import logger
from lib.pair import Pair
import time
import lib
from util.defaults import set_params
import util.transform as transform


class StatsAPI:
    def __init__(self, **kwargs):
        try:
            # Set params
            self.kwargs = kwargs
            self.options = ["testing"]
            self.netid = "ALL"
            set_params(self, self.kwargs, self.options)
            if "gecko_source" in kwargs:
                self.gecko_source = kwargs["gecko_source"]
            else:
                logger.loop("Getting gecko source for Generic")
                self.gecko_source = lib.load_gecko_source(testing=self.testing)

            if "coins_config" in kwargs:
                self.coins_config = kwargs["coins_config"]
            else:
                logger.loop("Getting coins_config for Generic")
                self.coins_config = lib.load_coins_config(testing=self.testing)

            if "last_traded_cache" in kwargs:
                self.last_traded_cache = kwargs["last_traded_cache"]
            else:
                self.last_traded_cache = lib.load_generic_last_traded(
                    testing=self.testing
                )
            self.db_path = get_sqlite_db_paths(netid="ALL")
            self.db = get_sqlite_db(
                testing=self.testing,
                netid=self.netid,
                coins_config=self.coins_config,
                gecko_source=self.gecko_source,
                last_traded_cache=self.last_traded_cache,
            )
        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to init Generic: {e}")

    def top_pairs(self, summaries: list):
        try:
            top_pairs_by_value = {
                i["trading_pair"]: i["pair_trade_value_usd"]
                for i in transform.get_top_items(summaries, "pair_trade_value_usd", 5)
            }
            top_pairs_by_liquidity = {
                i["trading_pair"]: i["pair_liquidity_usd"]
                for i in transform.get_top_items(summaries, "pair_liquidity_usd", 5)
            }
            top_pairs_by_swaps = {
                i["trading_pair"]: i["pair_swaps_count"]
                for i in transform.get_top_items(summaries, "pair_swaps_count", 5)
            }
            return {
                "by_value_traded_usd": transform.clean_decimal_dict(top_pairs_by_value),
                "by_current_liquidity_usd": transform.clean_decimal_dict(
                    top_pairs_by_liquidity
                ),
                "by_swaps_count": transform.clean_decimal_dict(top_pairs_by_swaps),
            }
        except Exception as e:
            logger.error(f"{type(e)} Error in [get_top_pairs]: {e}")
            return {"by_volume": [], "by_liquidity": [], "by_swaps": []}

    def pair_summaries(self, days: int = 1, pairs_days: int = 7):
        try:
            if days > pairs_days:
                pairs_days = days
            pairs = self.db.query.get_pairs(days=pairs_days)
            suffix = transform.get_suffix(days)
            ticker_infos = [
                Pair(
                    pair_str=i,
                    netid=self.netid,
                    db=self.db,
                    gecko_source=self.gecko_source,
                    coins_config=self.coins_config,
                    last_traded_cache=self.last_traded_cache,
                ).ticker_info(days)
                for i in pairs
            ]
            data = [
                transform.ticker_to_statsapi(i, suffix=suffix) for i in ticker_infos
            ]
            return transform.clean_decimal_dict_list(data)

        except Exception as e:
            logger.error(f"{type(e)} Error in [StatsAPI.pair_summaries]: {e}")
            return None

    def adex_fortnite(self, days=14):
        try:
            end = int(time.time())
            start = end - 14 * 86400
            swaps = self.db.query.get_timespan_swaps(start=start, end=end)
            summaries = self.pair_summaries(days)
            liquidity = transform.sum_json_key(data=summaries, key="pair_liquidity_usd")
            swaps_value = transform.sum_json_key(
                data=summaries, key="pair_trade_value_usd"
            )
            logger.debug(f"{len(swaps)} swaps ({days} days)")
            data = {
                "days": days,
                "swaps_count": len(swaps),
                "swaps_value": round(float(swaps_value), 8),
                "top_pairs": self.top_pairs(summaries),
                "current_liquidity": round(float(liquidity), 8),
            }
            data = transform.clean_decimal_dict(data)
            return data
        except Exception as e:
            logger.error(f"{type(e)} Error in [StatsAPI.adex_fortnite]: {e}")
            return None
