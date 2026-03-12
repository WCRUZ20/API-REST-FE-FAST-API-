from ..core.documentos_electronicos_core.schemas.invoice_schema import InfoTributaria, InfoFactura
from .module11 import CheckDigit

from ..app.models.datos_facturacion import Datos_Facturacion

digitoVerificador = CheckDigit()

def getDateComplete(day: str, month: str, year: str):
    return day + month + year

def createAccessKey(documentInfo: InfoTributaria, randomNumber: int, data_facturacion: Datos_Facturacion):
    fechaEmision = ''.join(getDateComplete(documentInfo.diaEmission, documentInfo.mesEmission, documentInfo.anioEmission))
    codDoc = ''.join(documentInfo.codDoc)
    rucNegocio = ''.join(data_facturacion.ruc)
    ambiente = ''.join(documentInfo.ambiente)
    establecimiento = ''.join(documentInfo.estab)
    puntoEmision = ''.join(documentInfo.ptoEmi)
    secuencial = ''.join(documentInfo.secuencial)
    randomNumber = ''.join(randomNumber)
    tipoEmision = ''.join(documentInfo.tipoEmision)

    preClaveAcceso = fechaEmision + codDoc + rucNegocio + ambiente + establecimiento + puntoEmision + secuencial + randomNumber + tipoEmision

    checkerDigit = str(digitoVerificador.compute_mod11(preClaveAcceso))

    if int(checkerDigit) == 10:
        checkerDigit = 1
    if int(checkerDigit) == 11:
        checkerDigit = 0

    return preClaveAcceso + checkerDigit