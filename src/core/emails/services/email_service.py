import requests
import locale
import bcrypt
import logging
import os
import certifi
import json


from dotenv import dotenv_values 
from tortoise.transactions import atomic, in_transaction
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, TrackingSettings, ClickTracking
from ..schemas.email_schema import EmailData
from ...documentos_electronicos_core.schemas.invoice_schema import Invoice
from ....app.constans.enums import EmailTemplate, ProfilesId, CarpetaDocumentos
from ....app.models.model import Datos_Facturacion, User, Profile, EmailLog, Factura, NotaCreditoModel, RetentionModel, GuiaRemisionModel, LiquidacionCompraModel, NotaDebitoModel
from ...documentos_electronicos_core.schemas.schemas import FacturaSchema, GuiaSchema, LiquidacionCompraSchema, NotaCreditoSchema, RetencionSchema, NotaDebitoSchema
from ....app.middlewares.audit_middleware import ModelAudit
from ...security.profiles.exceptions.profile_exception import ProfileNotFoundException


os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE'] = certifi.where()
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

TIPO_DOCUMENTO_ENTIDADES = {
    CarpetaDocumentos.FACTURAS.value: FacturaSchema,
    CarpetaDocumentos.NOTAS_CREDITO.value: NotaCreditoSchema,
    CarpetaDocumentos.RETENCIONES.value: RetencionSchema,
    CarpetaDocumentos.GUIAS_REMISION.value: GuiaSchema,
    CarpetaDocumentos.LIQUIDACIONES_COMPRA.value: LiquidacionCompraSchema,
    CarpetaDocumentos.NOTAS_DEBITO.value: NotaDebitoSchema
}

class EmailService():
        
    def __init__(self, db) -> None:
        self.db = db
        self.config = {
            **dotenv_values('.env')
        }

    async def obtener_email_log_existente(self, carpeta: str, id_documento: int) -> EmailLog | None:
        if carpeta == CarpetaDocumentos.FACTURAS.value:
            return await EmailLog.filter(id_factura=id_documento).first()
        elif carpeta == CarpetaDocumentos.NOTAS_CREDITO.value:
            return await EmailLog.filter(id_notacredito=id_documento).first()
        elif carpeta == CarpetaDocumentos.RETENCIONES.value:
            return await EmailLog.filter(id_retencion=id_documento).first()
        elif carpeta == CarpetaDocumentos.LIQUIDACIONES_COMPRA.value:
            return await EmailLog.filter(id_liquidacioncompra=id_documento).first()
        elif carpeta == CarpetaDocumentos.NOTAS_DEBITO.value:
            return await EmailLog.filter(id_notadebito=id_documento).first()
        elif carpeta == CarpetaDocumentos.GUIAS_REMISION.value:
            return await EmailLog.filter(id_guiaremision=id_documento).first()
        else:
            return None

    @atomic()
    async def send_mails(self, emailData: EmailData, documento, user_info: ModelAudit, carpeta: str, id_documento: int):
        user = await User.filter(usuario=emailData.usuario).first()
        datos_facturacion = await Datos_Facturacion.get_or_none(user=user_info["created_by"])

        email_log_existente = await self.obtener_email_log_existente(carpeta, id_documento)
        if email_log_existente and email_log_existente.status == "sent":
            logging.info("Ya se envió exitosamente el correo para este documento.")
            return email_log_existente

        numero_documento = documento.infoTributaria.estab + "-" + documento.infoTributaria.ptoEmi + "-" + documento.infoTributaria.secuencial

        documento_electronico = None
        if carpeta == CarpetaDocumentos.FACTURAS.value:
            documento_electronico = await Factura.get_or_none(id=id_documento)
        elif carpeta == CarpetaDocumentos.NOTAS_CREDITO.value:
            documento_electronico = await NotaCreditoModel.get_or_none(id=id_documento)
        elif carpeta == CarpetaDocumentos.RETENCIONES.value:
            documento_electronico = await RetentionModel.get_or_none(id=id_documento)
        elif carpeta == CarpetaDocumentos.GUIAS_REMISION.value:
            documento_electronico = await GuiaRemisionModel.get_or_none(id=id_documento)
        elif carpeta == CarpetaDocumentos.LIQUIDACIONES_COMPRA.value:
            documento_electronico = await LiquidacionCompraModel.get_or_none(id=id_documento)
        elif carpeta == CarpetaDocumentos.NOTAS_DEBITO.value:
            documento_electronico = await NotaDebitoModel.get_or_none(id=id_documento)

        try:
            if user:
                response_mail = self.send_document_message(emailData, documento, datos_facturacion, carpeta)
                logging.info(f"MAIL: {response_mail}")
                if response_mail.status_code != 200:
                    raise Exception(f"Error al enviar el correo: {response_mail.text}")
            else:
                profile = await Profile.get_or_none(id=ProfilesId.CLIENTE.value)
                if not profile:
                    raise ProfileNotFoundException(ProfilesId.CLIENTE.value)

                hashed_password = bcrypt.hashpw(emailData.usuario.encode('utf-8'), bcrypt.gensalt())

                async with in_transaction():
                    user_create = await User.create(
                        identificacion=emailData.identificacion,
                        usuario=emailData.usuario,
                        email=emailData.email_receptor,
                        password=hashed_password,
                        full_name=emailData.nombre_usuario,
                        active=1,
                        created=user_info['created'],
                        created_by=user_info['created_by'],
                        created_by_name=user_info['created_by_name'],
                        profile=profile
                    )

                    response_welcome = self.send_welcome_message(emailData)
                    if response_welcome.status_code != 200:
                        raise Exception(f"Error al enviar el correo de bienvenida: {response_welcome.text}")

                    response_mail = self.send_document_message(emailData, documento, datos_facturacion, carpeta)
                    if response_mail.status_code != 200:
                        raise Exception(f"Error al enviar el correo: {response_mail.text}")
                    user = user_create

            email_log_data = {
                "to_email": emailData.email_receptor,
                "subject": emailData.subject,
                "status": "sent",
                "numero_documento": numero_documento,
                "id_user": user,
                "notified": True,
                "retry_count": (email_log_existente.retry_count + 1) if email_log_existente else 0,
            }

            if carpeta == CarpetaDocumentos.FACTURAS.value:
                email_log_data["id_factura"] = documento_electronico
            elif carpeta == CarpetaDocumentos.NOTAS_CREDITO.value:
                email_log_data["id_notacredito"] = documento_electronico
            elif carpeta == CarpetaDocumentos.RETENCIONES.value:
                email_log_data["id_retencion"] = documento_electronico
            elif carpeta == CarpetaDocumentos.LIQUIDACIONES_COMPRA.value:
                email_log_data["id_liquidacioncompra"] = documento_electronico
            elif carpeta == CarpetaDocumentos.GUIAS_REMISION.value:
                email_log_data["id_guiaremision"] = documento_electronico
            elif carpeta == CarpetaDocumentos.NOTAS_DEBITO.value:
                email_log_data["id_notadebito"] = documento_electronico

            return await EmailLog.create(**email_log_data)

        except Exception as e:
            logging.error("Error al enviar correo: %s", str(e))
            error_log_data = {
                "to_email": emailData.email_receptor,
                "subject": emailData.subject,
                "status": "failed",
                "error_message": str(e),
                "retry_count": (email_log_existente.retry_count + 1) if email_log_existente else 1,
                "notified": False,
                "numero_documento": numero_documento,
                "id_user": user,
            }

            if carpeta == CarpetaDocumentos.FACTURAS.value:
                error_log_data["id_factura"] = documento_electronico
            elif carpeta == CarpetaDocumentos.NOTAS_CREDITO.value:
                error_log_data["id_notacredito"] = documento_electronico
            elif carpeta == CarpetaDocumentos.RETENCIONES.value:
                error_log_data["id_retencion"] = documento_electronico
            elif carpeta == CarpetaDocumentos.LIQUIDACIONES_COMPRA.value:
                error_log_data["id_liquidacioncompra"] = documento_electronico
            elif carpeta == CarpetaDocumentos.GUIAS_REMISION.value:
                error_log_data["id_guiaremision"] = documento_electronico
            elif carpeta == CarpetaDocumentos.NOTAS_DEBITO.value:
                error_log_data["id_notadebito"] = documento_electronico

            await EmailLog.create(**error_log_data)
            raise
        
    def send_welcome_message(self, emailData: EmailData):
        url_send_mail = self.config['URL_SEND_MAIL']
        return requests.post(
            url_send_mail,
            auth=('api', self.config['API_KEY_MAILGUN']),
            data={
                'from': 'SOLSAP Bienvenida <notificaciones@solsaptech.com>',
                'to': emailData.email_receptor,
                'subject': "Bienvenido a facturacion - SOLSAP",
                "template": "welcome user",
                "h:X-Mailgun-Variables": '{"nombre_usuario": "' + emailData.nombre_usuario + '", "user": "' + emailData.usuario + '", "contrasenia": "' + emailData.contrasenia + '", "portal_web": "' + self.config['URL_PORTAL'] + '"}'
            }
        )

    def send_document_message(self, emailData: EmailData, documento, datos_facturacion: Datos_Facturacion, carpeta: str):
        url_send_mail = self.config['URL_SEND_MAIL']

        entidad_schema = TIPO_DOCUMENTO_ENTIDADES.get(carpeta)
        # Convertir el documento recibido a la entidad correspondiente
        """ try:
            documento = entidad_schema(**documento.dict())
        except Exception as e:
            raise ValueError(f"Error al mapear el documento con el esquema correspondiente: {str(e)}") """
        
        # Definir etiquetas según carpeta
        valor_pagar = 0
        if carpeta == CarpetaDocumentos.FACTURAS.value:
            tipo_doc = "Factura"
            tipo_doc_correo = "factura"
            valor_pagar += float(documento.infoFactura.importeTotal)
        elif carpeta == CarpetaDocumentos.NOTAS_CREDITO.value:
            tipo_doc = "Nota de Crédito"
            tipo_doc_correo = "nota de credito"
            valor_pagar += float(documento.infoNotaCredito.valorModificacion)
        elif carpeta == CarpetaDocumentos.RETENCIONES.value:
            tipo_doc = "Retención"
            tipo_doc_correo = "retencion"
            for docSustento in documento.docsSustento:
                valor_pagar += float(docSustento.importeTotal)
        elif carpeta == CarpetaDocumentos.LIQUIDACIONES_COMPRA.value:
            tipo_doc = "Liquidación de Compra"
            tipo_doc_correo = "liquidacion de compra"
            valor_pagar += float(documento.infoLiquidacionCompra.importeTotal)
        elif carpeta == CarpetaDocumentos.GUIAS_REMISION.value:
            tipo_doc = "Guia de Remision"
            tipo_doc_correo = "guia de remision"
            valor_pagar += 0
        elif carpeta == CarpetaDocumentos.NOTAS_DEBITO.value:
            tipo_doc = "Nota de Debito"
            tipo_doc_correo = "nota de debito"
            valor_pagar += float(documento.infoNotaDebito.valorTotal)
        else:
            tipo_doc = "Documento Electrónico"
            tipo_doc_correo = "documento"

        # Construir título del correo
        titulo_correo = f"{tipo_doc} {documento.infoTributaria.estab}-{documento.infoTributaria.ptoEmi}-{documento.infoTributaria.secuencial}"
        
        # Obtener clave de acceso
        clave_acceso = documento.infoTributaria.claveAcceso

        # Construir URLs
        url_documento_xml = f"{self.config['URL_DOWNLOAD_DOCUMENT_XML']}/{carpeta}/{datos_facturacion.ruc}/{clave_acceso}"
        url_documento_pdf = f"{self.config['URL_DOWNLOAD_DOCUMENT_PDF']}/{carpeta}/{datos_facturacion.ruc}/{clave_acceso}"

        # Preparar payload para Mailgun
        variables_mailgun = {
            "titulo_correo": titulo_correo,
            "nombre_usuario": emailData.nombre_usuario,
            "documento": tipo_doc_correo,
            "nombre_comercial": datos_facturacion.razon_social,
            "fecha_emision": datetime.now().strftime('%B %d, %Y').capitalize(),
            "valor_pagar": str(valor_pagar),
            "url_documento_xml": url_documento_xml,
            "url_documento_pdf": url_documento_pdf
        }

        return requests.post(
            url_send_mail,
            auth=('api', self.config['API_KEY_MAILGUN']),
            data={
                'from': 'SOLSAP Documentos Electronicos <notificaciones@solsaptech.com>',
                'to': emailData.email_receptor,
                'subject': emailData.subject,
                'template': 'mail invoice',
                'h:X-Mailgun-Variables': json.dumps(variables_mailgun)
            }
        )