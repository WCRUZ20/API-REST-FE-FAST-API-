from pydantic import BaseModel, field_validator, Field, model_validator
from typing import List, Optional
from datetime import datetime
from .base_schema import InfoTributaria, DetallesAdicionales, TotalConImpuesto, Pago

class InofoGuiaRemision(BaseModel):
    dirEstablecimiento:                                 Optional[str] = None
    dirPartida:                                         str
    razonSocialTransportista:                           str
    tipoIdentificacionTransportista:                    Optional[str] = None
    rucTransportista:                                   str
    rise:                                               Optional[str] = None
    obligadoContabilidad:                               Optional[str] = None
    contribuyenteEspecial:                              Optional[str] = None
    fechaIniTransporte:                                 str = Field(..., description="Fecha de inicio del transporte en formato dd/mm/yyyy")
    fechaFinTransporte:                                 str = Field(..., description="Fecha de fin del transporte en formato dd/mm/yyyy")
    placa:                                              str

    @field_validator('fechaIniTransporte', 'fechaFinTransporte')
    @classmethod
    def validar_fecha(cls, value):
        try:
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Fecha debe estar en formato dd/mm/yyyy")
        return value
    
class Detalle(BaseModel):
    codigoInterno:                                      Optional[str] = None
    codigoAdicional:                                    Optional[str] = None
    descripcion:                                        str
    cantidad:                                           int
    detallesAdicionales:                                Optional[List[DetallesAdicionales]] = None

class Destinatario(BaseModel):
    identificacionDestinatario:                         str
    razonSocialDestinatario:                            str
    dirDestinatario:                                    str
    motivoTraslado:                                     str
    codEstabDestino:                                    Optional[str] = None
    codDocSustento:                                     Optional[str] = None
    numDocSustento:                                     Optional[str] = None
    numAutDocSustento:                                  Optional[str] = None
    fechaEmisionDocSustento:                            Optional[str] = None
    docAduaneroUnico:                                   Optional[str] = None
    ruta:                                               Optional[str] = None
    detalles:                                           List[Detalle]

class GuiaRemision(BaseModel):
    infoTributaria:                                     InfoTributaria
    infoGuiaRemision:                                   InofoGuiaRemision
    destinatarios:                                      List[Destinatario]
    infoAdicional:                                      Optional[List[DetallesAdicionales]]
    campoAdicional1:                                    Optional[str] = Field(None, description="Campo para enviar el nombre del logo con extensión (ejemplo: logo.png)")
    campoAdicional2:                                    Optional[str] = Field(None, description="Campo para enviar información adicional 2")