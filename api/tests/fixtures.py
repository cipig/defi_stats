#!/usr/bin/env python3
import os
import sys
import pytest
from decimal import Decimal

API_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(API_ROOT_PATH)
from util.cron import Time
from lib.external import CoinGeckoAPI
from lib.dex_api import DexAPI
from util.utils import Utils
from util.files import Files
from util.urls import Urls
from lib.calc import Calc
from util.logger import logger
from lib.cache import Cache
from lib.cache_item import CacheItem
from lib.pair import Pair
from db.sqlitedb import SqliteDB, get_sqlite_db
from db.sqlitedb_query import SqliteQuery
from db.sqlitedb_update import SqliteUpdate
from lib.orderbook import Orderbook
import util.helper as helper
from const import templates

logger.info("Loading test fixtures...")


@pytest.fixture
def setup_fake_db():
    """Fixture to set up the in-memory database with test data"""
    DB = SqliteDB(db_path=":memory:", testing=True, dict_format=False)
    DB.sql_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stats_swaps (
            id INTEGER NOT NULL PRIMARY KEY,
            maker_coin VARCHAR(255) NOT NULL,
            taker_coin VARCHAR(255) NOT NULL,
            uuid VARCHAR(255) NOT NULL UNIQUE,
            started_at INTEGER NOT NULL,
            finished_at INTEGER NOT NULL,
            maker_amount DECIMAL NOT NULL,
            taker_amount DECIMAL NOT NULL,
            is_success INTEGER NOT NULL,
            maker_coin_ticker VARCHAR(255) NOT NULL DEFAULT '',
            maker_coin_platform VARCHAR(255) NOT NULL DEFAULT '',
            taker_coin_ticker VARCHAR(255) NOT NULL DEFAULT '',
            taker_coin_platform VARCHAR(255) NOT NULL DEFAULT '',
            maker_coin_usd_price DECIMAL,
            taker_coin_usd_price DECIMAL
        );
    """
    )
    yield DB


@pytest.fixture
def setup_actual_db():
    yield get_sqlite_db()


@pytest.fixture
def setup_dexapi():
    yield DexAPI(testing=True)


@pytest.fixture
def setup_calc():
    yield Calc(testing=True)


@pytest.fixture
def setup_sqlite_query():
    yield SqliteQuery(testing=True)


@pytest.fixture
def setup_sqlite_update():
    yield SqliteUpdate(testing=True)


@pytest.fixture
def setup_cache_item():
    yield CacheItem(testing=True)


@pytest.fixture
def setup_files():
    yield Files(testing=True)


@pytest.fixture
def setup_urls():
    yield Urls(testing=True)


@pytest.fixture
def setup_time():
    yield Time(from_ts=1700000000)


@pytest.fixture
def setup_gecko():
    yield CoinGeckoAPI(testing=True)


@pytest.fixture
def setup_gecko_coin_ids(setup_gecko):
    gecko = setup_gecko
    yield gecko.get_gecko_coin_ids_list()


@pytest.fixture
def setup_gecko_info(setup_gecko):
    gecko = setup_gecko
    yield gecko.get_gecko_info_dict()


@pytest.fixture
def setup_cache():
    yield Cache(testing=True)


@pytest.fixture
def setup_helper():
    yield helper


@pytest.fixture
def setup_templates():
    yield templates


@pytest.fixture
def setup_rick_morty_tuple_pair():
    yield Pair(("RICK", "MORTY"), testing=True)


@pytest.fixture
def setup_rick_morty_str_pair():
    yield Pair("RICK_MORTY", testing=True)


@pytest.fixture
def setup_dgb_kmd_str_pair(setup_swaps_db_data):
    yield Pair("DGB_KMD", testing=True)


@pytest.fixture
def setup_dgb_kmd_orderbook(setup_dgb_kmd_str_pair):
    pair = setup_dgb_kmd_str_pair
    yield Orderbook(pair=pair, testing=True)


@pytest.fixture
def setup_kmd_dgb_tuple_pair(setup_swaps_db_data):
    yield Pair(("KMD", "DGB"), testing=True)


@pytest.fixture
def setup_kmd_dgb_orderbook(setup_kmd_dgb_tuple_pair):
    pair = setup_kmd_dgb_tuple_pair
    yield Orderbook(pair=pair, testing=True)


@pytest.fixture
def setup_kmd_ltc_str_pair(setup_swaps_db_data):
    yield Pair("KMD_LTC", testing=True)


@pytest.fixture
def setup_ltc_kmd_list_pair(setup_swaps_db_data):
    yield Pair(["LTC", "KMD"], testing=True)


@pytest.fixture
def setup_kmd_ltc_orderbook(setup_kmd_ltc_str_pair):
    pair = setup_kmd_ltc_str_pair
    yield Orderbook(pair=pair, testing=True)


@pytest.fixture
def setup_kmd_btc_list_pair(setup_swaps_db_data):
    yield Pair(["KMD", "BTC"], testing=True)


@pytest.fixture
def setup_kmd_btc_orderbook(setup_swaps_db_data, setup_kmd_btc_str_pair):
    pair = setup_kmd_btc_str_pair
    yield Orderbook(pair=pair, testing=True)


@pytest.fixture
def setup_not_a_real_pair():
    yield Pair("NotARealPair", testing=True)


@pytest.fixture
def setup_three_ticker_pair():
    yield Pair("NOT_GONNA_WORK", testing=True)


@pytest.fixture
def setup_not_existing_pair():
    yield Pair("XYZ_123", testing=True)


@pytest.fixture
def setup_utils():
    yield Utils(testing=True)


@pytest.fixture
def setup_kmd_btc_segwit_orderbook_data(setup_utils):
    utils = setup_utils
    file = f"{API_ROOT_PATH}/tests/fixtures/orderbook/KMD_BTC-segwit.json"
    orderbook = utils.load_jsonfile(file)
    yield orderbook


@pytest.fixture
def setup_kmd_btc_bep20_orderbook_data(setup_utils):
    utils = setup_utils
    file = f"{API_ROOT_PATH}/tests/fixtures/orderbook/KMD_BTC-BEP20.json"
    orderbook = utils.load_jsonfile(file)
    yield orderbook


@pytest.fixture
def setup_kmd_btc_orderbook_data(setup_utils):
    utils = setup_utils
    file = f"{API_ROOT_PATH}/tests/fixtures/orderbook/KMD_BTC.json"
    orderbook = utils.load_jsonfile(file)
    yield orderbook


@pytest.fixture
def setup_swaps_db_data(setup_fake_db, setup_time):
    time = setup_time
    sample_data = [
        (
            4,
            "MCL",
            "KMD",
            "44444444-FAIL-FAIL-FAIL-44444444",
            time.hours_ago(1) - 3,
            time.hours_ago(1) + 3,
            1,
            1,
            0,
            "MCL",
            "",
            "KMD",
            "",
            None,
            None,
        ),
        (
            1,
            "KMD",
            "MORTY",
            "11111111-ffe1-4c7a-ad7f-04b1df6323b6",
            time.hours_ago(1) - 1,
            time.hours_ago(1) + 1,
            1,
            1,
            1,
            "KMD",
            "",
            "MORTY",
            "",
            None,
            None,
        ),
        (
            2,
            "DGB-segwit",
            "KMD-BEP20",
            "22222222-fd33-4dc4-2a7f-f6320b1d3b64",
            time.hours_ago(1) - 2,
            time.hours_ago(1) + 2,
            1000,
            1,
            1,
            "DGB",
            "segwit",
            "KMD",
            "BEP20",
            None,
            None,
        ),
        (
            3,
            "DGB-segwit",
            "KMD-BEP20",
            "33333333-fd33-4dc4-2a7f-f6320b1d3b64",
            time.hours_ago(1) + 5,
            time.hours_ago(1) + 60,
            500,
            0.9,
            1,
            "DGB",
            "segwit",
            "KMD",
            "BEP20",
            None,
            None,
        ),
        (
            5,
            "DGB",
            "LTC",
            "55555555-ee4b-494f-a2fb-48467614b613",
            time.hours_ago(1),
            time.hours_ago(1) + 4,
            1,
            1,
            1,
            "DGB",
            "",
            "LTC",
            "",
            None,
            None,
        ),
        (
            6,
            "KMD",
            "LTC-segwit",
            "666666666-75a2-d4ef-009d-5e9baad162ef",
            time.hours_ago(1),
            time.hours_ago(1) + 5,
            1,
            5,
            1,
            "KMD",
            "",
            "LTC",
            "segwit",
            None,
            None,
        ),
        (
            7,
            "LTC-segwit",
            "KMD",
            "77777777-2762-4633-8add-6ad2e9b1a4e7",
            time.hours_ago(2),
            time.hours_ago(2) + 6,
            10,
            1,
            1,
            "LTC",
            "segwit",
            "KMD",
            "",
            None,
            None,
        ),
        (
            8,
            "KMD",
            "BTC",
            "888888888-7622-6334-add8-9b1a4e76ad2e",
            time.hours_ago(3),
            time.hours_ago(3) + 7,
            1000000,
            1,
            1,
            "KMD",
            "",
            "BTC",
            "",
            None,
            None,
        ),
        (
            9,
            "LTC",
            "KMD",
            "999999999-73a2-d46d-900d-aad5e9b162ef",
            time.hours_ago(4),
            time.hours_ago(4) + 8,
            20,
            1,
            1,
            "LTC",
            "",
            "KMD",
            "",
            None,
            None,
        ),
        (
            10,
            "KMD-BEP20",
            "BTC",
            "AAAAAAAA-273f-40a5-bcd4-31efdb6bcc8b",
            time.days_ago(1) - 900,
            time.days_ago(1) - 300,
            2000000,
            1,
            1,
            "KMD",
            "BEP20",
            "BTC",
            "",
            None,
            None,
        ),
        (
            11,
            "BTC",
            "LTC",
            "BBBBBBBB-ac6f-4649-b420-5eb8e2924bf2",
            time.days_ago(7) - 900,
            time.days_ago(7) + 10,
            5,
            1,
            1,
            "BTC",
            "",
            "LTC",
            "",
            None,
            None,
        ),
        (
            12,
            "DGB",
            "LTC-segwit",
            "CCCCCCCC-40a5-4649-b420-5eb8e2924bf2",
            time.days_ago(7) - 900,
            time.days_ago(7) + 11,
            100000,
            1,
            1,
            "DGB",
            "",
            "LTC",
            "segwit",
            None,
            None,
        ),
        (
            13,
            "DGB-segwit",
            "LTC",
            "DDDDDDDD-ac6f-a2fb-b360-4bf25fed4292",
            time.days_ago(30) - 900,
            time.days_ago(30) + 12,
            200000,
            1,
            1,
            "DGB",
            "segwit",
            "LTC",
            "",
            None,
            None,
        ),
        (
            14,
            "LTC",
            "DOGE",
            "EEEEEEEE-ee4b-494f-a2fb-48467614b613",
            time.days_ago(60) - 900,
            time.days_ago(60) + 13,
            10,
            1,
            1,
            "LTC",
            "",
            "DOGE",
            "",
            None,
            None,
        ),
        (
            15,
            "DOGE",
            "LTC",
            "FFFFFFFF-ee4b-494f-a2fb-48467614b613",
            time.days_ago(60) - 900,
            time.days_ago(60) + 10,
            1,
            10,
            1,
            "DOGE",
            "",
            "LTC",
            "",
            None,
            None,
        ),
    ]
    sql = "INSERT INTO stats_swaps VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    DB = setup_fake_db
    DB.sql_cursor.executemany(sql, sample_data)
    yield DB


@pytest.fixture
def historical_trades():
    return [
        {
            "trade_id": "2b22b6b9-c7b2-48c4-acb7-ed9077c8f47d",
            "price": "0.8000000000",
            "base_volume": "20",
            "target_volume": "16",
            "timestamp": "1697471102",
            "type": "buy",
        },
        {
            "trade_id": "c76ed996-d44a-4e39-998e-acb68681b0f9",
            "price": "1.0000000000",
            "base_volume": "20",
            "target_volume": "20",
            "timestamp": "1697471080",
            "type": "buy",
        },
        {
            "trade_id": "d2602fa9-6680-42f9-9cb8-20f76275f587",
            "price": "1.2000000000",
            "base_volume": "20",
            "target_volume": "24",
            "timestamp": "1697469503",
            "type": "buy",
        },
        {
            "trade_id": "c80e9b57-406f-4f9c-8b41-79ff2623cc7a",
            "price": "1.0000000000",
            "base_volume": "10",
            "target_volume": "10",
            "timestamp": "1697475729",
            "type": "sell",
        },
        {
            "trade_id": "09d72ac9-3e55-4e84-9f32-cf22b5b442ad",
            "price": "1.0000000000",
            "base_volume": "20",
            "target_volume": "20",
            "timestamp": "1697448297",
            "type": "sell",
        },
    ]


@pytest.fixture
def historical_data():
    return {
        "ticker_id": "KMD_LTC",
        "start_time": "1697394564",
        "end_time": "1697480964",
        "limit": "100",
        "trades_count": "5",
        "sum_base_volume_buys": "60",
        "sum_base_volume_sells": "30",
        "sum_target_volume_buys": "60",
        "sum_target_volume_sells": "30",
        "average_price": "1",
        "buy": [
            {
                "trade_id": "2b22b6b9-c7b2-48c4-acb7-ed9077c8f47d",
                "price": "0.8000000000",
                "base_volume": "20",
                "target_volume": "16",
                "timestamp": "1697471102",
                "type": "buy",
            },
            {
                "trade_id": "c76ed996-d44a-4e39-998e-acb68681b0f9",
                "price": "1.0000000000",
                "base_volume": "20",
                "target_volume": "20",
                "timestamp": "1697471080",
                "type": "buy",
            },
            {
                "trade_id": "d2602fa9-6680-42f9-9cb8-20f76275f587",
                "price": "1.2000000000",
                "base_volume": "20",
                "target_volume": "24",
                "timestamp": "1697469503",
                "type": "buy",
            },
        ],
        "sell": [
            {
                "trade_id": "c80e9b57-406f-4f9c-8b41-79ff2623cc7a",
                "price": "1.0000000000",
                "base_volume": "10",
                "target_volume": "10",
                "timestamp": "1697475729",
                "type": "sell",
            },
            {
                "trade_id": "09d72ac9-3e55-4e84-9f32-cf22b5b442ad",
                "price": "1.0000000000",
                "base_volume": "20",
                "target_volume": "20",
                "timestamp": "1697448297",
                "type": "sell",
            },
        ],
    }


@pytest.fixture
def dirty_dict():
    yield {
        "a": Decimal("1.23456789"),
        "b": "string",
        "c": 1,
        "d": False,
        "e": ["foo", "bar"],
        "f": {"foo": "bar"},
    }


@pytest.fixture
def no_trades_info():
    yield []

@pytest.fixture
def coins_config():
    yield {
        "NOSWAP": {
            "wallet_only": True,
            "is_testnet": False
        },
        "TEST": {
            "wallet_only": False,
            "is_testnet": True
        },
        "OK": {
            "wallet_only": False,
            "is_testnet": False
        }
    }


@pytest.fixture
def trades_info():
    yield [
        {
            "trade_id": "2b22b6b9-c7b2-48c4-acb7-ed9077c8f47d",
            "price": "0.8000000000",
            "base_volume": "20",
            "target_volume": "16",
            "timestamp": "1697471102",
            "type": "buy",
        },
        {
            "trade_id": "c76ed996-d44a-4e39-998e-acb68681b0f9",
            "price": "1.0000000000",
            "base_volume": "20",
            "target_volume": "20",
            "timestamp": "1697471080",
            "type": "buy",
        },
        {
            "trade_id": "d2602fa9-6680-42f9-9cb8-20f76275f587",
            "price": "1.2000000000",
            "base_volume": "20",
            "target_volume": "24",
            "timestamp": "1697469503",
            "type": "buy",
        },
    ]
