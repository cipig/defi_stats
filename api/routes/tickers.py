#!/usr/bin/env python3
from fastapi import APIRouter
from util.logger import logger
from models.tickers import TickersSummary
from models.generic import ErrorMessage
from lib.cache import Cache
from util.transform import deplatform
import util.transform as transform
import util.memcache as memcache


router = APIRouter()
cache = Cache()


@router.get(
    "/summary",
    description="24-hour price & volume for each standard market pair traded in last 7 days.",
    responses={406: {"model": ErrorMessage}},
    response_model=TickersSummary,
    status_code=200,
)
def summary():
    try:
        tickers = {}
        tickers_data = deplatform.tickers(memcache.get_tickers())
        for i in tickers_data["data"]:
            tickers.update({i['ticker_id']: transform.ticker_to_gecko_summary(i)})
        tickers_data.update({"data": tickers})
        
        return tickers_data
    except Exception as e:  # pragma: no cover
        logger.warning(f"{type(e)} Error in [/api/v3/tickers/summary]: {e}")
        return {"error": f"{type(e)} Error in [/api/v3/tickers/summary]: {e}"}
