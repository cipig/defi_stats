import util.memcache as memcache
from lib.cache import Cache


def test_cache():
    cache = Cache()

    for i in [
        "coin_volumes_24hr",
        "pair_last_traded",
        "pair_last_traded_24hr",
        "pair_prices_24hr",
        "pair_volumes_24hr",
        "pair_volumes_14d",
        "gecko_pairs",
        "pair_orderbook_extended",
        "markets_summary",
        "stats_api_summary",
        "adex_24hr",
        "adex_fortnite",
        "prices_tickers_v1",
        "prices_tickers_v2",
        "tickers",
    ]:
        cache_item = cache.get_item(i)
        data = cache_item.save()
        assert "error" not in data
