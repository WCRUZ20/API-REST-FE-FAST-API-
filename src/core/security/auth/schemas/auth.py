from pydantic import BaseModel
from datetime import datetime

class AuthenticationModel(BaseModel):
    password:                   str
    usuario:                    str

class ResponseLogin():
    token:                      str
