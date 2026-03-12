from pydantic import BaseModel, field_validator, Field, model_validator
from typing import List, Optional, Literal
from .base_schema import InfoTributaria, DetallesAdicionales, Impuesto, Pago, Detalle, TotalConImpuesto
from datetime import datetime

class InfoNotaDebito(BaseModel):
    fechaEmision:                   str                     = Field(..., description="Fecha de emision en formato dd/mm/yyyy")
    dirEstablecimiento:             Optional[str]           = None
    tipoIdentificacionComprador:    Optional[str]
    razonSocialComprador:           str
    identificacionComprador:        str
    contribuyenteEspecial:          Optional[str]           = None
    obligadoContabilidad:           Optional[str]           = Field(..., description="Es obligado a llevar contabilidad? SI/NO")
    codDocModificado:               str
    numDocModificado:               str
    fechaEmisionDocSustento:        str
    totalSinImpuestos:              str
    impuestos:                      List[Impuesto]
    valorTotal:                     str
    pagos:                          List[Pago]

    @field_validator("obligadoContabilidad")
    @classmethod
    def validar_obligado_contabilidad(cls, v):
        if v not in {"SI", "NO"}:
            raise ValueError("El valor de 'obligadoContabilidad' debe ser 'SI' o 'NO'")
        return v

    @field_validator("fechaEmision")
    @classmethod
    def validar_fecha(cls, v):
        try:
            datetime.strptime(v, "%d/%m/%Y")
        except ValueError:
            raise ValueError("La 'fechaEmision' debe tener el formato dd/mm/yyyy")
        return v

class Motivo(BaseModel):
    razon:                              str
    valor:                              str

class NotaDebito(BaseModel):
    infoTributaria:                     InfoTributaria
    infoNotaDebito:                     InfoNotaDebito
    motivos:                            List[Motivo]
    infoAdicional:                      List[DetallesAdicionales]
    campoAdicional1:                    Optional[str] = Field(None, description="Campo para enviar el nombre del logo con extensión (ejemplo: logo.png)")
    campoAdicional2:                    Optional[str] = Field(None, description="Campo para enviar información adicional 2")