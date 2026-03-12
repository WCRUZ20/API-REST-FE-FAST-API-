from ...exceptions.base_exception import AppBaseException

class InvoiceException(AppBaseException):

    ERROR_MESSAGES = {
        "2": "RUC del emisor se encuentra NO ACTIVO.",
        "10": "Establecimiento del emisor se encuentra Clausurado.",
    }

    def __init__(self, detail: str):
        super().__init__(detail)

class InvoiceErrorException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"Ocurrión un error durante el registro de la factura.")
        self.detail = detail

class InvoiceDataNotExistsException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"La informacion del usuario {detail} no existe")
        self.message = f"La informacion del usuario {detail} no existe"