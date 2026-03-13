import traceback
from typing import Any
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(data: Any, total:int = None):
    content = {"success": True, "data": jsonable_encoder(data)}
    if total is not None:
        content["total"] = total
    return JSONResponse(
        content=content, 
        status_code=200
    )

def fails_response(e: Exception, status_code: int = 500):
    # TODO: Registrar exception en log
    traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
    #print(traceback_str)
    codigo_return = 0
    if status_code == 400:
        codigo_return = 4

    return JSONResponse(
        content={
            "success": False, 
            "data": {
                "result": {
                    "codigo": codigo_return,
                    "mensaje": str(e.detail), 
                    "claveAcceso": None
                }
            }
        },
        status_code=status_code
    )