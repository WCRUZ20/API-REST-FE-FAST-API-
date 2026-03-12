from ...exceptions.base_exception import AppBaseException

class RetentionDataNotExistsException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"La informacion del usuario {detail} no existe")
    
class RetentionErrorException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"Ocurrió un error durante el registro de la retención.")
        self.detail = detail