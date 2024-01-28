import util.cron as cron
import pytest
from decimal import Decimal
from util.logger import logger
from tests.fixtures_data import swap_item
from tests.fixtures_db import setup_swaps_db_data, setup_time
from util.helper import (
    get_mm2_rpc_port,
    get_chunks,
    get_price_at_finish,
)
from const import MM2_DB_PATH_7777, MM2_DB_PATH_8762, MM2_DB_PATH_ALL
from lib.markets import Markets


def test_tickers():
    # markets = Markets()
    pass
