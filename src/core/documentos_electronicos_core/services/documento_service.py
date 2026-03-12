import pytz

from datetime import datetime
from dotenv import dotenv_values
from tortoise.transactions import in_transaction, atomic
from ..schemas.base_schema import ConsultaDocumento
from ..schemas.respuestas_sri_schema import map_sri_status_to_custom
from ....app.middlewares.audit_middleware import ModelAudit
from ....utils.sendXml import send_consult_accesskey

class DocumentService():
    def __init__(self, db):
        self.db = db
        self.config = {
            **dotenv_values('.env')
        }

    async def consultar_estado_factura(self, consulta: ConsultaDocumento, user):
        clave_acceso = consulta.claveAcceso
        url_consulta = self.config["URL_CONSULTA_COMPROBANTE_PRUEBAS"]

        consultaDoc = await send_consult_accesskey(clave_acceso, url_consulta)
        return {
            'result': {
                **consultaDoc
            }
        }
