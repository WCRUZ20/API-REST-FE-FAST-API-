from tortoise import Tortoise
from ..db.connection_enum import ConnectionName

from ...core.security.profiles.schemas.profile import ProfileModel
from ...core.security.profiles.services.profile_service import ProfileService

class ProfileController():
    def __init__(self):
        self.db = Tortoise.get_connection(ConnectionName.DEFAULT.value)

    async def create_profile(self, profile: ProfileModel) -> dict:
        return await ProfileService(self.db).create(profile)