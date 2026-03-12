from pydantic import BaseModel
from typing import  List, Optional

class CertificadoFirma(BaseModel):
    nombre_firma:       str
    password_firma:     str
