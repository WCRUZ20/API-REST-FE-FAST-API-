from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from dotenv import dotenv_values
from ..app.controllers.email_controller import EmailController
from .bases.base_response import success_response, fails_response
from fastapi.responses import FileResponse
from src.app.middlewares.jwt_bearer import JWTBearer


import os
import logging

email_router = APIRouter()
jwt_bearer = JWTBearer()

TAG = "Facturacion electronica"

config_env = {
    **dotenv_values(".env")
}

@email_router.get("/sendMail", tags=[TAG])
async def sendMailSendGrid():
    try:
        emailController = EmailController()
        response = await emailController.sendGridMail()
        return response
    except Exception as e:
        logging.error(e)
        return e