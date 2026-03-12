import os
from fastapi.security import HTTPBearer
from fastapi import HTTPException, Request
from src.app.middlewares.token import Token

class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request) -> dict:
        auth = await super().__call__(request)
        config = Token()
        secret = os.getenv("SECRET_KEY")
        data = config.validate_token(auth.credentials, secret=secret)
        if "error" in data: 
            raise HTTPException(status_code=403, detail={"message": "Invalid Credentials", "code": "403"})
        if "credentials" not in data:
            data["credentials"] = auth.credentials
        return data