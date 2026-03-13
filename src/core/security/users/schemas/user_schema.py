from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

from ...auth.schemas.auth import AuthenticationModel

class UserCreateModel(AuthenticationModel):
    email:                      str
    full_name:                  str
    profile_id:                 int
    identificacion:             str

class UserCreateResponseModel(UserCreateModel):
    created_by_name:            str
    created:                    datetime

class DatosFacturacionRegisterModel(BaseModel):
    usuario:                    int
    ruc:                        str
    razon_social:               str
    nombre_comercial:           Optional[str] = None
    direccion:                  str
    telefono:                   Optional[str] = None
    obligado_contabilidad:      Literal["SI", "NO"]
    nombre_firma:               Optional[str] = None
    password_sign:              Optional[str] = None
    ruta_logo:                  Optional[str] = None

class UserUpdateModel(BaseModel):
    usuario:                    Optional[str] = None
    password:                   Optional[str] = None
    email:                      Optional[str] = None
    full_name:                  Optional[str] = None
    identificacion:             Optional[str] = None
    profile_id:                 Optional[int] = None
    active:                     Optional[bool] = None


class DatosFacturacionUpdateModel(BaseModel):
    ruc:                        Optional[str] = None
    razon_social:               Optional[str] = None
    nombre_comercial:           Optional[str] = None
    direccion:                  Optional[str] = None
    telefono:                   Optional[str] = None
    obligado_contabilidad:      Optional[Literal["SI", "NO"]] = None
    nombre_firma:               Optional[str] = None
    password_sign:              Optional[str] = None
    ruta_logo:                  Optional[str] = None