from pydantic import BaseModel, field_validator, Field, model_validator
from typing import  List, Optional
from datetime import datetime
from .base_schema import InfoTributaria, DetallesAdicionales, Detalle, TotalConImpuesto, Pago

class DetalleImpuestoReembolso(BaseModel):
    codigo:                             str = Field(..., description="Código del impuesto")
    codigoPorcentaje:                   str = Field(..., description="Código del porcentaje del impuesto")
    baseImponibleReembolso:             str = Field(..., description="Base imponible del impuesto")
    tarifa:                             str = Field(..., description="Tarifa del impuesto")
    impuestoReembolso:                  str = Field(..., description="Valor del impuesto")

    @field_validator('baseImponibleReembolso', 'impuestoReembolso')
    @classmethod
    def validate_positive(cls, value):
        if float(value) < 0:
            raise ValueError("El valor debe ser positivo")
        return value

class ReembolsoDetalle(BaseModel):
    tipoIdentificacionProveedorReembolso:   str = Field(..., description="Tipo de identificación del proveedor de reembolso")
    identificacionProveedorReembolso:       str = Field(..., description="Identificación del proveedor de reembolso")
    codPaisPagoProveedorReembolso:          str = Field(..., description="Código del país de pago del proveedor de reembolso")
    tipoProveedorReembolso:                 str = Field(..., description="Tipo de proveedor de reembolso")
    codDocReembolso:                        str = Field(..., description="Código del documento de reembolso")
    estabDocReembolso:                      str = Field(..., description="Establecimiento del documento de reembolso")
    ptoEmiDocReembolso:                     str = Field(..., description="Punto de emisión del documento de reembolso")
    secuencialDocReembolso:                 str = Field(..., description="Secuencial del documento de reembolso")
    fechaEmisionDocReembolso:               str = Field(..., description="Fecha de emisión del documento de reembolso en formato dd/mm/yyyy")
    numeroautorizacionDocReemb:             str = Field(..., description="Número de autorización del documento de reembolso")
    detalleImpuestos:                       List[DetalleImpuestoReembolso] = Field(..., description="Lista de impuestos del reembolso")

    @field_validator('fechaEmisionDocReembolso')
    @classmethod
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Fecha debe estar en formato dd/mm/yyyy")
        return value

class InfoFactura(BaseModel):
    fechaEmision:                       str           = Field(..., description="Fecha de emision en formato dd/mm/yyyy")  
    dirEstablecimiento:                 Optional[str] = Field(None, description="Dirección del establecimiento")
    contribuyenteEspecial:              Optional[str] = Field(None, description="Contribuyente especial")
    obligadoContabilidad:               Optional[str] = Field(None, description="Obligado a llevar contabilidad")
    tipoIdentificacionComprador:        str
    guiaRemision:                       Optional[str] = Field(None, description="Guía de remisión")
    razonSocialComprador:               str
    identificacionComprador:            str
    direccionComprador:                 Optional[str] = Field(None, description="Dirección del comprador")
    totalSinImpuestos:                  str
    totalDescuento:                     str
    totalConImpuestos:                  list[TotalConImpuesto]
    propina:                            str
    importeTotal:                       str
    moneda:                             str
    pagos:                              list[Pago]
    valorRetIva:                        Optional[str] = None
    valorRetRenta:                      Optional[str] = None

    #Exportación
    comercioExterior:                   Optional[str] = Field(None, description="Comercio exterior | Obligatorio si es de exportación (EXPORTADOR)")
    IncoTermFactura:                    Optional[str] = Field(None, description="Incoterm de la factura | Obligatorio si es de exportación (EXPORTADOR)")
    lugarIncoTerm:                      Optional[str] = Field(None, description="Lugar del Incoterm | Obligatorio si es de exportación (EXPORTADOR)")
    paisOrigen:                         Optional[str] = Field(None, description="País de origen | Obligatorio si es de exportación (EXPORTADOR)")
    puertoEmbarque:                     Optional[str] = Field(None, description="Puerto de embarque | Obligatorio si es de exportación (EXPORTADOR)")
    paisDestino:                        Optional[str] = Field(None, description="País de destino | Obligatorio si es de exportación (EXPORTADOR)")
    paisAdquisicion:                    Optional[str] = Field(None, description="País de adquisición | Obligatorio si es de exportación (EXPORTADOR)") 
    incoTermTotalSinImpuestos:          Optional[str] = Field(None, description="Incoterm total sin impuestos | Obligatorio si es de exportación (EXPORTADOR)") 
    fleteInternacional:                 Optional[str] = Field(None, description="Flete internacional | Obligatorio si es de exportación (EXPORTADOR)")
    seguroInternacional:                Optional[str] = Field(None, description="Seguro internacional | Obligatorio si es de exportación (EXPORTADOR)")
    gastosAduaneros:                    Optional[str] = Field(None, description="Gastos aduaneros | Obligatorio si es de exportación (EXPORTADOR)")
    gastosTransporteOtros:              Optional[str] = Field(None, description="Gastos de transporte y otros | Obligatorio si es de exportación (EXPORTADOR)")

    #Reembolso
    codDocReembolso:                    Optional[str] = Field(None, description="Código del documento de reembolso(41) | Obligatorio si aplica")
    totalComprobantesReembolso:         Optional[str] = Field(None, description="Total de comprobantes de reembolso | Obligatorio si 'codDocReembolso' es 41")
    totalBaseImponibleReembolso:        Optional[str] = Field(None, description="Total de base imponible de reembolso | Obligatorio si 'codDocReembolso' es 41")
    totalImpuestoReembolso:             Optional[str] = Field(None, description="Total de impuesto de reembolso | Obligatorio si 'codDocReembolso' es 41")
    reembolsos:                         Optional[List[ReembolsoDetalle]] = Field(None, description="Detalles de reembolsos | Obligatorio si 'codDocReembolso' es 41")

    @field_validator('fechaEmision')
    @classmethod
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Fecha debe estar en formato dd/mm/yyyy")
        return value
    
    @model_validator(mode='after')
    def validar_condicionales(self):
        if self.comercioExterior and not self.IncoTermFactura:
            raise ValueError("Si comercioExterior es 'EXPORTADOR', IncoTermFactura es obligatorio")
        if self.IncoTermFactura and not self.lugarIncoTerm:
            raise ValueError("Si IncoTermFactura está presente, lugarIncoTerm es obligatorio")
        if self.paisOrigen and not self.puertoEmbarque:
            raise ValueError("Si paisOrigen está presente, puertoEmbarque es obligatorio")
        if self.paisDestino and not self.paisAdquisicion:
            raise ValueError("Si paisDestino está presente, paisAdquisicion es obligatorio")
        if self.comercioExterior and not self.puertoEmbarque:
            raise ValueError("Si comercioExterior es 'EXPORTADOR', puertoEmbarque es obligatorio")
        if self.comercioExterior and not self.paisAdquisicion:
            raise ValueError("Si comercioExterior es 'EXPORTADOR', paisAdquisicion es obligatorio")
        if self.comercioExterior and not self.incoTermTotalSinImpuestos:
            raise ValueError("Si comercioExterior es 'EXPORTADOR', incoTermTotalSinImpuestos es obligatorio")
        if self.comercioExterior and not self.fleteInternacional:
            raise ValueError("Si comercioExterior es 'EXPORTADOR', fleteInternacional es obligatorio")
        if self.comercioExterior and not self.seguroInternacional:
            raise ValueError("Si comercioExterior es 'EXPORTADOR', seguroInternacional es obligatorio")
        if self.comercioExterior and not self.gastosAduaneros:
            raise ValueError("Si comercioExterior es 'EXPORTADOR', gastosAduaneros es obligatorio")
        if self.comercioExterior and not self.gastosTransporteOtros:
            raise ValueError("Si comercioExterior es 'EXPORTADOR', gastosTransporteOtros es obligatorio")
        if self.codDocReembolso == "41":
            if not self.totalComprobantesReembolso:
                raise ValueError("El campo 'totalComprobantesReembolso' es obligatorio cuando 'codDocReembolso' es 41")
            if not self.totalBaseImponibleReembolso:
                raise ValueError("El campo 'totalBaseImponibleReembolso' es obligatorio cuando 'codDocReembolso' es 41")
            if not self.totalImpuestoReembolso:
                raise ValueError("El campo 'totalImpuestoReembolso' es obligatorio cuando 'codDocReembolso' es 41")
            if not self.reembolsos:
                raise ValueError("El campo 'reembolsos' es obligatorio cuando 'codDocReembolso' es 41")
        return self
    
class Retencion(BaseModel):
    codigo:                             str
    codigoPorcentaje:                   str
    tarifa:                             str
    valor:                              str

class Invoice(BaseModel):
    infoTributaria:                     InfoTributaria
    infoFactura:                        InfoFactura
    detalles:                           List[Detalle]
    retenciones:                        Optional[List[Retencion]]           = Field(None, description="Opcional. Aplica para comercializadores de derivados de petróleo y retención presuntiva de IVA a editores, distriibuidores y voceadores que participan en la comercialización de periódicos y/o revistas")
    infoAdicional:                      Optional[List[DetallesAdicionales]]
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