from ..schemas.profile import ProfileModel, ProfileModelResponse
from ..exceptions.profile_exception import ProfileNotFoundException, UnAuthorizedException, ProfileExistsException
from .....app.models.profile import Profile
from typing import Dict

from datetime import datetime

class ProfileService():
    def __init__(self, db):
        self.db = db

    async def create(self, profile: ProfileModel) -> Dict[str, ProfileModelResponse]:
        existing_profile = await Profile.filter(name__iexact=profile.name.lower()).first()
        if existing_profile:
            raise ProfileExistsException(profile.name)
        
        prof = await Profile.create(
            name = profile.name.lower(),
            active = 1,
            created = datetime.utcnow(), 
            created_by = 1,
            created_by_name = "Kevin Carvajal"
        )

        prof.save()
        
        data_define = ProfileModelResponse(
            id = prof.id,
            name = prof.name, 
            active = prof.active,
            created = prof.created
        )

        return {"message": f"El perfil {profile.name} fue creado exitosamente.", "profile_id": data_define}
    