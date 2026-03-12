from ....exceptions.base_exception import AppBaseException

class UserExistsException(AppBaseException):
    def __init__(self, user: str):
        super().__init__(f"El usuario {user} ya existe, por favor verifique e intente nuevamente")
        self.user = user

class DataFacturacionExistsException(AppBaseException):
    def __init__(self, ruc: str):
        super().__init__(f"La información de facturación para el ruc {ruc} ya existe, por favor verifique e intente nuevamente")
        self.ruc = ruc