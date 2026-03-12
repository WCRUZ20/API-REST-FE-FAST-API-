from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials

from src.core.security.auth.schemas.auth import AuthenticationModel
from src.app.controllers.auth_controller import AuthController
from src.app.middlewares.jwt_bearer import JWTBearer
from src.app.middlewares.token import Token

import os

tiempo_sesion = int(os.getenv("IDLE_TIME","15"))

auth_route = APIRouter()

TAG="Auth"
jwt_bearer = JWTBearer()

@auth_route.post("/login",tags=[TAG], response_model=dict)
async def auth(user:AuthenticationModel) -> dict:
    obj_controller = AuthController()
    result = await obj_controller.login(user)
    if result.get('error'):
        raise HTTPException(status_code=404, detail=result['message'])
    if result["userFound"] == False:
        raise HTTPException(status_code=404, detail=result["message"])

    return JSONResponse(content=jsonable_encoder(result["result"]), status_code=200)

@auth_route.post("/renew-token",tags=["Auth"], response_model=dict)
async def renew_token(credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer)):
    token = credentials['credentials']
    secret = os.getenv("SECRET_KEY")
    token_service = Token()
    data = token_service.validate_token(token, secret)
    if "error" in data:
        raise HTTPException(status_code=403, detail='Invalid Credentials')
    new_token = await token_service.encode(data, secret, expires_in=tiempo_sesion)
    return {"access_token": new_token}