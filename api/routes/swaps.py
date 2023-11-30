#!/usr/bin/env python3
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from const import MM2_DB_PATH_7777
from logger import logger
from models import ErrorMessage, GeckoSwapItem
from generics import UuidNotFoundException
from db import SqliteDB

router = APIRouter()


@router.get(
    '/swap/{uuid}',
    description="Get swap info from a uuid.",
    responses={406: {"model": ErrorMessage}},
    response_model=GeckoSwapItem,
    status_code=200
)
def get_swap(uuid: str):
    try:
        sqliteDB = SqliteDB(path_to_db=MM2_DB_PATH_7777)
        resp = sqliteDB.get_swap(uuid)
        if "error" in resp:
            raise UuidNotFoundException(resp["error"])
        return sqliteDB.get_swap(uuid)
    except Exception as e:
        err = {"error": f"{e}"}
        logger.warning(err)
        return JSONResponse(status_code=406, content=err)
