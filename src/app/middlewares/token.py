import jwt

from fastapi.security import OAuth2PasswordBearer
import os
from datetime import datetime, timedelta

class Token():

    tiempo_sesion = int(os.getenv("IDLE_TIME", "15"))
    async def encode(self, data: dict, secret, expires_in: int = tiempo_sesion):
        payload = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_in)
        payload.update({"exp":expire})
        return jwt.encode(
            payload=payload,
            key=secret,
            algorithm="HS256"
        )
    
    def validate_token(self, token: str, secret) -> dict:
        try:
            data: dict = jwt.decode(token, key=secret, algorithms=["HS256"])
            return data
        except jwt.ExpiredSignatureError:
            return {"error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}
    
oaut2_scheme = OAuth2PasswordBearer(tokenUrl="token")