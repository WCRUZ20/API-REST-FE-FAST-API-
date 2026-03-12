import os 

TORTOISE_ORM = {
    "connections": {
        "default": os.getenv("DATABASE_URL")
    },
    "apps": {
        "models": {
            "models": ["src.app.models"], 
            "default_connection": "default",
        }
    },
}