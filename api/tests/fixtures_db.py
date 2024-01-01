#!/usr/bin/env python3
import os
import sys
import time
import pytest


API_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(API_ROOT_PATH)

from db.sqlitedb import SqliteDB
from db.sqlitedb import get_sqlite_db
from util.cron import Time
from lib.pair import Pair
from util.logger import logger


@pytest.fixture
def setup_time():
    yield Time(from_ts=int(time.time()))


@pytest.fixture
def setup_swaps_db_data(setup_time):
    """Fixture to set up the in-memory database with test data"""
    db = SqliteDB(db_path=":memory:", testing=True)
    db.sql_cursor.execute(
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
    db.conn.commit()
    time_obj = setup_time
    sample_data = [
        (
            4,
            "MCL",
            "KMD",
            "44444444-FAIL-FAIL-FAIL-44444444",
            time_obj.hours_ago(1) - 3,
            time_obj.hours_ago(1) + 3,
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
            time_obj.hours_ago(1) - 1,
            time_obj.hours_ago(1) + 1,
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
            time_obj.hours_ago(1) - 2,
            time_obj.hours_ago(1) + 2,
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
            time_obj.hours_ago(1) + 5,
            time_obj.hours_ago(1) + 60,
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
            time_obj.hours_ago(1),
            time_obj.hours_ago(1) + 4,
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
            time_obj.hours_ago(1),
            time_obj.hours_ago(1) + 5,
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
            time_obj.hours_ago(2),
            time_obj.hours_ago(2) + 6,
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
            time_obj.hours_ago(3),
            time_obj.hours_ago(3) + 7,
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
            time_obj.hours_ago(4),
            time_obj.hours_ago(4) + 8,
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
            time_obj.days_ago(1) - 900,
            time_obj.days_ago(1) - 300,
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
            time_obj.days_ago(7) - 900,
            time_obj.days_ago(7) + 10,
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
            time_obj.days_ago(7) - 900,
            time_obj.days_ago(7) + 11,
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
            time_obj.days_ago(30) - 900,
            time_obj.days_ago(30) + 12,
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
            time_obj.days_ago(60) - 900,
            time_obj.days_ago(60) + 13,
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
            time_obj.days_ago(60) - 900,
            time_obj.days_ago(60) + 10,
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
    db.sql_cursor.executemany(sql, sample_data)
    db.conn.commit()
    yield db


@pytest.fixture
def setup_actual_db():
    yield get_sqlite_db()


@pytest.fixture
def setup_kmd_btc_pair(setup_swaps_db_data):
    db = setup_swaps_db_data
    yield Pair("KMD_BTC", testing=True, db=db)


@pytest.fixture
def setup_kmd_dgb_pair(setup_swaps_db_data):
    db = setup_swaps_db_data
    yield Pair("KMD_DGB", testing=True, db=db)


@pytest.fixture
def setup_kmd_ltc_pair(setup_swaps_db_data):
    db = setup_swaps_db_data
    yield Pair("KMD_LTC", testing=True, db=db)


@pytest.fixture
def setup_dgb_kmd_pair(setup_swaps_db_data):
    db = setup_swaps_db_data
    yield Pair("DGB_KMD", testing=True, db=db)


@pytest.fixture
def setup_ltc_kmd_pair(setup_swaps_db_data):
    db = setup_swaps_db_data
    yield Pair("LTC_KMD", testing=True, db=db)


@pytest.fixture
def setup_btc_kmd_pair(setup_swaps_db_data):
    db = setup_swaps_db_data
    yield Pair("BTC_KMD", testing=True, db=db)


@pytest.fixture
def setup_not_a_real_pair(setup_swaps_db_data):
    db = setup_swaps_db_data
    yield Pair("NotARealPair", testing=True, db=db)


@pytest.fixture
def setup_three_ticker_pair(setup_swaps_db_data):
    db = setup_swaps_db_data
    yield Pair("NOT_GONNA_WORK", testing=True, db=db)


@pytest.fixture
def setup_not_existing_pair(setup_swaps_db_data):
    db = setup_swaps_db_data
    yield Pair("XYZ_123", testing=True, db=db)
