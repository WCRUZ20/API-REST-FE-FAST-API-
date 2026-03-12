from src.app.models.model import User

async def autenticate_user(usuari):
    try:
        user = await User.filter(usuario=usuari).first()
        if user is not None:
            return {"user": user, "userFound": True}
        return {"userFound": False}
    except Exception as e:
        return {"error": True}