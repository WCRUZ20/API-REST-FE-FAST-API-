from pydantic import BaseModel, field_validator, Field, model_validator
from typing import List, Optional, Literal
from .base_schema import InfoTributaria, DetallesAdicionales, Impuesto, Pago, Detalle
from datetime import datetime

class TotalImpuesto(Impuesto):
    descuentoAdicional:             Optional[str]           = None

class PagoLiquidacionCompra(Pago):
    plazo:                          str

class InfoLiquidacionCompra(BaseModel):
    fechaEmision:                   str                     = Field(..., description="Fecha de emision en formato dd/mm/yyyy")
    dirEstablecimiento:             Optional[str]           = None
    contribuyenteEspecial:          Optional[str]           = None
    obligadoContabilidad:           Optional[str]           = Field(..., description="Es obligado a llevar contabilidad? SI/NO")
    tipoIdentificacionProveedor:    Optional[str]
    razonSocialProveedor:           str
    identificacionProveedor:        str
    direccionProveedor:             Optional[str]
    totalSinImpuestos:              str
    totalDescuento:                 str
    codDocReembolso:                Optional[str]           = Field(None, description="Código de documento de reembolso")
    totalComprobantesReembolso:     Optional[str]           = Field(None, description="Suma de los comprobantes de reembolso")
    totalBaseImponibleReembolso:    Optional[str]           = Field(None, description="Suma de las bases imponibles reembolsadas")
    totalImpuestoReembolso:         Optional[str]           = Field(None, description="Suma de impuesto reembolsos")
    totalConImpuestos:              List[TotalImpuesto]
    importeTotal:                   str
    moneda:                         str
    pagos:                          List[PagoLiquidacionCompra]

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

    @model_validator(mode="after")
    def validar_cod_reembolso_y_relacionados(self):
        cod = self.codDocReembolso

        if cod == "41":
            if not self.totalComprobantesReembolso:
                raise ValueError("El campo 'totalComprobantesReembolso' es obligatorio cuando 'codDocReembolso' es '41'")
            if not self.totalBaseImponibleReembolso:
                raise ValueError("El campo 'totalBaseImponibleReembolso' es obligatorio cuando 'codDocReembolso' es '41'")
            if not self.totalImpuestoReembolso:
                raise ValueError("El campo 'totalImpuestoReembolso' es obligatorio cuando 'codDocReembolso' es '41'")
        return self

class DetalleLiquidacionCompra(Detalle):
    unidadMedida:                               Optional[str]       = None

class DetalleImpuesto(BaseModel):
    codigo:                                     str
    codigoPorcentaje:                           str
    tarifa:                                     str
    baseImponibleReembolso:                     str
    impuestoReembolso:                          str

class ReembolsoDetalle(BaseModel):
    tipoIdentificacionProveedorReembolso:       str
    identificacionProveedorReembolso:           str
    codPaisPagoProveedorReembolso:              str
    tipoProveedorReembolso:                     str
    codDocReembolso:                            str
    estabDocReembolso:                          str
    ptoEmiDocReembolso:                         str
    secuencialDocReembolso:                     str
    fechaEmisionDocReembolso:                   str         = Field(..., description="Fecha de emision de reembolso en formato dd/mm/yyyy")
    numeroautorizacionDocReemb:                 str
    detalleImpuestos:                           List[DetalleImpuesto]


    @field_validator("fechaEmisionDocReembolso")
    @classmethod
    def validar_fecha(cls, v):
        try:
            datetime.strptime(v, "%d/%m/%Y")
        except ValueError:
            raise ValueError("La 'fechaEmisionDocReembolso' debe tener el formato dd/mm/yyyy")
        return v
    
class LiquidacionCompra(BaseModel):
    infoTributaria:                             InfoTributaria
    infoLiquidacionCompra:                      InfoLiquidacionCompra
    detalles:                                   List[DetalleLiquidacionCompra]
    reembolsos:                                 Optional[List[ReembolsoDetalle]]    = None
    infoAdicional:                              Optional[List[DetallesAdicionales]]     = None
    campoAdicional1:                            Optional[str] = Field(None, description="Campo para enviar el nombre del logo con extensión (ejemplo: logo.png)")
    campoAdicional2:                            Optional[str] = Field(None, description="Campo para enviar información adicional 2")

    @model_validator(mode="after")
    def validar_reembolsos_requeridos(cls, self):
        if self.infoLiquidacionCompra.codDocReembolso == "41" and not self.reembolsos:
            raise ValueError("El campo 'reembolsos' es obligatorio cuando 'codDocReembolso' es '41'")
        return self