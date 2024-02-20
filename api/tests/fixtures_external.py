#!/usr/bin/env python3
import pytest
from lib.external import CoinGeckoAPI


@pytest.fixture
def setup_gecko():
    yield CoinGeckoAPI()


@pytest.fixture
def setup_gecko_coin_ids(setup_gecko):
    gecko = setup_gecko
    yield gecko.get_gecko_coin_ids()


@pytest.fixture
def setup_gecko_info(setup_gecko):
    gecko = setup_gecko
    yield gecko.get_gecko_info()
