from pydantic import BaseModel
from typing import Any, Optional

class SuccessModel(BaseModel):
    success: bool = True
    data: Any
    total: Optional[int] = None

class ErrorModel(BaseModel):
    success: bool = False
    message: str
