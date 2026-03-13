import logging
import os
import subprocess

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.encoders import jsonable_encoder
from typing import Literal, Optional
from fastapi.responses import JSONResponse
from ..app.controllers.security.user_controller import UserController
from ..core.security.users.schemas.user_schema import UserCreateModel, DatosFacturacionRegisterModel
from ..core.security.users.exceptions.user_exception import UserExistsException, DataFacturacionExistsException
from ..core.security.profiles.exceptions.profile_exception import UnAuthorizedException
from ..app.middlewares.jwt_bearer import JWTBearer

user_router = APIRouter()
jwt_bearer = JWTBearer()

TAG = "security_user"
UPLOAD_FOLDER = "src/assets/"

# Asegurarse de que la carpeta exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@user_router.post("/", tags=[TAG], response_model=dict)
async def createUser(userCreate: UserCreateModel, user: dict = Depends(jwt_bearer)) -> dict:
    try:
        auth_controller = UserController()
        result = await auth_controller.create_user(userCreate, user)
        if result.get('error'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        return result
    except UserExistsException as e:
        logging.error(e)
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@user_router.post("/data_factura")
async def fomulario_datos_facturas(usuario: int = Form(...),
                                   ruc: str = Form(...),
                                   razon_social: str = Form(...),
                                   nombre_comercial: Optional[str] = Form(None),
                                   direccion: str = Form(...),
                                   obligado_contabilidad: Literal["SI", "NO"] = Form(...),
                                   password_sign: Optional[str] = Form(None),
                                   ruta_logo: Optional[UploadFile] = File(None), 
                                   telefono: Optional[str] = Form(None), 
                                   firma: UploadFile = File(...), user: dict = Depends(jwt_bearer)):
    try:
        if not firma.filename.endswith(".p12"):
            return {"error": "El archivo de firma debe tener la extensión .p12"}
    
        firma_path = os.path.join(UPLOAD_FOLDER + "firmasElectronicas", firma.filename)
        with open(firma_path, "wb") as buffer:
            buffer.write(await firma.read())

        name_sign = firma.filename.split('.')[0]
        
        if ruta_logo:
            if not ruta_logo.filename.endswith(".png") and not ruta_logo.filename.endswith(".jpg"):
                return {"error": "El archivo de ruta_logo debe tener la extensión .jpg o .png"}
            
            ruta_logo_path = os.path.join(UPLOAD_FOLDER + "imgs", ruc)
            if not os.path.exists(ruta_logo_path):
                os.makedirs(ruta_logo_path)
            logo_path = os.path.join(ruta_logo_path, ruta_logo.filename)
            with open(logo_path, "wb") as buffer:
                buffer.write(await ruta_logo.read())

        datos_facturacion = DatosFacturacionRegisterModel(
            usuario=usuario,
            ruc=ruc,
            razon_social=razon_social,
            nombre_comercial=nombre_comercial,
            direccion=direccion,
            obligado_contabilidad=obligado_contabilidad,
            nombre_firma=name_sign,
            password_sign=password_sign,
            telefono= telefono,
            ruta_logo=ruta_logo.filename if ruta_logo else None
        )
        
        user_controller = UserController()
        result = await user_controller.create_data_factura(datos_facturacion, user)
        
        return JSONResponse(content=jsonable_encoder(result), status_code=200)
    except DataFacturacionExistsException as e:
        raise HTTPException(status_code=500, detail={"message": e.detail})
    except UserExistsException as e:
        raise HTTPException(status_code=500, detail={"message": e.detail})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@user_router.get("/", tags=[TAG], response_model=dict)
async def getUsers(user: dict = Depends(jwt_bearer)) -> dict:
    try:
        user_controller = UserController()
        return await user_controller.get_users(user)
    except UnAuthorizedException as e:
        raise HTTPException(status_code=403, detail={"message": e.detail})
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

""" @user_router.post("/", tags=[TAG], response_model=dict)
async def createUser(userCreate: UserCreateModel) -> dict:
    try:
        auth_controller = UserController()
        result = await auth_controller.create_user(userCreate)
        if result.get('error'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        return result
    except UserExistsException as e:
        logging.error(e)
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Internal Server Error") """