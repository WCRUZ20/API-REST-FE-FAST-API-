from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials

from ..core.security.profiles.schemas.profile import ProfileModel
from ..app.controllers.profile_controller import ProfileController
from ..core.security.profiles.exceptions.profile_exception import ProfileExistsException

profile_router = APIRouter()

TAG = "Profile"

@profile_router.post("/create", tags=[TAG], response_model=dict)
async def createProfile(profile: ProfileModel) -> dict:
    try:
        profile_controller = ProfileController()
        response = await profile_controller.create_profile(profile)
        return JSONResponse(content=jsonable_encoder(response), status_code=200)
    except ProfileExistsException as e:
        raise HTTPException(status_code=400, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")