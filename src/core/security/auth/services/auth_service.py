import os

from fastapi.encoders import jsonable_encoder

from src.app.middlewares.token import Token
from ..schemas.auth import AuthenticationModel, ResponseLogin
from src.app.gateway.active_directory import autenticate_user

import bcrypt

class AuthService():
    def __init__(self, token: Token, db):
        self.token = token
        self.db = db
    
    async def login(self, data: AuthenticationModel) -> ResponseLogin:
        result = await autenticate_user(data.usuario)
        return await self._validation_response(result, data)
    
    async def _validation_response(self, result_authentication, data: AuthenticationModel):
        if result_authentication.get('error'):
            return {"error": True, "message": "No se ha encontrado el usuario debido a un error con la BDD"}
        if not result_authentication["userFound"]:
            return {"userFound": False, "message": "Usuario no encontrado dentro de los registros, por favor revise el usuario y contraseña"}

        user = result_authentication['user']
        
        if not bcrypt.checkpw(data.password.encode('utf-8'), user.password):
            return {"userFound": False, "message": "Credenciales invalidas, por favor revise el usuario y contraseña"}

        secret = os.getenv("SECRET_KEY")
        token = await self.token.encode(jsonable_encoder(user), secret=secret)
        return {"result": {"token": token, "user": user}, "userFound": True}