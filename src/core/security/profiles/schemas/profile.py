from pydantic import BaseModel
from datetime import datetime

class ProfileModel(BaseModel):
    name:           str

class ProfileModelResponse(BaseModel):
    id:             int
    name:           str
    active:         bool
    created:        datetime