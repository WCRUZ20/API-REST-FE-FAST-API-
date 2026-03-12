from src.core.security.auth.services.auth_service import AuthService
from tortoise import Tortoise
from src.app.middlewares.token import Token
from src.core.security.auth.schemas.auth import AuthenticationModel, ResponseLogin
from src.app.db.connection_enum import ConnectionName

class AuthController():

    def __init__(self):
        self.db = Tortoise.get_connection(ConnectionName.DEFAULT.value)
        self.obj_token = Token()
    
    async def login(self, user: AuthenticationModel) -> ResponseLogin:
        return await AuthService(self.obj_token, self.db).login(user)