from ...exceptions.base_exception import AppBaseException

class XSDErrorException(AppBaseException):
    def __init__(self, detail: str):
        super().__init__(f"Ocurrión un error durante la validacion del XML: {detail}")
        self.detail = detail