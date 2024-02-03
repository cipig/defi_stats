#!/usr/bin/env python3
import pytest
from lib.external import CoinGeckoAPI
from util.files import Files
from util.urls import Urls
from lib.markets import Markets
from lib.cache import Cache, CacheItem
from lib.stats_api import StatsAPI
import util.helper as helper


@pytest.fixture
def setup_statsapi():
    yield StatsAPI()


@pytest.fixture
def setup_markets():
    yield Markets()


@pytest.fixture
def setup_cache_item():
    yield CacheItem()


@pytest.fixture
def setup_last_traded_cache():
    yield CacheItem("generic_last_traded").data


@pytest.fixture
def setup_files():
    yield Files()


@pytest.fixture
def setup_urls():
    yield Urls()


@pytest.fixture
def setup_cache():
    yield Cache()


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


@pytest.fixture
def setup_helper():
    yield helper
