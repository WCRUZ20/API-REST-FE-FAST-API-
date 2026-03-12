from ....exceptions.base_exception import AppBaseException

class ProfileNotFoundException(AppBaseException):
    def __init__(self, name: str):
        super().__init__(f"El perfil {name} no existe, por favor verifique la información e intente nuevamente")
        self.name = name
    
class UnAuthorizedException(AppBaseException):
    def __init__(self, action: str):
        super().__init__(f"No está autorizado para realizar la siguiente acción: {action}")
        self.action = action

class ProfileExistsException(AppBaseException):
    def __init__(self, profileName: str):
        super().__init__(f"El perfil {profileName} ya existe")
        self.profileName = profileName