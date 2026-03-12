from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise

from src.routers.routes import router

import os
import logging

load_dotenv(override=True)

# Configurar el sistema de logging
logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  
    handlers=[
        #logging.FileHandler("app.log"),  
        logging.StreamHandler()  
    ]
)

# Silenciar logs verbosos de fontTools
logging.getLogger("fontTools.subset").setLevel(logging.ERROR)

#Crear instancia de FASTApi
app = FastAPI(
    title="SOLSAP API",
    version="1.0.0",
    description="API de facturación electrónica para uso en SAP Business One (SAP BO) y SAP Customer Checkout (SAP CCO)."
)

#CORS
origins = [
    os.getenv("URL_LOCAL"),
    os.getenv("URL_PROD")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#Configuracion de Tortoise
async def init():
    try:
        await Tortoise.init(
            db_url=os.getenv("DATABASE_URL"),
            modules={'models': ['src.app.models.model']}  
        )
        logging.info("Conexión de BD exitosa.")
    except Exception as e:
        logging.error(f"Error inicializando Tortoise ORM: {e}")
    finally:
        await Tortoise.close_connections()

@app.on_event("startup")
async def startup_event():
    await init()

@app.get("/solsap", tags=["init server"], response_model=dict)
async def root():
    return {"status": 200, "message": "server is running"}

#Incluir otras rutas
app.include_router(router, prefix="/solsap/api/v1")