import bcrypt

from ..schemas.user_schema import (
    UserCreateModel,
    DatosFacturacionRegisterModel,
    UserUpdateModel,
    DatosFacturacionUpdateModel,
)
from ...users.exceptions.user_exception import UserExistsException, DataFacturacionExistsException
from ...profiles.exceptions.profile_exception import ProfileNotFoundException, UnAuthorizedException
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
    
    async def update_user(self, user_id: int, user_data: UserUpdateModel, user_info: ModelAudit) -> Dict[str, str]:
        user = await User.get_or_none(id=user_id)
        if not user:
            return {"error": True, "message": f"No existe usuario con id {user_id}"}

        if user_data.profile_id is not None:
            profile = await Profile.get_or_none(id=user_data.profile_id)
            if not profile:
                raise ProfileNotFoundException(user_data.profile_id)
            user.profile = profile

        if user_data.usuario is not None:
            existing_user = await User.get_or_none(usuario=user_data.usuario)
            if existing_user and existing_user.id != user.id:
                raise UserExistsException(user_data.usuario)
            user.usuario = user_data.usuario

        if user_data.password is not None:
            user.password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())

        if user_data.email is not None:
            user.email = user_data.email

        if user_data.full_name is not None:
            user.full_name = user_data.full_name

        if user_data.identificacion is not None:
            user.identificacion = user_data.identificacion

        if user_data.active is not None:
            user.active = user_data.active

        user.updated = user_info['created']
        user.updated_by = user_info['created_by']
        user.updated_by_name = user_info['created_by_name']

        await user.save()

        return {"message": f"Usuario {user.id} actualizado exitosamente"}

    async def update_data_facturacion(self, user_id: int, data_factura: DatosFacturacionUpdateModel, user_info: ModelAudit) -> Dict[str, str]:
        existing_user = await User.get_or_none(id=user_id)
        if not existing_user:
            return {"error": True, "message": f"No existe usuario con id {user_id}"}

        datos_facturacion = await Datos_Facturacion.get_or_none(user=existing_user)
        if not datos_facturacion:
            return {"error": True, "message": f"No existe facturación asociada al usuario {user_id}"}

        if data_factura.ruc is not None:
            existing_data = await Datos_Facturacion.get_or_none(ruc=data_factura.ruc)
            if existing_data and existing_data.id != datos_facturacion.id:
                raise DataFacturacionExistsException(data_factura.ruc)
            datos_facturacion.ruc = data_factura.ruc

        if data_factura.razon_social is not None:
            datos_facturacion.razon_social = data_factura.razon_social

        if data_factura.nombre_comercial is not None:
            datos_facturacion.nombre_comercial = data_factura.nombre_comercial

        if data_factura.direccion is not None:
            datos_facturacion.direccion = data_factura.direccion

        if data_factura.telefono is not None:
            datos_facturacion.telefono = data_factura.telefono

        if data_factura.obligado_contabilidad is not None:
            datos_facturacion.obligado_contabilidad = data_factura.obligado_contabilidad

        if data_factura.nombre_firma is not None:
            datos_facturacion.nombre_firma = data_factura.nombre_firma

        if data_factura.password_sign is not None:
            datos_facturacion.password_sign = data_factura.password_sign

        if data_factura.ruta_logo is not None:
            datos_facturacion.ruta_logo = data_factura.ruta_logo

        datos_facturacion.updated = user_info['created']
        datos_facturacion.updated_by = user_info['created_by']
        datos_facturacion.updated_by_name = user_info['created_by_name']

        await datos_facturacion.save()

        return {"message": f"Datos de facturación del usuario {user_id} actualizados exitosamente"}

    async def get_users(self, user_info):
        profile_id = user_info.get('profile_id')
        if profile_id is None and isinstance(user_info.get('profile'), dict):
            profile_id = user_info['profile'].get('id')

        if profile_id not in [1, 3]:
            raise UnAuthorizedException('listar usuarios de sec_users')

        users = await User.all().select_related('profile').values(
            'id',
            'identificacion',
            'usuario',
            'email',
            'full_name',
            'active',
            'profile_id',
            'profile__name'
        )

        return {
            'message': 'Usuarios obtenidos exitosamente',
            'data': users
        }

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