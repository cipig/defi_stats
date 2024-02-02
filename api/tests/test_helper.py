import time
import pytest
from decimal import Decimal
from lib.generic import Generic
from tests.fixtures_data import swap_item, swap_item2
from util.logger import logger
import util.helper as helper
import util.memcache as memcache
import util.transform as transform

generic = Generic()


def test_get_mm2_rpc_port():
    assert helper.get_mm2_rpc_port("7777") == 7877
    assert helper.get_mm2_rpc_port(7777) == 7877
    assert helper.get_mm2_rpc_port("8762") == 7862
    assert helper.get_mm2_rpc_port("ALL") == 7862

    with pytest.raises(Exception):
        assert helper.get_mm2_rpc_port("nope") == 7862


def test_get_netid_filename():
    assert helper.get_netid_filename("filename.ext", "7777") == "filename_7777.ext"


def test_get_chunks():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    chunks = list(helper.get_chunks(data, 3))
    assert len(chunks) == 4
    assert len(chunks[0]) == 3
    assert len(chunks[3]) == 1


def test_get_price_at_finish():
    r = helper.get_price_at_finish(swap_item)
    assert "1700000777" in r
    assert r["1700000777"] == 0.01
    r = helper.get_price_at_finish(swap_item, is_reverse=True)
    assert "1700000777" in r
    assert r["1700000777"] == 100

    r = helper.get_price_at_finish(swap_item2)
    assert "1700000000" in r
    assert r["1700000000"] == 0.01
    r = helper.get_price_at_finish(swap_item2, is_reverse=True)
    assert "1700000000" in r
    assert r["1700000000"] == 100


def test_get_pairs_info():
    pairs = ["KMD_LTC", "LTC-segwit_KMD", "DOC_LTC"]
    r = helper.get_pairs_info(pairs, True)
    assert len(r) == 3
    assert r[0]["priced"]


def test_get_pair_info_sorted():
    pairs = ["KMD_LTC", "LTC-segwit_KMD", "DOC_LTC", "BTC_DGB-segwit"]
    r = helper.get_pair_info_sorted(pairs, False)
    assert len(r) == 4
    assert r[0]["ticker_id"] == "BTC_DGB-segwit"
    assert not r[0]["priced"]


def test_base_quote_from_pair():
    base, quote = helper.base_quote_from_pair("XXX-PLG20_OLD_YYY-PLG20_OLD")
    assert base == "XXX-PLG20_OLD"
    assert quote == "YYY-PLG20_OLD"


def test_get_coin_variants():
    r = helper.get_coin_variants("BTC")
    assert "BTC-BEP20" in r
    assert "BTC-segwit" in r
    assert "BTC" in r
    assert len(r) > 2
    r = helper.get_coin_variants("BTC", True)
    assert "BTC-BEP20" not in r
    assert "BTC-segwit" in r
    assert "BTC" in r
    assert len(r) == 2

    r = helper.get_coin_variants("USDC")
    assert "USDC-BEP20" in r
    assert "USDC-PLG20" in r
    assert "USDC-PLG20_OLD" in r
    assert "BTC-segwit" not in r
    assert "USDC" not in r
    assert len(r) > 6


def test_get_pair_variants():
    r = helper.get_pair_variants("KMD_LTC")
    assert "KMD_LTC" in r
    assert "KMD_LTC-segwit" in r
    assert "KMD-BEP20_LTC" in r
    assert "KMD-BEP20_LTC-segwit" in r
    assert len(r) == 4

    r = helper.get_pair_variants("KMD_LTC-segwit")
    assert "KMD_LTC" in r
    assert "KMD_LTC-segwit" in r
    assert "KMD-BEP20_LTC" in r
    assert "KMD-BEP20_LTC-segwit" in r
    assert len(r) == 4

    r = helper.get_pair_variants("LTC_KMD")
    assert "LTC_KMD" in r
    assert "LTC-segwit_KMD" in r
    assert "LTC_KMD-BEP20" in r
    assert "LTC-segwit_KMD-BEP20" in r
    assert len(r) == 4

    r = helper.get_pair_variants("KMD_USDC")
    assert "KMD_USDC" not in r
    assert "KMD_USDC-PLG20" in r
    assert "KMD_USDC-PLG20_OLD" in r
    assert "KMD-BEP20_USDC-PLG20_OLD" in r

    r = helper.get_pair_variants("KMD_USDC-PLG20")
    assert "KMD_USDC" not in r
    assert "KMD_USDC-PLG20" in r
    assert "KMD_USDC-PLG20_OLD" in r
    assert "KMD-BEP20_USDC-PLG20_OLD" in r


def test_find_lowest_ask():
    orderbook = generic.orderbook("KMD_BTC", all=True)
    time.sleep(1)
    orderbook = generic.orderbook("KMD_BTC", all=True)

    r = helper.find_lowest_ask(orderbook)
    assert transform.format_10f(r) == transform.format_10f(1 / 24)


def test_find_highest_bid():
    orderbook = generic.orderbook("KMD_BTC", all=True)
    time.sleep(1)
    orderbook = generic.orderbook("KMD_BTC", all=True)
    r = helper.find_highest_bid(orderbook)
    assert transform.format_10f(r) == transform.format_10f(1 / 26)
