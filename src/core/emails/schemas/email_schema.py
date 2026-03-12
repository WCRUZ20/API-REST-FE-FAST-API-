from pydantic import BaseModel
from typing import Optional 

class EmailData(BaseModel):
    nombre_usuario:     Optional[str]
    usuario:            Optional[str]
    contrasenia:        Optional[str]
    email_receptor:     str
    subject:            str
    identificacion:     str