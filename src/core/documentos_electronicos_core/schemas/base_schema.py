from pydantic import BaseModel
from typing import  Optional

class ConsultaDocumento(BaseModel):
    claveAcceso:                        str

class InfoTributaria(BaseModel):
    ambiente:                           str
    tipoEmision:                        str
    claveAcceso:                        Optional[str] = None
    razonSocial:                        Optional[str] = None
    nombreComercial:                    Optional[str] = None
    ruc:                                Optional[str] = None
    codDoc:                             str
    estab:                              str
    ptoEmi:                             str
    secuencial:                         str
    dirMatriz:                          str
    diaEmission:                        str
    mesEmission:                        str
    anioEmission:                       str

class TotalConImpuesto(BaseModel):
    codigo:                             str
    codigoPorcentaje:                   str
    baseImponible:                      str
    valor:                              str

class Pago(BaseModel):
    formaPago:                          str
    total:                              str
    plazo:                              Optional[str] = None
    unidadTiempo:                       Optional[str] = None

class DetallesAdicionales(BaseModel):
    nombre:                             str
    valor:                              str

class Impuesto(TotalConImpuesto):
    tarifa:                              str

class Detalle(BaseModel):
    codigoPrincipal:                    str
    codigoAuxiliar:                     Optional[str] = None
    descripcion:                        str
    cantidad:                           int
    precioUnitario:                     str
    descuento:                          str
    precioTotalSinImpuesto:             str
    detallesAdicionales:                Optional[list[DetallesAdicionales]] = None
    impuestos:                          list[Impuesto]

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