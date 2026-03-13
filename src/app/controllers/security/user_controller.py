from tortoise import Tortoise
from ...db.connection_enum import ConnectionName
from ...middlewares.audit_middleware import AuditRecord
from ....core.security.users.schemas.user_schema import UserCreateModel, DatosFacturacionRegisterModel
from ....core.security.users.services.user_service import UserService

class UserController():
    def __init__(self):
        self.db = Tortoise.get_connection(ConnectionName.DEFAULT.value)
        self.audit = AuditRecord()

    async def create_user(self, user: UserCreateModel, user_create):
        auditor_create = await self.audit.audit_for_create_dict(user_create)
        return await UserService(self.db).create_user(user, auditor_create)
    
    async def create_data_factura(self, data_factura: DatosFacturacionRegisterModel, user_create):
        auditor_create = await self.audit.audit_for_create_dict(user_create)
        return await UserService(self.db).create_data_facturacion(data_factura, auditor_create)
    
    async def get_users(self, user_info):
        return await UserService(self.db).get_users(user_info)

    """ async def create_user(self, user: UserCreateModel):
        return await UserService(self.db).create_user(user) """