import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from tortoise import Tortoise

from src import *

db_router = APIRouter()

@db_router.get("/schema/generate", tags=["Schemas"], response_model=dict)
async def generate_schema():
    try: 
        await Tortoise.generate_schemas()
        return JSONResponse(content=jsonable_encoder({"message:": "esquemas y tablas generados exitosamente"}), status_code=200)
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail={"message": f"Error al crear los esquemas y tablas con Tortoise ORM"})