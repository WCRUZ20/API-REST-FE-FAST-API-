from ...exceptions.base_exception import AppBaseException

class LiquidacionCompraDataNotExistsException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"La informacion del usuario {detail} no existe")

class LiquidacionCompraErrorException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"Ocurrión un error durante el registro de la liquidación de compra.")
        self.detail = detail