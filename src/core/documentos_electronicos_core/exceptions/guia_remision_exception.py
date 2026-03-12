from ...exceptions.base_exception import AppBaseException

class GuiaRemisionDataNotExistsException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"La informacion del usuario {detail} no existe")

class GuiaRemisionErrorException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"Ocurrión un error durante el registro de la Guia de Remision.")
        self.detail = detail