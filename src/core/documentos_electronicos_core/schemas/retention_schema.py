from pydantic import BaseModel, field_validator, Field, model_validator
from typing import List, Optional, Literal
from .base_schema import InfoTributaria, DetallesAdicionales
from datetime import datetime

class InfoCompRetencion(BaseModel):
    fechaEmision:                       str             = Field(..., description="Fecha de emision en formato dd/mm/yyyy")
    dirEstablecimiento:                 Optional[str]   = None
    contribuyenteEspecial:              Optional[str]   = None
    obligadoContabilidad:               Optional[str]   = None
    tipoIdentificacionSujetoRetenido:   str
    tipoSujetoRetenido:                 str
    parteRel:                           str             = Field(..., description="Indicar si hay relación: 'SI' o 'NO'")
    razonSocialSujetoRetenido:          str
    identificacionSujetoRetenido:       str
    periodoFiscal:                      str

    @field_validator('fechaEmision')
    @classmethod
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Fecha debe estar en formato dd/mm/yyyy")
        return value
    
    @field_validator("parteRel")
    @classmethod
    def validar_parte_rel(cls, v):
        if v not in {"SI", "NO"}:
            raise ValueError("El valor de parteRel debe ser 'SI' o 'NO'")
        return v

class ImpuestoDocSustento(BaseModel):
    codImpuestoDocSustento:          str
    codigoPorcentaje:                   str
    baseImponible:                      str
    tarifa:                             str
    valorImpuesto:                      str

class Dividendos(BaseModel):
    fechaPagoDiv:                       Optional[str]   = Field(None, description="Fecha de pago de dividendos dd/mm/yyyy")
    imRentaSoc:                         Optional[str]   = Field(None, description="Impuesto renta")
    ejerFisUtDiv:                       Optional[str]   = Field(None, description="Ejercicio Fiscal Ut Div")

class Retencion_Interna(BaseModel):
    codigo:                             str
    codigoRetencion:                    str
    baseImponible:                      str
    porcentajeRetener:                  str
    valorRetenido:                      str
    dividendos:                         Optional[Dividendos]   = Field(None, description="Dividendos")

class Pago(BaseModel):
    formaPago:                          str
    total:                              str

class DocSustento(BaseModel):
    codSustento:                        str
    codDocSustento:                     str
    numDocSustento:                     str
    factura_relacionada:                str
    fechaEmisionDocSustento:            str             = Field(..., description="Fecha de emision del documento sustento en formato dd/mm/yyyy")
    fechaRegistroContable:              Optional[str]   = Field(..., description="Fecha de registro contable sustento en formato dd/mm/yyyy")
    numAutDocSustento:                  Optional[str]   = None
    pagoLocExt:                         str
    tipoRegi:                           Optional[str]   = None
    paisEfecPago:                       Optional[str]   = None
    aplicConvDobTrib:                   Optional[str]   = Field(None, description="Aplicación de convenio de doble tributación")
    pagExtSujRetNorLeg:                 Optional[str]   = Field(None, description="Pago al exterior sujeto a retención por norma legal")
    pagRegFis:                          Optional[str]   = Field(None, description="Pago al registro fiscal")
    totalComprobantesReembolso:         Optional[str]   = Field(None, description="Total de comprobantes reembolsados")
    totalBaseImponibleReembolso:        Optional[str]   = Field(None, description="Total de base imponible reemplosados")
    totalSinImpuestos:                  str
    importeTotal:                       str
    impuestosDocSustento:               List[ImpuestoDocSustento]
    retenciones:                        List[Retencion_Interna]
    #no se ha agregado 'reembolsos'
    pagos:                              List[Pago]

    @field_validator('fechaEmisionDocSustento', 'fechaRegistroContable')
    @classmethod
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Fecha debe estar en formato dd/mm/yyyy")
        return value
    
    @model_validator(mode="after")
    def validar_condicionales(self):
        codigo_doc_sustento = self.codDocSustento
        pago = self.pagoLocExt
        aplic_conv = self.aplicConvDobTrib
        pag_ext = self.pagExtSujRetNorLeg
        pag_reg = self.pagRegFis
        totalCompReem = self.totalComprobantesReembolso
        totalBaseImpoReem = self.totalBaseImponibleReembolso

        if codigo_doc_sustento == "41" and not totalCompReem:
            raise ValueError("El campo 'totalComprobantesReembolso' es obligatorio cuando 'codDocSustento' es 41")
        
        if codigo_doc_sustento == "41" and not totalBaseImpoReem:
            raise ValueError("El campo 'totalBaseImpoReem' es obligatorio cuando 'codDocSustento' es 41")

        # Validar que aplicConvDobTrib sea obligatorio si pagoLocExt == "02"
        if pago == "02" and not aplic_conv:
            raise ValueError("El campo 'aplicConvDobTrib' es obligatorio cuando 'pagoLocExt' es '02'")
        
        if pago == "02" and not pag_reg:
            raise ValueError("El campo 'pag_reg' es obligatorio cuando 'pagoLocExt' es '02'")

        # Validar que pagExtSujRetNorLeg sea obligatorio si aplicConvDobTrib == "NO"
        if aplic_conv == "NO" and not pag_ext:
            raise ValueError("El campo 'pagExtSujRetNorLeg' es obligatorio cuando 'aplicConvDobTrib' es 'NO'")

        if self.codSustento == "10":
            for idx, r in enumerate(self.retenciones):
                if not r.dividendos:
                    raise ValueError(f"El campo 'dividendos' es obligatorio en retenciones[{idx}] cuando 'codSustento' es '10'")
                
                dividendos = r.dividendos

                if not dividendos.fechaPagoDiv:
                    raise ValueError(f"El campo 'fechaPagoDiv' es obligatorio en retenciones[{idx}] cuando 'codSustento' es '10'")
                if not dividendos.imRentaSoc:
                    raise ValueError(f"El campo 'imRentaSoc' es obligatorio en retenciones[{idx}] cuando 'codSustento' es '10'")
                if not dividendos.ejerFisUtDiv:
                    raise ValueError(f"El campo 'ejerFisUtDiv' es obligatorio en retenciones[{idx}] cuando 'codSustento' es '10'")

                try:
                    datetime.strptime(dividendos.fechaPagoDiv, "%d/%m/%Y")
                except ValueError:
                    raise ValueError(f"El campo 'fechaPagoDiv' en retenciones[{idx}] debe tener el formato dd/mm/yyyy")

        return self

class Impuesto(BaseModel):
    codigo:                             str
    codigoRetencion:                    str
    baseImponible:                       str
    porcentajeRetener:                  str
    valorRetenido:                       str
    codDocSustento:                      Optional[str] = None
    numDocSustento:                      Optional[str] = None
    fechaEmisionDocSustento:             Optional[str] = Field(..., description="Fecha de inicio del transporte en formato dd/mm/yyyy")

    @field_validator('fechaEmisionDocSustento')
    @classmethod
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Fecha debe estar en formato dd/mm/yyyy")
        return value

class Retention(BaseModel):
    infoTributaria:                     InfoTributaria
    infoCompRetencion:                  InfoCompRetencion
    docsSustento:                       List[DocSustento]
    infoAdicional:                      Optional[List[DetallesAdicionales]]  = None
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