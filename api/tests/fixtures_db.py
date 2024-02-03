#!/usr/bin/env python3
import pytest
from sqlmodel import Session, SQLModel, create_engine
from util.logger import logger
import db
from util.cron import Time
import util.cron as cron
import util.memcache as memcache
import util.transform as transform

from const import POSTGRES_HOST, POSTGRES_USERNAME, POSTGRES_PASSWORD, POSTGRES_PORT

clean = transform.Clean()

gecko_source = memcache.get_gecko_source()
coins_config = memcache.get_coins_config()


@pytest.fixture
def setup_time():
    yield Time(from_ts=int(cron.now_utc()))


TEST_DB_NAME = "defi_swaps_test"
TEST_DB_HOST = f"{POSTGRES_HOST}:{POSTGRES_PORT}"
TEST_DB_CREDS = f"{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}"
TEST_DB_URL = f"postgresql://{TEST_DB_CREDS}@{TEST_DB_HOST}"
logger.info(TEST_DB_URL)


def reset_test_defi_stats_table():
    pgdb = db.SqlUpdate(db_type="pgsql")
    try:
        pgdb.drop("defi_swaps_test")
    except Exception as e:
        logger.warning(e)
    SQLModel.metadata.create_all(pgdb.engine)
    logger.merge("Created PGSQL Test Table")


@pytest.fixture
def setup_actual_db():
    pgdb_query = db.SqlQuery(db_type="pgsql")
    yield pgdb_query


@pytest.fixture()
def setup_swaps_db_data(setup_time):
    pg_query = db.SqlQuery(db_type="pgsql")
    time_obj = setup_time
    engine = create_engine(TEST_DB_URL)

    reset_test_defi_stats_table()

    sample_data = [
        {
            "taker_coin": "MCL",
            "maker_coin": "KMD",
            "uuid": "00000000-FAIL-FAIL-FAIL-00000000",
            "started_at": time_obj.minutes_ago(1) - 180,
            "finished_at": time_obj.hours_ago(1) + 3,
            "taker_amount": 1,
            "maker_amount": 1,
            "is_success": 0,
            "taker_coin_ticker": "MCL",
            "taker_coin_platform": "",
            "maker_coin_ticker": "KMD",
            "maker_coin_platform": "",
            "taker_gui": "pytomicDEX",
            "maker_gui": "AtomicDEX Desktop",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "1.2",
            "maker_version": "1.3",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 1.0,
            "reverse_price": 1.0,
            "trade_type": "sell",
            "pair": "MCL_KMD",
            "pair_reverse": "KMD_MCL",
            "pair_std": "MCL_KMD",
            "pair_std_reverse": "KMD_MCL",
            "last_updated": "",
        },
        {
            "taker_coin": "KMD",
            "maker_coin": "MORTY",
            "uuid": "11111111-ffe1-4c7a-ad7f-04b1df6323b6",
            "started_at": time_obj.hours_ago(1) - 1,
            "finished_at": time_obj.hours_ago(1) + 1,
            "taker_amount": 1,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "KMD",
            "taker_coin_platform": "",
            "maker_coin_ticker": "MORTY",
            "maker_coin_platform": "",
            "taker_gui": "komodo-wallet-web-5.8",
            "maker_gui": "komodo-wallet-web-5.8.1",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "2.0.0-beta_b0fd99e",
            "maker_version": "1.0.7-beta",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 1.0,
            "reverse_price": 1.0,
            "trade_type": "buy",
            "pair": "MORTY_KMD",
            "pair_reverse": "KMD_MORTY",
            "pair_std": "MORTY_KMD",
            "pair_std_reverse": "KMD_MORTY",
            "last_updated": "",
        },
        {
            "taker_coin": "DGB-segwit",
            "maker_coin": "KMD-BEP20",
            "uuid": "22222222-fd33-4dc4-2a7f-f6320b1d3b64",
            "started_at": time_obj.hours_ago(1) - 2,
            "finished_at": time_obj.hours_ago(1) + 2,
            "taker_amount": 1000,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "DGB",
            "taker_coin_platform": "segwit",
            "maker_coin_ticker": "KMD",
            "maker_coin_platform": "BEP20",
            "taker_gui": "Komodo Wallet 0.7.0-beta",
            "maker_gui": "mpm",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "2.0.1-beta",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 0.001,
            "reverse_price": 1000.0,
            "trade_type": "buy",
            "pair": "KMD-BEP20_DGB-segwit",
            "pair_reverse": "DGB-segwit_KMD-BEP20",
            "pair_std": "KMD_DGB",
            "pair_std_reverse": "DGB_KMD",
            "last_updated": "",
        },
        {
            "taker_coin": "DGB-segwit",
            "maker_coin": "KMD-BEP20",
            "uuid": "33333333-fd33-4dc4-2a7f-f6320b1d3b64",
            "started_at": time_obj.hours_ago(1) + 5,
            "finished_at": time_obj.hours_ago(1) + 60,
            "taker_amount": 500,
            "maker_amount": 0.9,
            "is_success": 1,
            "taker_coin_ticker": "DGB",
            "taker_coin_platform": "segwit",
            "maker_coin_ticker": "KMD",
            "maker_coin_platform": "BEP20",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "2.0.0-beta_b0fd99e",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 0.0018,
            "reverse_price": 555.55555556,
            "trade_type": "buy",
            "pair": "KMD-BEP20_DGB-segwit",
            "pair_reverse": "DGB-segwit_KMD-BEP20",
            "pair_std": "KMD_DGB",
            "pair_std_reverse": "DGB_KMD",
            "last_updated": "",
        },
        {
            "taker_coin": "DGB",
            "maker_coin": "LTC",
            "uuid": "55555555-ee4b-494f-a2fb-48467614b613",
            "started_at": time_obj.hours_ago(1),
            "finished_at": time_obj.hours_ago(1) + 4,
            "taker_amount": 1,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "DGB",
            "taker_coin_platform": "",
            "maker_coin_ticker": "LTC",
            "maker_coin_platform": "",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 1.0,
            "reverse_price": 1.0,
            "trade_type": "sell",
            "pair": "DGB_LTC",
            "pair_reverse": "LTC_DGB",
            "pair_std": "DGB_LTC",
            "pair_std_reverse": "LTC_DGB",
            "last_updated": "",
        },
        {
            "taker_coin": "KMD",
            "maker_coin": "LTC-segwit",
            "uuid": "666666666-75a2-d4ef-009d-5e9baad162ef",
            "started_at": time_obj.hours_ago(1),
            "finished_at": time_obj.hours_ago(1) + 10,
            "taker_amount": 100,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "KMD",
            "taker_coin_platform": "",
            "maker_coin_ticker": "LTC",
            "maker_coin_platform": "segwit",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 100.0,
            "reverse_price": 0.01,
            "trade_type": "sell",
            "pair": "KMD_LTC-segwit",
            "pair_reverse": "LTC-segwit_KMD",
            "pair_std": "KMD_LTC",
            "pair_std_reverse": "LTC_KMD",
            "last_updated": "",
        },
        {
            "taker_coin": "LTC-segwit",
            "maker_coin": "KMD",
            "uuid": "77777777-2762-4633-8add-6ad2e9b1a4e7",
            "started_at": time_obj.hours_ago(2),
            "finished_at": time_obj.hours_ago(2) + 6,
            "taker_amount": 1,
            "maker_amount": 100,
            "is_success": 1,
            "taker_coin_ticker": "LTC",
            "taker_coin_platform": "segwit",
            "maker_coin_ticker": "KMD",
            "maker_coin_platform": "",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 100.0,
            "reverse_price": 0.01,
            "trade_type": "buy",
            "pair": "KMD_LTC-segwit",
            "pair_reverse": "LTC-segwit_KMD",
            "pair_std": "KMD_LTC",
            "pair_std_reverse": "LTC_KMD",
            "last_updated": "",
        },
        {
            "taker_coin": "KMD",
            "maker_coin": "BTC",
            "uuid": "888888888-7622-6334-add8-9b1a4e76ad2e",
            "started_at": time_obj.hours_ago(3),
            "finished_at": time_obj.hours_ago(3) + 7,
            "taker_amount": 1000000,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "KMD",
            "taker_coin_platform": "",
            "maker_coin_ticker": "BTC",
            "maker_coin_platform": "",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 1000000.0,
            "reverse_price": 1e-06,
            "trade_type": "sell",
            "pair": "KMD_BTC",
            "pair_reverse": "BTC_KMD",
            "pair_std": "KMD_BTC",
            "pair_std_reverse": "BTC_KMD",
            "last_updated": "",
        },
        {
            "taker_coin": "LTC",
            "maker_coin": "KMD",
            "uuid": "999999999-73a2-d46d-900d-aad5e9b162ef",
            "started_at": time_obj.hours_ago(4),
            "finished_at": time_obj.hours_ago(4) + 8,
            "taker_amount": 2,
            "maker_amount": 200,
            "is_success": 1,
            "taker_coin_ticker": "LTC",
            "taker_coin_platform": "",
            "maker_coin_ticker": "KMD",
            "maker_coin_platform": "",
            "taker_gui": "Komodo Wallet 0.7.1-beta",
            "maker_gui": "Komodo Wallet 0.7.1-beta",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 100.0,
            "reverse_price": 0.01,
            "trade_type": "buy",
            "pair": "KMD_LTC",
            "pair_reverse": "LTC_KMD",
            "pair_std": "KMD_LTC",
            "pair_std_reverse": "LTC_KMD",
            "last_updated": "",
        },
        {
            "taker_coin": "KMD-BEP20",
            "maker_coin": "BTC",
            "uuid": "AAAAAAAA-273f-40a5-bcd4-31efdb6bcc8b",
            "started_at": time_obj.days_ago(1) - 900,
            "finished_at": time_obj.days_ago(1) - 300,
            "taker_amount": 2000000,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "KMD",
            "taker_coin_platform": "BEP20",
            "maker_coin_ticker": "BTC",
            "maker_coin_platform": "",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 2000000.0,
            "reverse_price": 5e-07,
            "trade_type": "sell",
            "pair": "KMD-BEP20_BTC",
            "pair_reverse": "BTC_KMD-BEP20",
            "pair_std": "KMD_BTC",
            "pair_std_reverse": "BTC_KMD",
            "last_updated": "",
        },
        {
            "taker_coin": "BTC",
            "maker_coin": "LTC",
            "uuid": "BBBBBBBB-ac6f-4649-b420-5eb8e2924bf2",
            "started_at": time_obj.days_ago(7) - 900,
            "finished_at": time_obj.days_ago(7) + 10,
            "taker_amount": 5,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "BTC",
            "taker_coin_platform": "",
            "maker_coin_ticker": "LTC",
            "maker_coin_platform": "",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 0.2,
            "reverse_price": 5.0,
            "trade_type": "buy",
            "pair": "LTC_BTC",
            "pair_reverse": "BTC_LTC",
            "pair_std": "LTC_BTC",
            "pair_std_reverse": "BTC_LTC",
            "last_updated": "",
        },
        {
            "taker_coin": "DGB",
            "maker_coin": "LTC-segwit",
            "uuid": "CCCCCCCC-40a5-4649-b420-5eb8e2924bf2",
            "started_at": time_obj.days_ago(7) - 900,
            "finished_at": time_obj.days_ago(7) - 11,
            "taker_amount": 100000,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "DGB",
            "taker_coin_platform": "",
            "maker_coin_ticker": "LTC",
            "maker_coin_platform": "segwit",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 100000.0,
            "reverse_price": 1e-05,
            "trade_type": "sell",
            "pair": "DGB_LTC-segwit",
            "pair_reverse": "LTC-segwit_DGB",
            "pair_std": "DGB_LTC",
            "pair_std_reverse": "LTC_DGB",
            "last_updated": "",
        },
        {
            "taker_coin": "DGB-segwit",
            "maker_coin": "LTC",
            "uuid": "DDDDDDDD-ac6f-a2fb-b360-4bf25fed4292",
            "started_at": time_obj.days_ago(30) - 900,
            "finished_at": time_obj.days_ago(30) + 12,
            "taker_amount": 200000,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "DGB",
            "taker_coin_platform": "segwit",
            "maker_coin_ticker": "LTC",
            "maker_coin_platform": "",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 200000.0,
            "reverse_price": 5e-06,
            "trade_type": "sell",
            "pair": "DGB-segwit_LTC",
            "pair_reverse": "LTC_DGB-segwit",
            "pair_std": "DGB_LTC",
            "pair_std_reverse": "LTC_DGB",
            "last_updated": "",
        },
        {
            "taker_coin": "LTC",
            "maker_coin": "DOGE",
            "uuid": "EEEEEEEE-ee4b-494f-a2fb-48467614b613",
            "started_at": time_obj.days_ago(60) - 900,
            "finished_at": time_obj.days_ago(60) + 13,
            "taker_amount": 10,
            "maker_amount": 1,
            "is_success": 1,
            "taker_coin_ticker": "LTC",
            "taker_coin_platform": "",
            "maker_coin_ticker": "DOGE",
            "maker_coin_platform": "",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 10.0,
            "reverse_price": 0.1,
            "trade_type": "sell",
            "pair": "LTC_DOGE",
            "pair_reverse": "DOGE_LTC",
            "pair_std": "LTC_DOGE",
            "pair_std_reverse": "DOGE_LTC",
            "last_updated": "",
        },
        {
            "taker_coin": "DOGE",
            "maker_coin": "LTC",
            "uuid": "FFFFFFFF-ee4b-494f-a2fb-48467614b613",
            "started_at": time_obj.weeks_ago(10) - 900,
            "finished_at": time_obj.weeks_ago(10) + 10,
            "taker_amount": 1,
            "maker_amount": 10,
            "is_success": 1,
            "taker_coin_ticker": "DOGE",
            "taker_coin_platform": "",
            "maker_coin_ticker": "LTC",
            "maker_coin_platform": "",
            "taker_gui": "",
            "maker_gui": "",
            "taker_pubkey": "",
            "maker_pubkey": "",
            "taker_version": "",
            "maker_version": "",
            "taker_coin_usd_price": 0,
            "maker_coin_usd_price": 0,
            "price": 10.0,
            "reverse_price": 0.1,
            "trade_type": "buy",
            "pair": "LTC_DOGE",
            "pair_reverse": "DOGE_LTC",
            "pair_std": "LTC_DOGE",
            "pair_std_reverse": "DOGE_LTC",
            "last_updated": "",
        },
    ]

    with Session(engine) as session:
        sample_data = db.SqlSource().normalise_swap_data(sample_data, gecko_source)
        sample_data = clean.decimal_dict_lists(sample_data)

        for i in sample_data:
            data = db.DefiSwapTest(
                uuid=i["uuid"],
                taker_coin=i["taker_coin"],
                taker_gui=i["taker_gui"],
                taker_pubkey=i["taker_pubkey"],
                taker_version=i["taker_version"],
                maker_coin=i["maker_coin"],
                maker_gui=i["maker_gui"],
                maker_pubkey=i["maker_pubkey"],
                maker_version=i["maker_version"],
                maker_coin_platform=i["maker_coin_platform"],
                maker_coin_ticker=i["maker_coin_ticker"],
                taker_coin_platform=i["taker_coin_platform"],
                taker_coin_ticker=i["taker_coin_ticker"],
                taker_amount=i["taker_amount"],
                maker_amount=i["maker_amount"],
                started_at=i["started_at"],
                finished_at=i["finished_at"],
                is_success=i["is_success"],
                # Not in Cipi's DB, but derived from taker/maker amounts.
                price=i["price"],
                reverse_price=i["reverse_price"],
                # Not in Cipi's DB
                maker_coin_usd_price=i["maker_coin_usd_price"],
                taker_coin_usd_price=i["taker_coin_usd_price"],
                # Extra columns
                trade_type=i["trade_type"],
                pair=i["pair"],
                pair_reverse=i["pair_reverse"],
                pair_std=i["pair_std"],
                pair_std_reverse=i["pair_std_reverse"],
                last_updated=i["last_updated"],
            )
            if isinstance(data.finished_at, int) and isinstance(data.started_at, int):
                data.duration = data.finished_at - data.started_at
            else:
                data.duration = -1
            session.add(data)
        session.commit()

    logger.info(f"{TEST_DB_NAME} ready")
    yield pg_query
