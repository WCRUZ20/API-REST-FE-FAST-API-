import enum

class EmailTemplate(str, enum.Enum):
    FACTURA                     =       'Mail Invoice'
    NOTA_CREDITO                =       ''
    BIENVENIDA                  =       'welcome user'

class ProfilesId(str, enum.Enum):
    ADMINISTRADOR               =       1
    ADMINISTRADOR_SOLSAP        =       2
    DESARROLLADOR               =       3
    CLIENTE                     =       4

class DocumentType(str, enum.Enum):
    FACTURA                     =       '01'
    LIQUIDACION_COMPRA          =       '03'
    NOTA_CREDITO                =       '04'
    NOTA_DEBITO                 =       '05'
    GUIA_REMISION               =       '06'
    RETENCION                   =       '07'
    COMPROBANTE_ELECTRONICO     =       '09'

class ImpositivoRetenido(str, enum.Enum):
    RENTA                       =       '1'
    IVA                         =       '2'
    ISD                         =       '6'

class CarpetaDocumentos(str, enum.Enum):
    FACTURAS                    =       'facturas'
    NOTAS_CREDITO               =       'notacredito'
    NOTAS_DEBITO                =       'notadebito'
    GUIAS_REMISION              =       'guiaremision'
    LIQUIDACIONES_COMPRA        =       'liquidacioncompra'
    RETENCIONES                 =       'retenciones'
    COMPROBANTES_ELECTRONICOS   =       'comprobanteselectronicos'

class FormasPagoCodigo(str, enum.Enum):
    SIN_UTILIZACION_DEL_SISTEMA_FINANCIERO          =   '01'
    COMPENSACION_DE_DEUDAS                          =   '15'
    TARJETA_DE_DEBITO                               =   '16'
    DINERO_ELECTRONICO                              =   '17'
    TARJETA_PREPAGO                                 =   '18'
    TARJETA_DE_CREDITO                              =   '19'
    OTROS_CON_UTILIZACION_DEL_SISTEMA_FINANCIERO    =   '20'
    ENDOSO_TITULOS                                  =   '21'

    @staticmethod
    def get_label_by_code(code: str) -> str:
        for item in FormasPagoCodigo:
            if item.value == code:
                return item.name.replace('_', ' ')
        return "CÓDIGO DESCONOCIDO"
