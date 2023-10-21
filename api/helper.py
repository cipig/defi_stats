#!/usr/bin/env python3
from decimal import Decimal
from fastapi import HTTPException


def format_10f(number: float) -> str:
    '''
    Format a float to 10 decimal places.
    '''
    return f"{number:.10f}"


def list_json_key(data: dict, key: str, filter_value: str) -> Decimal:
    '''
    list of key values from dicts.
    '''
    return [i for i in data if i[key] == filter_value]


def sum_json_key(data: dict, key: str) -> Decimal:
    '''
    Sum a key from a list of dicts.
    '''
    return sum(Decimal(d[key]) for d in data)


def sum_json_key_10f(data: dict, key: str) -> str:
    '''
    Sum a key from a list of dicts and format to 10 decimal places.
    '''
    return format_10f(sum_json_key(data, key))


def sort_dict_list(data: dict, key: str, reverse=False) -> dict:
    '''
    Sort a list of dicts by the value of a key.
    '''
    return sorted(data, key=lambda k: k[key], reverse=reverse)


def validate_ticker(ticker_id: str):
    if len(ticker_id) > 32:
        raise HTTPException(
            status_code=400,
            detail="Pair cant be longer than 32 symbols"
        )
    elif len(ticker_id.split("_")) != 2:
        raise HTTPException(
            status_code=400,
            detail="Pair should be in format BASE_TARGET"
        )


def set_pair_as_tuple(pair):
    if isinstance(pair, list):
        pair = tuple(pair)
    if isinstance(pair, str):
        pair = tuple(map(str, pair.split("_")))
    if not isinstance(pair, tuple):
        raise TypeError("Pair should be a string, tuple or list")
    if len(pair) != 2:
        raise ValueError("Pair tuple should have two values only")
    return pair


def order_pair_by_market_cap(pair, gecko_source):
    if pair[0] in gecko_source:
        if pair[1] in gecko_source:
            if (
                gecko_source[pair[1]]["usd_market_cap"]
                < gecko_source[pair[0]]["usd_market_cap"]
            ):
                pair = (pair[1], pair[0])
        else:
            pair = (pair[1], pair[0])
    return pair
