from pydantic import BaseModel, field_validator, Field, model_validator
from datetime import datetime
from typing import  List, Optional
from .base_schema import InfoTributaria, TotalConImpuesto, Pago, DetallesAdicionales, Impuesto

class InfoNotaCredito(BaseModel):
    fechaEmision:                       str                                     =   Field(..., description="Fecha de emision en formato dd/mm/yyyy")
    dirEstablecimiento:                 str
    tipoIdentificacionComprador:        str
    razonSocialComprador:               str
    identificacionComprador:            str
    contribuyenteEspecial:              Optional[str]                           = None
    obligadoContabilidad:               Optional[str]                           = None
    rise:                               Optional[str]                           = None
    codDocModificado:                   str
    numDocModificado:                   str
    fechaEmisionDocSustento:            str                                     = Field(..., description="Fecha de emision documento sustento en formato dd/mm/yyyy")
    totalSinImpuestos:                  str
    valorModificacion:                  str
    moneda:                             Optional[str]                           = None
    totalConImpuestos:                  List[TotalConImpuesto]
    motivo:                             str

    @field_validator('fechaEmision')
    @classmethod
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Fecha debe estar en formato dd/mm/yyyy")
        return value

class Detalle(BaseModel):
    codigoInterno:                      Optional[str]                           = None
    codigoAdicional:                    Optional[str]                           = None
    descripcion:                        str
    cantidad:                           str
    precioUnitario:                     str
    descuento:                          str
    precioTotalSinImpuesto:             str
    detallesAdicionales:                Optional[List[DetallesAdicionales]]     = None
    impuestos:                          List[Impuesto]


class NotaCredito(BaseModel):
    infoTributaria:                     InfoTributaria
    infoNotaCredito:                    InfoNotaCredito
    detalles:                           List[Detalle]
    infoAdicional:                      Optional[List[DetallesAdicionales]]     = None
    campoAdicional1:                    Optional[str] = Field(None, description="Campo para enviar el nombre del logo con extensión (ejemplo: logo.png)")
    campoAdicional2:                    Optional[str] = Field(None, description="Campo para enviar información adicional 2")

class InfoToSignXml:
    def __init__(
            self,
            pathXmlToSign: str,
            pathXmlSigned: str,
            pathSignatureP12: str,
            passwordSignature: str
    ):
        self.pathXmlToSign = pathXmlToSign
        self.pathXmlSigned = pathXmlSigned
        self.passwordSignature = passwordSignature
        self.pathSignatureP12 = pathSignatureP12