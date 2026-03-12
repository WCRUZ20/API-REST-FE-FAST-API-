from src.app.db.connection_enum import ConnectionName
from tortoise import Tortoise
from ...core.emails.schemas.email_schema import EmailData
from ...core.emails.services.email_service import EmailService
from ...core.documentos_electronicos_core.schemas.invoice_schema import Invoice

class EmailController():
    def __init__(self):
        self.db = Tortoise.get_connection(ConnectionName.DEFAULT.value)

    async def send_mail(self, emailData: EmailData, invoice, user_info, carpeta, id_documento: int = None):
        response = await EmailService(self.db).send_mails(emailData, invoice, user_info, carpeta, id_documento)
        return response

    async def sendGridMail(self):
        response = EmailService(self.db).sendMailSendGrid()
        return response