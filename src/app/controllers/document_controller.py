import os

from tortoise import Tortoise
from src.app.db.connection_enum import ConnectionName
from ...core.documentos_electronicos_core.schemas.invoice_schema import Invoice
from ...core.documentos_electronicos_core.schemas.nota_credito_schema import NotaCredito
from ...core.documentos_electronicos_core.services.invoice_service import InvoiceService
from ...core.documentos_electronicos_core.services.nota_credito_service import NotaCreditoService
from ...core.documentos_electronicos_core.services.retencion_service import RetentionService
from ...core.documentos_electronicos_core.services.guia_remision_service import GuiaService
from ...core.documentos_electronicos_core.services.liquidacion_compra_service import LiquidacionCompraService
from ...core.documentos_electronicos_core.services.notadebito_service import NotaDebitoService
from ...core.documentos_electronicos_core.services.documento_service import DocumentService
from ..middlewares.audit_middleware import AuditRecord

class DocumentController():
    def __init__(self):
        self.db = Tortoise.get_connection(ConnectionName.DEFAULT.value)
        self.audit = AuditRecord()

    async def send_invoice(self, invoice: Invoice, user, background_tasks):
        auditor_creador = await self.audit.audit_for_create_dict(user)
        servicio_factura = InvoiceService(self.db)
        response = await servicio_factura.sign_invoice(invoice, auditor_creador, background_tasks)
        return {
            'result': {
                **response['result']
            }
        }
    
    async def send_invoice_sap(self, invoice: Invoice, user, background_tasks):
        auditor_creador = await self.audit.audit_for_create_dict(user)
        servicio_factura = InvoiceService(self.db)
        response = await servicio_factura.send_invoice_sap(invoice, auditor_creador, background_tasks)
        return {
            'result': {
                **response['result']
            }
        }
    
    async def send_nota_credito_sap(self, nota_credito: NotaCredito, user, background_tasks):
        auditor_creador = await self.audit.audit_for_create_dict(user)
        servicio_nota_credito = NotaCreditoService(self.db)
        response = await servicio_nota_credito.sign_nota_credito_sap(nota_credito, auditor_creador, background_tasks)
        return {
            'result': {
                **response['result']
            }
        }
    
    async def send_retention(self, retention, user, background_tasks):
        auditor_creador = await self.audit.audit_for_create_dict(user)
        servicio_retencion = RetentionService(self.db)
        response = await servicio_retencion.envio_retencion_sap(retention, auditor_creador, background_tasks)
        return {
            'result': {
                **response['result']
            }
        }
    
    async def enviar_guiaRemision(self, guia_remision, user, background_tasks):
        auditor_creador = await self.audit.audit_for_create_dict(user)
        servicio_guiaRemision = GuiaService(self.db)
        response = await servicio_guiaRemision.enviar_guia_remision(guia_remision, auditor_creador, background_tasks)
        return {
            'result': {
                **response['result']
            }
        }
    
    async def enviar_liquidacioncompra(self, liquidacionCompra, user, background_tasks):
        auditor_creador = await self.audit.audit_for_create_dict(user)
        servicio_guiaRemision = LiquidacionCompraService(self.db)
        response = await servicio_guiaRemision.enviar_liquidacion_compra(liquidacionCompra, auditor_creador, background_tasks)
        return {
            'result': {
                **response['result']
            }
        }
    
    async def enviar_notadebito(self, notaDebito, user, background_tasks):
        auditor_creador = await self.audit.audit_for_create_dict(user)
        servicio_guiaRemision = NotaDebitoService(self.db)
        response = await servicio_guiaRemision.enviar_notadebito(notaDebito, auditor_creador, background_tasks)
        return {
            'result': {
                **response['result']
            }
        }
    
    async def consultar_estado_factura(self, consulta, user):
        auditor_creador = await self.audit.audit_for_create_dict(user)
        servicio_factura = DocumentService(self.db)
        response = await servicio_factura.consultar_estado_factura(consulta, auditor_creador)
        return {
            'result': {
                **response['result']
            }
        }