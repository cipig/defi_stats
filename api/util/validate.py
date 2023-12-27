from decimal import Decimal
from util.logger import logger
from util.helper import get_valid_coins
from util.exceptions import CoinNotFoundException, CoinWalletOnlyException


def validate_ticker_id(ticker_id, valid_tickers, allow_reverse=False, allow_fail=False):
    if allow_reverse:
        inverse_valid_tickers = [
            f'{i.split("_")[1]}_{i.split("_")[0]}' for i in valid_tickers
        ]
        if ticker_id in inverse_valid_tickers:
            return "reversed"

    if ticker_id in valid_tickers:
        return "standard"

    msg = f"ticker_id '{ticker_id}' not in available pairs."
    msg += " Check the /api/v3/gecko/pairs endpoint for valid values."
    if allow_fail:
        return "failed"
    raise ValueError(msg)


def validate_coin(coin, coins_config):
    if coin not in get_valid_coins(coins_config):
        raise CoinNotFoundException(f"{coin} is not in coins_config.json!")
    if coin not in get_valid_coins(coins_config):
        raise CoinWalletOnlyException(f"{coin} is wallet_only!")


def validate_positive_numeric(value, name, is_int=False):
    try:
        if Decimal(value) < 0:
            raise ValueError(f"{name} can not be negative!")
        if is_int and Decimal(value) % 1 != 0:
            raise ValueError(f"{name} must be an integer!")
    except Exception as e:
        logger.warning(f"{type(e)} Error validating {name}: {e}")
        raise ValueError(f"{name} must be numeric!")
