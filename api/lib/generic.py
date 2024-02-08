#!/usr/bin/env python3
from db.sqldb import SqlQuery
import lib.pair as pair
from lib.coins import get_kmd_pairs
from util.exceptions import DataStructureError
from util.logger import timed, logger
from util.transform import sortdata, clean, derive
import util.defaults as default
import util.helper as helper
import util.memcache as memcache
from util.transform import template


class Generic:  # pragma: no cover
    def __init__(self) -> None:
        try:
            self.pg_query = SqlQuery()
            self.pairs_last_trade_cache = memcache.get_pairs_last_traded()
            self.coins_config = memcache.get_coins_config()
            self.gecko_source = memcache.get_gecko_source()

        except Exception as e:  # pragma: no cover
            logger.error(f"Failed to init Generic: {e}")

    @timed
    def pairs(self, days: int = 90) -> dict:
        """Returns basic pair info and tags as priced/unpriced"""
        try:
            pairs = self.pg_query.get_pairs(days=days)
            if "error" in pairs:  # pragma: no cover
                raise DataStructureError(
                    f"'get_pairs' returned an error: {pairs['error']}"
                )
            else:
                resp = get_pairs_status(pairs)
                resp = clean.decimal_dict_lists(resp)
                self.pairs_last_trade_cache = memcache.get_pairs_last_traded()
                for i in resp:
                    first_last_swap = template.first_last_swap()
                    if self.pairs_last_trade_cache is not None:
                        if i["ticker_id"] in self.pairs_last_trade_cache:
                            x = self.pairs_last_trade_cache[i["ticker_id"]]
                            first_last_swap = clean.decimal_dicts(x)
                    i.update(first_last_swap)
                msg = f"{len(pairs)} pairs traded in the last {days} days"
                return default.result(data=resp, msg=msg, loglevel="loop")
        except Exception as e:  # pragma: no cover
            msg = f"Generic.pairs failed! {e}"
            return default.result(
                data=resp, msg=msg, loglevel="warning", ignore_until=2
            )

    @timed
    def orderbook(
        self,
        pair_str: str = "KMD_LTC",
        depth: int = 100,
        all_variants: bool = False,
        no_thread: bool = True,
    ):
        return pair.orderbook(
            pair_str=pair_str,
            depth=depth,
            all_variants=all_variants,
            no_thread=no_thread,
        )


@timed
def get_pairs_status(pairs, gecko_source=None):
    try:
        if gecko_source is None:  # pragma: no cover
            gecko_source = memcache.get_gecko_source()
        pairs = list(set(pairs + get_kmd_pairs()))
        pairs_dict = derive.price_status_dict(pairs, gecko_source)
        priced_pairs = helper.get_pairs_info(pairs_dict["priced_gecko"], True)
        unpriced_pairs = helper.get_pairs_info(pairs_dict["unpriced"], False)
        return sortdata.dict_lists(priced_pairs + unpriced_pairs, "ticker_id")
    except Exception as e:  # pragma: no cover
        logger.warning(e)
