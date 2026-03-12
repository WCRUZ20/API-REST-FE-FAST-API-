from fastapi import APIRouter

from .db_router import db_router
from .document_router import document_router
from .auth_router import auth_route
from .profile_router import profile_router
from .user_router import user_router
from .email_router import email_router

router = APIRouter()

router.include_router(user_router, prefix="/user")
router.include_router(auth_route, prefix="/auth")
router.include_router(db_router, prefix="/dbs")
router.include_router(profile_router, prefix="/profile")
router.include_router(document_router, prefix='/document')
router.include_router(email_router, prefix='/email')