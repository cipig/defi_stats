from decimal import Decimal, InvalidOperation
from typing import Any, List, Dict

from util.logger import logger, timed
import util.defaults as default
import util.helper as helper
import util.memcache as memcache
import util.templates as template


# TODO: Create Subclasses for transform / strip / aggregate / cast


class Clean:
    def __init__(self):
        pass

    @timed
    def decimal_dict_lists(self, data, to_string=False, rounding=8):
        """
        Works for a list of dicts with no nesting
        (e.g. summary_cache.json)
        """
        try:
            for i in data:
                for j in i:
                    if isinstance(i[j], Decimal):
                        if to_string:
                            i[j] = round_to_str(i[j], rounding)
                        else:
                            i[j] = round(float(i[j]), rounding)
            return data
        except Exception as e:  # pragma: no cover
            return default.error(e)

    @timed
    def decimal_dicts(
        self, data, to_string=False, rounding=8, exclude_keys: List = list()
    ):
        """
        Works for a simple dict with no nesting
        (e.g. summary_cache.json)
        """
        try:
            for i in data:
                if i not in exclude_keys:
                    if isinstance(data[i], Decimal):
                        if to_string:
                            data[i] = round_to_str(data[i], rounding)
                        else:
                            data[i] = float(data[i])
            return data
        except Exception as e:  # pragma: no cover
            return default.error(e)

    @timed
    def orderbook_data(self, data):
        """
        Works for a simple dict with no nesting
        (e.g. summary_cache.json)
        """
        try:
            for i in ["bids", "asks"]:
                for j in data[i]:
                    for k in ["price", "volume"]:
                        j[k] = format_10f(Decimal(j[k]))
            for i in [
                "total_asks_base_vol",
                "total_bids_base_vol",
                "total_asks_quote_vol",
                "total_bids_quote_vol",
                "total_asks_base_usd",
                "total_bids_quote_usd",
                "liquidity_in_usd",
            ]:
                data[i] = format_10f(Decimal(data[i]))
            return data
        except Exception as e:  # pragma: no cover
            return default.error(e)


class Convert:
    def __init__(self):
        pass

    def ticker_to_gecko_pair(self, pair_data):
        return {
            "ticker_id": pair_data["ticker_id"],
            "pool_id": pair_data["ticker_id"],
            "base": pair_data["base_currency"],
            "target": pair_data["quote_currency"],
            "variants": pair_data["variants"],
        }

    def ticker_to_gecko_ticker(self, ticker_data):
        return {
            "ticker_id": ticker_data["ticker_id"],
            "pool_id": ticker_data["ticker_id"],
            "base_currency": ticker_data["base_currency"],
            "target_currency": ticker_data["quote_currency"],
            "base_volume": ticker_data["base_volume"],
            "target_volume": ticker_data["quote_volume"],
            "bid": ticker_data["highest_bid"],
            "ask": ticker_data["lowest_ask"],
            "high": ticker_data["highest_price_24hr"],
            "low": ticker_data["lowest_price_24hr"],
            "trades_24hr": ticker_data["trades_24hr"],
            "last_price": ticker_data["last_swap_price"],
            "last_trade": ticker_data["last_swap_time"],
            "last_swap_uuid": ticker_data["last_swap_uuid"],
            "volume_usd_24hr": ticker_data["combined_volume_usd"],
            "liquidity_in_usd": ticker_data["liquidity_in_usd"],
            "variants": ticker_data["variants"],
        }

    def historical_trades_to_gecko(self, i):
        return {
            "trade_id": i["trade_id"],
            "price": i["price"],
            "base_volume": i["base_volume"],
            "target_volume": i["quote_volume"],
            "timestamp": i["timestamp"],
            "type": i["type"],
        }

    def last_traded_to_market(self, last_traded_item):
        return {
            "pair": last_traded_item["pair"],
            "swap_count": last_traded_item["pair"],
            "last_swap": last_traded_item["last_swap_time"],
            "last_swap_uuid": last_traded_item["last_swap_uuid"],
            "last_price": last_traded_item["last_swap_price"],
            "base_volume_usd_24hr": last_traded_item["base_volume_usd_24hr"],
            "quote_volume_24hr": last_traded_item["quote_volume_24hr"],
            "base_volume_24hr": last_traded_item["base_volume_24hr"],
            "trade_volume_usd_24hr": last_traded_item["trade_volume_usd_24hr"],
            "quote_volume_usd_24hr": last_traded_item["quote_volume_usd_24hr"],
            "priced": last_traded_item["priced"],
        }

    def traded_cache_to_stats_api(self, traded_cache):
        resp = {}
        for i in traded_cache:
            cleaned_ticker = deplatform.pair(i)
            if cleaned_ticker not in resp:
                resp.update({cleaned_ticker: traded_cache[i]})
            else:
                if (
                    resp[cleaned_ticker]["last_swap_time"]
                    < traded_cache[i]["last_swap_time"]
                ):
                    resp.update({cleaned_ticker: traded_cache[i]})
        return resp

    def ticker_to_summary_for_ticker(self, data):  # pragma: no cover
        return {
            "pair": data["ticker_id"],
            "base": data["base_currency"],
            "liquidity_usd": data["liquidity_in_usd"],
            "base_volume": data["base_volume"],
            "base_usd_price": data["base_usd_price"],
            "quote": data["quote_currency"],
            "quote_volume": data["quote_volume"],
            "quote_usd_price": data["quote_usd_price"],
            "highest_bid": data["highest_bid"],
            "lowest_ask": data["lowest_ask"],
            "highest_price_24hr": data["highest_price_24hr"],
            "lowest_price_24hr": data["lowest_price_24hr"],
            "price_change_24hr": data["price_change_24hr"],
            "price_change_percent_24hr": data["price_change_pct_24hr"],
            "trades_24hr": data["trades_24hr"],
            "volume_usd_24hr": data["combined_volume_usd"],
            "last_price": data["last_swap_price"],
            "last_trade": data["last_swap_time"],
            "last_swap_uuid": data["last_swap_uuid"],
        }

    def ticker_to_market_summary_item(self, i):
        data = {
            "trading_pair": f"{i['ticker_id']}",
            "variants": i["variants"],
            "base_currency": i["base_currency"],
            "base_volume": i["base_volume"],
            "quote_currency": i["quote_currency"],
            "quote_volume": i["quote_volume"],
            "lowest_ask": i["lowest_ask"],
            "highest_bid": i["highest_bid"],
            "price_change_pct_24hr": i["price_change_pct_24hr"],
            "highest_price_24hr": i["highest_price_24hr"],
            "lowest_price_24hr": i["lowest_price_24hr"],
            "trades_24hr": int(i["trades_24hr"]),
            "last_swap": int(i["last_swap_time"]),
            "last_swap_uuid": i["last_swap_uuid"],
            "last_price": i["last_swap_price"],
        }
        return data


@timed
def orderbook_to_gecko(data):
    bids = [[i["price"], i["volume"]] for i in data["bids"]]
    asks = [[i["price"], i["volume"]] for i in data["asks"]]
    data["asks"] = asks
    data["bids"] = bids
    data["ticker_id"] = data["pair"]
    return data


@timed
def to_summary_for_ticker_xyz_item(data):  # pragma: no cover
    return {
        "ticker_id": data["ticker_id"],
        "base_currency": data["base_currency"],
        "liquidity_usd": data["liquidity_in_usd"],
        "base_volume": data["base_volume"],
        "base_usd_price": data["base_usd_price"],
        "quote_currency": data["quote_currency"],
        "quote_volume": data["quote_volume"],
        "quote_usd_price": data["quote_usd_price"],
        "highest_bid": data["highest_bid"],
        "lowest_ask": data["lowest_ask"],
        "highest_price_24h": data["highest_price_24hr"],
        "lowest_price_24h": data["lowest_price_24hr"],
        "price_change_24h": data["price_change_24hr"],
        "price_change_pct_24h": data["price_change_pct_24hr"],
        "trades_24hr": data["trades_24hr"],
        "volume_usd_24h": data["combined_volume_usd"],
        "last_swap_price": data["last_swap_price"],
        "last_swap_timestamp": data["last_swap_time"],
    }


@timed
def ticker_to_xyz_summary(i):
    return {
        "ticker_id": f"{i['base_currency']}_{i['quote_currency']}",
        "base_currency": i["base_currency"],
        "base_volume": i["base_volume"],
        "quote_currency": i["quote_currency"],
        "quote_volume": i["quote_volume"],
        "lowest_ask": i["lowest_ask"],
        "last_swap_timestamp": int(i["last_swap_time"]),
        "highest_bid": i["highest_bid"],
        "price_change_pct_24h": str(i["price_change_pct_24hr"]),
        "highest_price_24hr": i["highest_price_24hr"],
        "lowest_price_24hr": i["lowest_price_24hr"],
        "trades_24hr": int(i["trades_24hr"]),
        "last_swap": int(i["last_swap_time"]),
        "last_swap_price": i["last_swap_price"],
    }


@timed
def ticker_to_market_ticker(i):
    return {
        f"{i['base_currency']}_{i['quote_currency']}": {
            "last_swap_price": i["last_swap_price"],
            "quote_volume": i["quote_volume"],
            "base_volume": i["base_volume"],
            "isFrozen": "0",
        }
    }


@timed
def ticker_to_gecko_summary(i):
    data = {
        "ticker_id": i["ticker_id"],
        "pool_id": i["ticker_id"],
        "variants": i["variants"],
        "base_currency": i["base_currency"],
        "quote_currency": i["quote_currency"],
        "highest_bid": format_10f(i["highest_bid"]),
        "lowest_ask": format_10f(i["lowest_ask"]),
        "highest_price_24hr": format_10f(i["highest_price_24hr"]),
        "lowest_price_24hr": format_10f(i["lowest_price_24hr"]),
        "base_volume": format_10f(i["base_volume"]),
        "quote_volume": format_10f(i["quote_volume"]),
        "last_swap_price": format_10f(i["last_swap_price"]),
        "last_swap_time": int(Decimal(i["last_swap_time"])),
        "last_swap_uuid": i["last_swap_uuid"],
        "trades_24hr": int(Decimal(i["trades_24hr"])),
        "combined_volume_usd": format_10f(i["combined_volume_usd"]),
        "liquidity_in_usd": format_10f(i["liquidity_in_usd"]),
    }
    return data


@timed
def ticker_to_statsapi_summary(i):
    if i is None:
        return i
    try:
        suffix = [k for k in i.keys() if k.startswith("trades_")][0].replace(
            "trades_", ""
        )
        if suffix == "24hr":
            alt_suffix = "24h"
        else:
            alt_suffix = suffix
        data = {
            "ticker_id": i["ticker_id"],
            "pair_swaps_count": int(Decimal(i[f"trades_{suffix}"])),
            "pair_liquidity_usd": Decimal(i["liquidity_in_usd"]),
            "pair_trade_value_usd": Decimal(i["combined_volume_usd"]),
            "base_currency": i["base_currency"],
            "base_volume": Decimal(i["base_volume"]),
            "base_price_usd": Decimal(i["base_usd_price"]),
            "base_trade_value_usd": Decimal(i["base_volume_usd"]),
            "base_liquidity_coins": Decimal(i["base_liquidity_coins"]),
            "base_liquidity_usd": Decimal(i["base_liquidity_usd"]),
            "quote_currency": i["quote_currency"],
            "quote_volume": Decimal(i["quote_volume"]),
            "quote_price_usd": Decimal(i["quote_usd_price"]),
            "quote_trade_value_usd": Decimal(i["quote_volume_usd"]),
            "quote_liquidity_coins": Decimal(i["quote_liquidity_coins"]),
            "quote_liquidity_usd": Decimal(i["quote_liquidity_usd"]),
            "newest_price": i["newest_price"],
            "oldest_price": i["oldest_price"],
            "newest_price_time": i["newest_price_time"],
            "oldest_price_time": i["oldest_price_time"],
            "highest_bid": Decimal(i["highest_bid"]),
            "lowest_ask": Decimal(i["lowest_ask"]),
            f"volume_usd_{alt_suffix}": Decimal(i["combined_volume_usd"]),
            f"highest_price_{alt_suffix}": Decimal(i[f"highest_price_{suffix}"]),
            f"lowest_price_{alt_suffix}": Decimal(i[f"lowest_price_{suffix}"]),
            f"price_change_{alt_suffix}": Decimal(i[f"price_change_{suffix}"]),
            f"price_change_pct_{alt_suffix}": Decimal(i[f"price_change_pct_{suffix}"]),
            "last_swap_price": i["last_swap_price"],
            "last_swap_time": int(Decimal(i["last_swap_time"])),
            "last_swap_uuid": i["last_swap_uuid"],
            "variants": i["variants"],
        }
        return data

    except Exception as e:  # pragma: no cover
        return default.error(e)


@timed
def historical_trades_to_market_trades(i):
    return {
        "trade_id": i["trade_id"],
        "price": i["price"],
        "base_volume": i["base_volume"],
        "quote_volume": i["quote_volume"],
        "timestamp": i["timestamp"],
        "type": i["type"],
    }


class Deplatform:
    def __init__(self):
        pass

    def tickers(self, tickers_data, priced_only=False):
        data = {}
        # Combine to pair without platforms
        for i in tickers_data["data"]:
            if priced_only and not i["priced"]:
                continue
            root_pair = self.pair(i["ticker_id"])
            i["ticker_id"] = root_pair
            i["base_currency"] = self.coin(i["base_currency"])
            i["quote_currency"] = self.coin(i["quote_currency"])
            if root_pair not in data:
                i["trades_24hr"] = int(i["trades_24hr"])
                data.update({root_pair: i})
            else:
                j = data[root_pair]
                j["variants"] += i["variants"]
                j["trades_24hr"] += int(i["trades_24hr"])
                for key in [
                    "combined_volume_usd",
                    "liquidity_in_usd",
                    "base_volume",
                    "base_volume_usd",
                    "base_liquidity_coins",
                    "base_liquidity_usd",
                    "quote_volume",
                    "quote_volume_usd",
                    "quote_liquidity_coins",
                    "quote_liquidity_usd",
                ]:
                    # Add to cumulative sum
                    j[key] = sumdata.numeric_str(i[key], j[key])
                if Decimal(i["last_swap_time"]) > Decimal(j["last_swap_time"]):
                    j["last_swap_price"] = i["last_swap_price"]
                    j["last_swap_time"] = i["last_swap_time"]
                    j["last_swap_uuid"] = i["last_swap_uuid"]

                if int(Decimal(j["newest_price_time"])) < int(
                    Decimal(i["newest_price_time"])
                ):
                    j["newest_price_time"] = i["newest_price_time"]
                    j["newest_price"] = i["newest_price"]

                if (
                    j["oldest_price_time"] > i["oldest_price_time"]
                    or j["oldest_price_time"] == 0
                ):
                    j["oldest_price_time"] = i["oldest_price_time"]
                    j["oldest_price"] = i["oldest_price"]

                if Decimal(j["highest_bid"]) < Decimal(i["highest_bid"]):
                    j["highest_bid"] = i["highest_bid"]

                if Decimal(j["lowest_ask"]) > Decimal(i["lowest_ask"]):
                    j["lowest_ask"] = i["lowest_ask"]

                if Decimal(j["highest_price_24hr"]) < Decimal(i["highest_price_24hr"]):
                    j["highest_price_24hr"] = i["highest_price_24hr"]

                if (
                    Decimal(j["lowest_price_24hr"]) > Decimal(i["lowest_price_24hr"])
                    or j["lowest_price_24hr"] == 0
                ):
                    j["lowest_price_24hr"] = i["lowest_price_24hr"]

                j["price_change_24hr"] = format_10f(
                    Decimal(j["newest_price"]) - Decimal(j["oldest_price"])
                )
                if Decimal(j["oldest_price"]) > 0:
                    j["price_change_pct_24hr"] = format_10f(
                        Decimal(j["newest_price"]) / Decimal(j["oldest_price"]) - 1
                    )
                else:
                    j["price_change_pct_24hr"] = format_10f(0)
                j["variants"].sort()
        return tickers_data

    def pair(self, pair):
        base, quote = helper.base_quote_from_pair(pair)
        return f"{self.coin(base)}_{self.coin(quote)}"

    def coin(self, coin):
        return coin.split("-")[0]

    # Unused?
    def pair_summary_item(self, i):
        resp = {}
        keys = i.keys()
        for k in keys:
            if k == "ticker_id":
                resp.update({k: self.pair(i[k])})
            elif k in ["base_currency", "quote_currency"]:
                resp.update({k: self.coin(i[k])})
            else:
                resp.update({k: i[k]})
        return resp

    # Unused?
    def last_trade(self, last_traded):
        data = {}
        for i in last_traded:
            pair = deplatform.coin(i)
            if pair not in data:
                data.update({pair: last_traded[i]})
            else:
                if last_traded[i]["last_swap_time"] > data[pair]["last_swap_time"]:
                    data[pair]["last_swap_time"] = last_traded[i]["last_swap_time"]
                    data[pair]["last_swap_uuid"] = last_traded[i]["last_swap_uuid"]
                    data[pair]["last_swap_price"] = last_traded[i]["last_swap_price"]
        return data


class Derive:
    def __init__(self):
        pass

    # TODO: add to Derive class
    def app(self, appname):
        logger.query(f"appname: {appname}")
        gui, match = self.gui(appname)
        appname.replace(match, "")
        app_version, match = self.app_version(appname)
        appname.replace(match, "")
        defi_version, match = self.defi_version(appname)
        appname.replace(match, "")
        # check the last to avoid false positives: e.g. web / web_dex
        device, match = self.device(appname)
        appname.replace(match, "")
        derived_app = f"{gui} {app_version} {device} (sdk: {defi_version})"
        logger.calc(f"appname remaining: {appname}")
        logger.info(f"derived_app: {derived_app}")
        return derived_app

    def gui(self, appname):
        for i in self.DeFiApps:
            for j in self.DeFiApps[i]:
                if j in appname.lower():
                    return i, j
        return "Unknown", ""

    def device(self, appname):
        for i in self.DeFiDevices:
            for j in self.DeFiDevices[i]:
                if j in appname.lower():
                    return i, j
        return "Unknown", ""

    def app_version(self, appname):
        parts = appname.split(" ")
        for i in parts:
            subparts = i.split("-")
            for j in subparts:
                version_parts = j.split(".")
                for k in version_parts:
                    try:
                        int(k)
                    except ValueError:
                        break
                    except Exception as e:
                        logger.warning(e)
                        break
                    return j, j
        return "Unknown", ""

    def defi_version(self, appname):
        parts = appname.split("_")
        for i in parts:
            if len(i) > 6:
                try:
                    int(i, 16)
                    return i, i
                except ValueError:
                    pass
        return "Unknown", ""

    @property
    def DeFiApps():
        return {
            "Adex-CLI": ["adex-cli"],
            "AirDex": ["air_dex", "airdex"],
            "AtomicDEX": ["atomicdex"],
            "BitcoinZ Dex": ["bitcoinz dex"],
            "BumbleBee": ["bumblebee"],
            "CLI": ["cli", "atomicdex client cli"],
            "ColliderDex": ["colliderdex desktop"],
            "DexStats": ["dexstats"],
            "Docs Walkthru": [
                "docs_walkthru",
                "devdocs",
                "core_readme",
                "kmd_atomicdex_api_tutorial",
            ],
            "DogeDex": ["dogedex"],
            "Faucet": ["faucet"],
            "FiroDex": ["firodex", "firo dex"],
            "GleecDex": ["gleecdex"],
            "Komodo Wallet": ["komodo wallet"],
            "Legacy Desktop": ["atomicdex desktop"],
            "Legacy Desktop CE": ["atomicdex desktop ce"],
            "LoreDex": ["lore dex"],
            "MM2 CLI": ["mm2cli"],
            "MM2GUI": ["mm2gui"],
            "NatureDEX": ["naturedex"],
            "Other": [],
            "PirateDex": ["piratedex"],
            "PytomicDex": ["pytomicdex", "pymakerbot"],
            "QA Tools": ["history_spammer_tool", "wasmtest", "artemii_dev", "qa_cli"],
            "ShibaDex": ["shibadex"],
            "SmartDEX": ["smartdex"],
            "SqueexeDEX": ["squeexedex", "squeexe wallet"],
            "SwapCase Desktop": ["swapcase desktop"],
            "Tokel IDO": ["tokel ido"],
            "Unknown": ["unknown"],
            "WebDEX": ["web_dex", "webdex"],
            "mmtools": ["mmtools"],
            "mpm": ["mpm"],
            "NN Seed": ["nn_seed"],
            "No Gui": ["nogui"],
        }

    @property
    def DeFiVersions():
        return {}

    @property
    def DeFiDevices():
        return {
            "ios": ["iOS"],
            "web": ["Web"],
            "android": ["Android"],
            "darwin": ["Mac"],
            "linux": ["Linux"],
            "windows": ["Windows"],
        }


class Invert:
    def __init__(self):
        pass

    def pair(self, pair_str):
        base, quote = helper.base_quote_from_pair(pair_str, True)
        return f"{base}_{quote}"

    def trade_type(self, trade_type):
        if trade_type == "buy":
            return "sell"
        if trade_type == "sell":
            return "buy"
        raise ValueError

    def orderbook(self, orderbook):
        try:
            if "rel" in orderbook:
                quote = orderbook["rel"]
                total_asks_quote_vol = orderbook["total_asks_rel_vol"]["decimal"]
                total_bids_quote_vol = orderbook["total_bids_rel_vol"]["decimal"]
                total_asks_base_vol = orderbook["total_asks_base_vol"]["decimal"]
                total_bids_base_vol = orderbook["total_bids_base_vol"]["decimal"]
            if "quote" in orderbook:
                quote = orderbook["quote"]
                total_asks_quote_vol = orderbook["total_asks_quote_vol"]
                total_bids_quote_vol = orderbook["total_bids_quote_vol"]
                total_asks_base_vol = orderbook["total_asks_base_vol"]
                total_bids_base_vol = orderbook["total_bids_base_vol"]
            inverted = {
                "pair": f'{quote}_{orderbook["base"]}',
                "base": quote,
                "quote": orderbook["base"],
                "num_asks": len(orderbook["bids"]),
                "num_bids": len(orderbook["asks"]),
                "total_asks_base_vol": {"decimal": total_asks_quote_vol},
                "total_asks_rel_vol": {"decimal": total_asks_base_vol},
                "total_bids_base_vol": {"decimal": total_bids_quote_vol},
                "total_bids_rel_vol": {"decimal": total_bids_base_vol},
                "asks": [],
                "bids": [],
            }

            for i in orderbook["asks"]:
                inverted["bids"].append(
                    {
                        "coin": orderbook["rel"],
                        "price": {
                            "decimal": format_10f(1 / Decimal(i["price"]["decimal"]))
                        },
                        "base_max_volume": {"decimal": i["rel_max_volume"]["decimal"]},
                        "rel_max_volume": {"decimal": i["base_max_volume"]["decimal"]},
                    }
                )
            for i in orderbook["bids"]:
                inverted["asks"].append(
                    {
                        "coin": orderbook["base"],
                        "price": {
                            "decimal": format_10f(1 / Decimal(i["price"]["decimal"]))
                        },
                        "base_max_volume": {"decimal": i["rel_max_volume"]["decimal"]},
                        "rel_max_volume": {"decimal": i["base_max_volume"]["decimal"]},
                    }
                )
        except Exception as e:
            logger.warning(e)
        return inverted


class FilterData:
    def __init__(self):
        pass

    @timed
    def dict_lists(self, data: dict, key: str, filter_value: str) -> Decimal:
        """
        list of key values from dicts.
        """
        return [i for i in data if i[key] == filter_value]


class Merge:
    def __init__(self):
        pass

    def segwit_swaps(self, variants, swaps):
        resp = []
        for i in variants:
            resp = resp + swaps[i]
        return sortdata.dict_lists(resp, "finished_at", reverse=True)

    def orderbooks(self, existing, new):
        try:
            existing.update(
                {
                    i: sumdata.dict_lists(existing[i], new[i], sort_key="price")
                    for i in ["asks", "bids"]
                }
            )
            existing.update(
                {i: sumdata.lists(existing[i], new[i]) for i in ["variants"]}
            )
            numerics = [
                "liquidity_in_usd",
                "total_asks_base_vol",
                "total_bids_base_vol",
                "total_asks_quote_vol",
                "total_bids_quote_vol",
                "total_asks_base_usd",
                "total_bids_quote_usd",
            ]

            existing.update(
                {i: sumdata.decimals(existing[i], new[i]) for i in numerics}
            )
            return existing
        except Exception as e:  # pragma: no cover
            logger.warning(new)
            logger.error(existing)
            err = {"error": f"transform.merge.orderbooks: {e}"}
            logger.warning(err)
        return existing

    @timed
    def volumes_data(
        self,
        data,
        suffix,
        swaps_for_pair,
        base_usd_price,
        quote_usd_price,
        sorted_pair_str,
    ):
        try:
            swaps_volumes = helper.get_swaps_volumes(swaps_for_pair, sorted_pair_str)
            base_volume_usd = swaps_volumes[0] * base_usd_price
            quote_volume_usd = swaps_volumes[1] * quote_usd_price
            # Halving the combined volume to not double count, and
            # get average between base and quote
            combined_volume_usd = (base_volume_usd + quote_volume_usd) / 2
            data.update(
                {
                    f"trades_{suffix}": sumdata.ints(
                        data[f"trades_{suffix}"], len(swaps_for_pair)
                    ),
                    "base_volume": sumdata.decimals(
                        data["base_volume"], swaps_volumes[0]
                    ),
                    "quote_volume": sumdata.decimals(
                        data["quote_volume"], swaps_volumes[1]
                    ),
                    "base_volume_usd": sumdata.decimals(
                        data["base_volume_usd"], base_volume_usd
                    ),
                    "quote_volume_usd": sumdata.decimals(
                        data["quote_volume_usd"], quote_volume_usd
                    ),
                    "combined_volume_usd": sumdata.decimals(
                        data["combined_volume_usd"], combined_volume_usd
                    ),
                    "variants": data["variants"],
                }
            )
            msg = f'Combined vol: {data["combined_volume_usd"]}'
            return default.result(data=data, msg=msg, loglevel="dexrpc", ignore_until=0)
        except Exception as e:
            logger.warning(e)


class SortData:
    def __init__(self):
        pass

    def dict_lists(self, data: List, key: str, reverse=False) -> dict:
        """
        Sort a list of dicts by the value of a key.
        """
        resp = sorted(data, key=lambda k: k[key], reverse=reverse)
        return resp

    def dicts(self, data: dict, reverse=False) -> dict:
        """
        Sort a dict by the value the root key.
        """
        k = list(data.keys())
        k.sort()
        if reverse:
            k.reverse()
        resp = {}
        for i in k:
            resp.update({i: data[i]})
        return resp

    def top_items(self, data: List[Dict], sort_key: str, length: int = 5):
        data.sort(key=lambda x: x[sort_key], reverse=True)
        return data[:length]

    @timed
    def top_pairs(self, summaries: list):
        try:
            for i in summaries:
                i["ticker_id"] = deplatform.pair(i["ticker_id"])

            top_pairs_by_value = {
                i["ticker_id"]: i["pair_trade_value_usd"]
                for i in self.top_items(summaries, "pair_trade_value_usd", 5)
            }
            top_pairs_by_liquidity = {
                i["ticker_id"]: i["pair_liquidity_usd"]
                for i in self.top_items(summaries, "pair_liquidity_usd", 5)
            }
            top_pairs_by_swaps = {
                i["ticker_id"]: i["pair_swaps_count"]
                for i in self.top_items(summaries, "pair_swaps_count", 5)
            }
            return {
                "by_value_traded_usd": clean.decimal_dicts(top_pairs_by_value),
                "by_current_liquidity_usd": clean.decimal_dicts(top_pairs_by_liquidity),
                "by_swaps_count": clean.decimal_dicts(top_pairs_by_swaps),
            }
        except Exception as e:
            logger.error(f"{type(e)} Error in [get_top_pairs]: {e}")
            return {"by_volume": [], "by_liquidity": [], "by_swaps": []}

    @timed
    def pair_by_market_cap(self, pair_str: str, gecko_source=None) -> str:
        try:
            if gecko_source is None:
                gecko_source = memcache.get_gecko_source()
            if gecko_source is not None:
                base, quote = helper.base_quote_from_pair(pair_str)
                base_mc = 0
                quote_mc = 0
                if base.replace("-segwit", "") in gecko_source:
                    base_mc = Decimal(
                        gecko_source[base.replace("-segwit", "")]["usd_market_cap"]
                    )
                if quote.replace("-segwit", "") in gecko_source:
                    quote_mc = Decimal(
                        gecko_source[quote.replace("-segwit", "")]["usd_market_cap"]
                    )
                if quote_mc < base_mc:
                    pair_str = invert.pair(pair_str)
                elif quote_mc == base_mc:
                    pair_str = "_".join(sorted([base, quote]))
        except Exception as e:  # pragma: no cover
            msg = f"pair_by_market_cap failed: {e}"
            logger.warning(msg)

        return pair_str


class SumData:
    def __init__(self):
        pass

    def decimals(self, x, y):
        try:
            return Decimal(x) + Decimal(y)
        except Exception as e:
            logger.warning(f"{type(e)}: {e}")
            logger.warning(f"x: {x} ({type(x)})")
            logger.warning(f"y: {y} ({type(y)})")
            raise ValueError

    def numeric_str(self, val1, val2):
        x = Decimal(val1) + Decimal(val2)
        return format_10f(x)

    def lists(self, x, y, sorted=True):
        try:
            data = x + y
            if not [isinstance(i, dict) for i in data]:
                data = list(set(data))
            if sorted:
                data.sort()
            return data
        except Exception as e:
            logger.warning(f"{type(e)}: {e}")
            logger.warning(f"x: {x} ({type(x)})")
            logger.warning(f"y: {y} ({type(y)})")
            raise ValueError

    def dict_lists(self, x, y, sort_key=None):
        try:
            if sort_key:
                merged_list = self.lists(x, y, False)
                if [sort_key in i for i in merged_list]:
                    return sortdata.dict_lists(merged_list, sort_key)
                return merged_list
            return self.lists(x, y)
        except Exception as e:
            logger.warning(f"{type(e)}: {e}")
            logger.warning(f"x: {x} ({type(x)})")
            logger.warning(f"y: {y} ({type(y)})")
            raise ValueError

    def ints(self, x, y):
        try:
            return int(x) + int(y)
        except Exception as e:
            logger.warning(f"{type(e)}: {e}")
            logger.warning(f"x: {x} ({type(x)})")
            logger.warning(f"y: {y} ({type(y)})")
            raise ValueError

    def json_key(self, data: dict, key: str) -> Decimal:
        """
        Sum a key from a list of dicts.
        """
        return sum(Decimal(d[key]) for d in data)

    def json_key_10f(self, data: dict, key: str) -> str:
        """
        Sum a key from a list of dicts and format to 10 decimal places.
        """
        return format_10f(self.json_key(data, key))


# Uncategorized
@timed
def get_coin_platform(coin):
    r = coin.split("-")
    if len(r) == 2:
        return r[1]
    return ""


@timed
def last_trade_time_filter(last_traded, start_time, end_time):
    # TODO: handle first/last within variants
    last_traded = memcache.get_last_traded()
    last_traded = [
        i for i in last_traded if last_traded[i]["last_swap_time"] > start_time
    ]
    last_traded = [
        i for i in last_traded if last_traded[i]["last_swap_time"] < end_time
    ]
    return last_traded


@timed
def label_bids_asks(orderbook_data, pair):
    data = template.orderbook(pair)
    for i in ["asks", "bids"]:
        data[i] = [
            {
                "price": format_10f(Decimal(j["price"]["decimal"])),
                "volume": j["base_max_volume"]["decimal"],
                "quote_volume": j["rel_max_volume"]["decimal"],
            }
            for j in orderbook_data[i]
        ]
    return data


@timed
def round_to_str(value: Any, rounding=8):
    try:
        if isinstance(value, (str, int, float)):
            value = Decimal(value)
        if isinstance(value, Decimal):
            value = value.quantize(Decimal(f'1.{"0" * rounding}'))
        else:
            raise TypeError(f"Invalid type: {type(value)}")
    except (ValueError, TypeError, InvalidOperation) as e:  # pragma: no cover
        logger.muted(f"{type(e)} Error rounding {value}: {e}")
        value = 0
    except Exception as e:  # pragma: no cover
        logger.error(e)
        value = 0
    return f"{value:.{rounding}f}"


@timed
def get_suffix(days: int) -> str:
    if days == 1:
        return "24hr"
    else:
        return f"{days}d"


@timed
def format_10f(number: float | Decimal) -> str:
    """
    Format a float to 10 decimal places.
    """
    if isinstance(number, str):
        number = Decimal(number)
    return f"{number:.10f}"


@timed
def update_if_greater(existing, new, key, secondary_key=None):
    if existing[key] < new[key]:
        existing[key] = new[key]
        if secondary_key is not None:
            existing[secondary_key] = new[secondary_key]


@timed
def update_if_lesser(existing, new, key, secondary_key=None):
    if existing[key] > new[key]:
        existing[key] = new[key]
        if secondary_key is not None:
            existing[secondary_key] = new[secondary_key]


clean = Clean()
convert = Convert()
deplatform = Deplatform()
derive = Derive()
filterdata = FilterData()
invert = Invert()
merge = Merge()
sortdata = SortData()
sumdata = SumData()
