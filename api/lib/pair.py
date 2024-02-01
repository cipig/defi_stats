#!/usr/bin/env python3
import util.cron as cron
from collections import OrderedDict
from decimal import Decimal
from typing import Optional, List, Dict
import db
from lib.coins import get_gecko_price, get_gecko_mcap
from lib.generic import Generic
from util.logger import logger, timed
from util.transform import sortdata, clean, deplatform, sumdata, merge
import util.defaults as default
import util.helper as helper
import util.memcache as memcache
import util.templates as template
import util.transform as transform


generic = Generic()


class Pair:  # pragma: no cover
    """
    Allows for referencing pairs as a string or tuple.
    e.g. DOGE_BTC, not BTC_DOGE
    """

    def __init__(
        self,
        pair_str: str,
        last_traded_cache: Dict | None = None,
        coins_config: Dict | None = None,
        **kwargs,
    ):
        try:
            # Set params
            self.kwargs = kwargs
            self.options = []
            default.params(self, self.kwargs, self.options)
            self.pg_query = db.SqlQuery()
            # Adjust pair order
            self.as_str = pair_str
            self.as_std_str = deplatform.pair(self.as_str)
            self.is_reversed = self.as_str != sortdata.pair_by_market_cap(self.as_str)
            base, quote = helper.base_quote_from_pair(self.as_str)
            self.base = base
            self.quote = quote
            self.as_tuple = tuple((self.base, self.quote))
            self.as_set = set((self.base, self.quote))

            # Get price and market cap
            self.base_usd_price = get_gecko_price(self.base)
            self.quote_usd_price = get_gecko_price(self.quote)
            self.base_mcap = get_gecko_mcap(self.base)
            self.quote_mcap = get_gecko_mcap(self.quote)
            self.last_traded_cache = last_traded_cache

            if self.quote_usd_price == 0 or self.base_usd_price == 0:
                self.priced = False
            else:
                self.priced = True

            if self.last_traded_cache is None:
                self.last_traded_cache = memcache.get_last_traded()
            self.coins_config = coins_config

            if self.coins_config is None:
                self.coins_config = memcache.get_coins_config()

        except Exception as e:  # pragma: no cover
            msg = f"Init Pair for {pair_str} failed!"
            logger.error(f"{type(e)} {msg}: {e}")

    @timed
    def historical_trades(
        self,
        limit: int = 100,
        start_time: Optional[int] = 0,
        end_time: Optional[int] = 0,
    ):
        """Returns trades for this pair."""
        # TODO: Review price / reverse price logic
        try:
            if start_time == 0:
                start_time = int(cron.now_utc()) - 86400
            if end_time == 0:
                end_time = int(cron.now_utc())

            resp = {}
            swaps_for_pair = self.pg_query.get_swaps(
                start_time=start_time,
                end_time=end_time,
                pair=self.as_str,
            )
            for variant in swaps_for_pair:
                trades_info = []
                for swap in swaps_for_pair[variant]:
                    trade_info = OrderedDict()
                    trade_info["trade_id"] = swap["uuid"]
                    trade_info["timestamp"] = swap["finished_at"]
                    # Handle reversed pair
                    if self.is_reversed:
                        price = Decimal(swap["reverse_price"])
                        trade_info["pair"] = transform.invert_pair(swap["pair"])
                        trade_info["type"] = transform.invert_trade_type(
                            swap["trade_type"]
                        )
                    else:
                        price = Decimal(swap["price"])
                        trade_info["pair"] = swap["pair"]
                        trade_info["type"] = swap["trade_type"]

                    if trade_info["type"] == "buy":
                        trade_info["base_volume"] = transform.format_10f(
                            swap["maker_amount"]
                        )
                        trade_info["quote_volume"] = transform.format_10f(
                            swap["taker_amount"]
                        )
                        trade_info["quote_volume"] = transform.format_10f(
                            swap["taker_amount"]
                        )
                    else:
                        trade_info["base_volume"] = transform.format_10f(
                            swap["taker_amount"]
                        )
                        trade_info["quote_volume"] = transform.format_10f(
                            swap["maker_amount"]
                        )
                        trade_info["quote_volume"] = transform.format_10f(
                            swap["maker_amount"]
                        )

                    trade_info["price"] = transform.format_10f(price)
                    trades_info.append(trade_info)

                average_price = self.get_average_price(trades_info)
                buys = transform.list_json_key(trades_info, "type", "buy")
                sells = transform.list_json_key(trades_info, "type", "sell")
                if len(buys) > 0:
                    buys = sortdata.dict_lists(buys, "timestamp", reverse=True)
                if len(sells) > 0:
                    sells = sortdata.dict_lists(sells, "timestamp", reverse=True)
                data = {
                    "ticker_id": self.as_str,
                    "start_time": str(start_time),
                    "end_time": str(end_time),
                    "limit": str(limit),
                    "trades_count": str(len(trades_info)),
                    "sum_base_volume_buys": sumdata.json_key_10f(buys, "base_volume"),
                    "sum_base_volume_sells": sumdata.json_key_10f(sells, "base_volume"),
                    "sum_quote_volume_buys": sumdata.json_key_10f(buys, "quote_volume"),
                    "sum_quote_volume_sells": sumdata.json_key_10f(
                        sells, "quote_volume"
                    ),
                    "average_price": transform.format_10f(average_price),
                    "buy": buys,
                    "sell": sells,
                }
                resp.update({variant: data})
        except Exception as e:  # pragma: no cover
            return default.result(
                data=resp,
                msg=f"pair.historical_trades {self.as_str} failed! {e}",
                loglevel="warning",
            )
        return default.result(
            data=resp,
            msg=f"historical_trades for {self.as_str} complete",
            loglevel="pair",
            ignore_until=2,
        )

    @timed
    def get_average_price(self, trades_info):
        try:
            data = 0
            if len(trades_info) > 0:
                data = sumdata.json_key(trades_info, "price") / len(trades_info)
            return default.result(
                data=data,
                msg=f"get_average_price for {self.as_str} complete",
                loglevel="pair",
                ignore_until=2,
            )
        except Exception as e:  # pragma: no cover
            msg = f"{self.as_str} get_average_price failed! {e}"
            return default.error(e, msg)

    @timed
    def get_volumes_and_prices(self, days: int = 1, all: bool = True):
        """
        Iterates over list of swaps to get volumes and prices data
        """
        try:
            suffix = transform.get_suffix(days)
            data = template.volumes_and_prices(suffix, base=self.base, quote=self.quote)
            swaps_for_pair_combo = self.pg_query.get_swaps(
                start_time=int(cron.now_utc() - 86400 * days),
                end_time=int(cron.now_utc()),
                pair=self.as_str,
            )
            # Extract all variant swaps, or for a single variant
            if all:
                cache_name = f"volumes_and_prices_{self.as_str}_ALL"
                variants = helper.get_pair_variants(self.as_str)
            elif self.as_str in swaps_for_pair_combo:
                cache_name = f"volumes_and_prices_{self.as_str}"
                variants = helper.get_pair_variants(self.as_str, segwit_only=True)
            elif transform.invert_pair(self.as_str) in swaps_for_pair_combo:
                cache_name = f"volumes_and_prices_{transform.invert_pair(self.as_str)}"
                variants = helper.get_pair_variants(
                    transform.invert_pair(self.as_str), segwit_only=True
                )
            else:
                logger.warning(
                    f"{self.str} not in swaps_for_pair_combo, returning template"
                )
                return data
            data.update(
                {
                    "base_price": self.base_usd_price,
                    "quote_price": self.quote_usd_price,
                    "variants": variants,
                }
            )
            if all:
                swaps_for_pair = swaps_for_pair_combo["ALL"]
                data = merge.volumes_data(
                    data,
                    suffix,
                    swaps_for_pair,
                    self.base_usd_price,
                    self.quote_usd_price,
                    self.is_reversed,
                )
                swap_prices = self.get_swap_prices(swaps_for_pair, self.is_reversed)
            else:
                swap_prices = {}
                for variant in variants:
                    if variant in swaps_for_pair_combo:
                        swaps_for_pair = swaps_for_pair_combo[variant]
                    else:
                        logger.warning(f"Variant {variant} not in swaps for pair!")
                        continue
                    data = merge.volumes_data(
                        data,
                        suffix,
                        swaps_for_pair,
                        self.base_usd_price,
                        self.quote_usd_price,
                        self.is_reversed,
                    )
                    swap_prices.update(
                        self.get_swap_prices(swaps_for_pair, self.is_reversed)
                    )

            # Get Prices
            # TODO: using timestamps as an index works for now,
            # but breaks when two swaps have the same timestamp.
            if len(swap_prices) > 0:
                swap_vals = list(swap_prices.values())
                swap_keys = list(swap_prices.keys())
                highest_price = max(swap_vals)
                lowest_price = min(swap_vals)
                newest_price = swap_prices[max(swap_prices.keys())]
                oldest_price = swap_prices[min(swap_prices.keys())]
                data["oldest_price_time"] = swap_keys[swap_vals.index(oldest_price)]
                data["newest_price_time"] = swap_keys[swap_vals.index(newest_price)]
                data["oldest_price"] = oldest_price
                data["newest_price"] = newest_price
                price_change = newest_price - oldest_price
                pct_change = newest_price / oldest_price - 1
                data[f"highest_price_{suffix}"] = highest_price
                data[f"lowest_price_{suffix}"] = lowest_price
                data[f"price_change_pct_{suffix}"] = pct_change
                data[f"price_change_{suffix}"] = price_change
                last_swap = self.first_last_swap(data["variants"])
                data["last_swap_price"] = last_swap["last_swap_price"]
                data["last_swap_time"] = last_swap["last_swap_time"]
                data["last_swap_uuid"] = last_swap["last_swap_uuid"]

            ignore_until = 3
            if Decimal(data["combined_volume_usd"]) > 0:
                data = clean.decimal_dicts(data)
                memcache.update(cache_name, data, 900)
                ignore_until = 0

            msg = f"{self.as_str}: ${data['combined_volume_usd']} volume | Added to {cache_name}"
            # msg += f"| Variants: {data['variants']} !"
            return default.result(
                data=data, msg=msg, loglevel="query", ignore_until=ignore_until
            )
        except Exception as e:  # pragma: no cover
            msg = f"get_volumes_and_prices for {self.as_str} failed! {e}, returning template"
            return default.result(
                data=data, msg=msg, loglevel="warning", ignore_until=0
            )

    @timed
    def first_last_swap(self, variants: List):
        try:
            data = template.first_last_swap()
            for variant in variants:
                x = template.first_last_swap()

                if variant in self.last_traded_cache:
                    x = self.last_traded_cache[variant]
                elif (
                    transform.invert_pair(variant) in self.last_traded_cache
                ):  # pragma: no cover
                    x = self.last_traded_cache[transform.invert_pair(variant)]

                if x["last_swap_time"] > data["last_swap_time"]:
                    data["last_swap_time"] = x["last_swap_time"]
                    data["last_swap_price"] = x["last_swap_price"]
                    data["last_swap_uuid"] = x["last_swap_uuid"]
                    if self.is_reversed and data["last_swap_price"] != 0:
                        data["last_swap_price"] = 1 / data["last_swap_price"]

            msg = f"Got first and last swap for {self.as_str}"
            return default.result(data=data, msg=msg, loglevel="pair", ignore_until=2)
        except Exception as e:  # pragma: no cover
            data = template.first_last_swap()
            msg = f"Returning template for {self.as_str} ({e})"
            return default.result(
                data=data, msg=msg, loglevel="warning", ignore_until=0
            )

    @timed
    def ticker_info(self, days=1, all: bool = False):
        # TODO: ps: in order for CoinGecko to show +2/-2% depth,
        # DEX has to provide the formula for +2/-2% depth.
        try:
            suffix = transform.get_suffix(days)
            if all:
                cache_name = f"ticker_info_{self.as_str}_{suffix}_ALL"
            else:
                cache_name = f"ticker_info_{self.as_str}_{suffix}"

            data = memcache.get(cache_name)
            if data is not None and Decimal(data["liquidity_in_usd"]) > 0:
                msg = f"Using cache: {cache_name}"
                return default.result(
                    data=data, msg=msg, loglevel="query", ignore_until=0
                )

            data = template.ticker_info(suffix, self.base, self.quote)
            data.update(
                {
                    "ticker_id": self.as_str,
                    "base_currency": self.base,
                    "quote_currency": self.quote,
                    "base_usd_price": self.base_usd_price,
                    "quote_usd_price": self.quote_usd_price,
                    "priced": self.priced,
                }
            )
            data.update(self.get_volumes_and_prices(days, all=all))
            orderbook_data = generic.orderbook(
                self.as_str, depth=100, all=all, no_thread=False
            )
            for i in orderbook_data.keys():
                if i in ["bids", "asks"]:
                    data.update({f"num_{i}": len(orderbook_data[i])})
                else:
                    data.update({i: orderbook_data[i]})
            ignore_until = 3

            # Add to cache if fully populated
            if (
                Decimal(data["liquidity_in_usd"]) > 0
                and Decimal(data["combined_volume_usd"]) > 0
            ):
                segwit_variants = helper.get_pair_variants(
                    self.as_str, segwit_only=True
                )
                for sv in segwit_variants:
                    if all:
                        cache_name = f"ticker_info_{sv}_{suffix}_ALL"
                    else:
                        cache_name = f"ticker_info_{sv}_{suffix}"
                    base, quote = helper.base_quote_from_pair(sv)
                    data.update(
                        {
                            "ticker_id": sv,
                            "pair": sv,
                            "base": base,
                            "quote": quote,
                            "ticker_info_cache_name": cache_name,
                        }
                    )
                    data = clean.decimal_dicts(data)
                    memcache.update(cache_name, data, 900)
                    msg = f" {cache_name} added to memcache"
                    loglevel = "cached"
                    ignore_until = 3
            else:
                msg = f" {cache_name} not added to memcache,"
                msg += " liquidity and volume for pair is zero"
                loglevel = "warning"
                ignore_until = 3
            return default.result(
                data=data, msg=msg, loglevel=loglevel, ignore_until=ignore_until
            )
        except Exception as e:  # pragma: no cover
            msg = f"ticker_info for {self.as_str} ({days} days) failed! {e}"
            return default.result(
                data=data, msg=msg, loglevel="warning", ignore_until=0
            )

    @timed
    def get_swap_prices(self, swaps_for_pair, is_reversed):
        try:
            data = {}
            [
                data.update(helper.get_price_at_finish(i, is_reversed))
                for i in swaps_for_pair
            ]
        except Exception as e:  # pragma: no cover
            msg = f"get_swap_prices for {self.as_str} failed! {e}"
            return default.result(data=data, msg=msg, loglevel="warning")
        msg = f"Completed get_swap_prices info for {self.as_str}"
        return default.result(data=data, msg=msg, loglevel="pair", ignore_until=2)

    @timed
    def swap_uuids(
        self,
        start_time: Optional[int] = 0,
        end_time: Optional[int] = 0,
        all=True,
    ) -> list:
        try:
            data = self.pg_query.swap_uuids(
                start_time=start_time, end_time=end_time, pair=self.as_str
            )
            if all:
                variants = sorted([i for i in data.keys() if i != "ALL"])
                data = {"uuids": data["ALL"], "variants": variants}
            elif self.as_str in data:
                data = {"uuids": data[self.as_str], "variants": [self.as_str]}
            elif transform.invert_pair(self.as_str) in data:
                data = {
                    "uuids": data[transform.invert_pair(self.as_str)],
                    "variants": [transform.invert_pair(self.as_str)],
                }

        except Exception as e:  # pragma: no cover
            data = {"uuids": [], "variants": [self.as_str]}
            msg = f"{self.as_str} swap_uuids failed! {e}"
            return default.result(data=data, msg=msg, loglevel="warning")
        msg = f"Completed swap_uuids for {self.as_str}"
        return default.result(data=data, msg=msg, loglevel="pair", ignore_until=2)


@timed
def get_all_coin_pairs(coin, priced_coins):
    try:
        pairs = [
            (f"{i}_{coin}") for i in priced_coins if coin not in [i, f"{i}-segwit"]
        ]
        data = list(set([sortdata.pair_by_market_cap(i) for i in pairs]))

    except Exception as e:  # pragma: no cover
        data = []
        msg = f"{coin} get_all_coin_pairs failed! {e}"
        return default.result(data=data, msg=msg, loglevel="warning")
    msg = f"Completed get_all_coin_pairs for {coin}"
    return default.result(data=data, msg=msg, loglevel="pair", ignore_until=2)
