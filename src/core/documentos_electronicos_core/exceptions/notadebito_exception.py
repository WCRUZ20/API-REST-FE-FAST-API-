from ...exceptions.base_exception import AppBaseException

class NotaDebitoDataNotExistsException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"La informacion del usuario {detail} no existe")

class NotaDebitoErrorException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"Ocurrión un error durante el registro de la Nota de Debito.")
        self.detail = detail