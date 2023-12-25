#!/usr/bin/env python3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import time
from util.logger import logger
from lib.models import FixerRates, ErrorMessage
from lib.cache import Cache

router = APIRouter()
cache = Cache()


@router.get(
    "/fixer_io",
    description="Get usd fiat rates from data.fixer.io",
    responses={406: {"model": ErrorMessage}},
    response_model=FixerRates,
    status_code=200,
)
def get_fixer_rates():
    try:
        data = cache.load_fixer_rates()
        if "timestamp" not in data:
            raise ValueError("No timestamp in data!")
        elif data["timestamp"] < time.time() - 900:
            raise ValueError("Data expired! No updates for > 15 mins.")
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except Exception as e:  # pragma: no cover
        err = {"error": f"Error in [/api/v3/rates/fixer_io]: {e}"}
        logger.warning(err)
        return JSONResponse(status_code=406, content=err)
