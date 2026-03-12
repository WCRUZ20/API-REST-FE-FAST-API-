from ...exceptions.base_exception import AppBaseException

class NotaCreditoDataNotExistsException(AppBaseException):
    def __init__(self, user: str):
        super().__init__(f"La informacion del usuario {user} no existe")

class NotaCreditoErrorException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"Ocurrión un error durante el registro de la nota de crédito.")
        self.detail = detail

class NotaCreditoDataNotExistsException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"La informacion de la nota de crédito del usuario {detail} no existe")
        self.message = f"La informacion de la nota de crédito del usuario {detail} no existe"