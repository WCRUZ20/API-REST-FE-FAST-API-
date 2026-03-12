import bcrypt

from ..schemas.user_schema import UserCreateModel, DatosFacturacionRegisterModel
from ...users.exceptions.user_exception import UserExistsException, DataFacturacionExistsException
from ...profiles.exceptions.profile_exception import ProfileNotFoundException
from .....app.middlewares.audit_middleware import ModelAudit
from .....app.models.model import User, Profile, Datos_Facturacion

from datetime import datetime

from typing import Dict

class UserService():
    def __init__(self, db):
        self.db = db

    async def create_user(self, user_data: UserCreateModel, user_info: ModelAudit) -> Dict[str, str]: 
        existing_user = await User.get_or_none(usuario=user_data.usuario)
        if existing_user:
            raise UserExistsException(existing_user.usuario)
        
        profile = await Profile.get_or_none(id=user_data.profile_id)
        if not profile:
            raise ProfileNotFoundException(user_data.profile_id)
        
        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())

        user = await User.create(
            usuario = user_data.usuario,
            email = user_data.email,
            password = hashed_password,
            identificacion=user_data.identificacion,
            full_name = user_data.full_name,
            active = 1,
            created = user_info['created'],  #datetime.utcnow()
            created_by = user_info['created_by'], #1
            created_by_name = user_info['created_by_name'], #"Kevin Carvajal",
            profile = profile
        )

        return {"message": f"Usuario {user.full_name} creado exitosamente"}
    
    async def create_data_facturacion(self, data_factura: DatosFacturacionRegisterModel, user_info: ModelAudit) -> Dict[str, str]:
        existing_data = await Datos_Facturacion.get_or_none(ruc=data_factura.ruc)
        if existing_data:
            raise DataFacturacionExistsException(data_factura.ruc)

        existing_user = await User.get_or_none(id = data_factura.usuario)
        if not existing_user:
            raise UserExistsException(data_factura.usuario)

        #hashed_password_sign = bcrypt.hashpw(data_factura.password_sign.encode('utf-8'), bcrypt.gensalt())

        await Datos_Facturacion.create(
            user = existing_user,
            ruc = data_factura.ruc,
            razon_social = data_factura.razon_social,
            nombre_comercial = data_factura.nombre_comercial,
            direccion = data_factura.direccion,
            obligado_contabilidad = data_factura.obligado_contabilidad,
            telefono = data_factura.telefono,
            nombre_firma = data_factura.nombre_firma,
            ruta_logo = data_factura.ruta_logo,
            password_sign = data_factura.password_sign,
            created = user_info['created'],  
            created_by = user_info['created_by'], 
            created_by_name = user_info['created_by_name']
        )

        return { "message": f"Data de {data_factura.ruc} - {data_factura.razon_social} registrada exitosamente."}
    
    """ async def create_user(self, user_data: UserCreateModel) -> Dict[str, str]: 
        existing_user = await User.get_or_none(usuario=user_data.usuario)
        if existing_user:
            raise UserExistsException(existing_user.usuario)
        
        profile = await Profile.get_or_none(id=user_data.profile_id)
        if not profile:
            raise ProfileNotFoundException(user_data.profile_id)
        
        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())

        user = await User.create(
            usuario = user_data.usuario,
            email = user_data.email,
            password = hashed_password,
            identificacion=user_data.identificacion,
            full_name = user_data.full_name,
            active = 1,
            created = datetime.utcnow(),
            created_by = 1,
            created_by_name = "Kevin Carvajal",
            profile = profile
        )

        return {"message": f"Usuario {user.email} creado exitosamente"} """