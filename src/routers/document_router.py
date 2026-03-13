from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from dotenv import dotenv_values

from ..app.models.responseModel.facturas_model.responseModel import SuccessModel, ErrorModel 
from ..core.documentos_electronicos_core.exceptions.exceptions_core import InvoiceDataNotExistsException, XSDErrorException, NotaCreditoDataNotExistsException, RetentionDataNotExistsException, GuiaRemisionDataNotExistsException, LiquidacionCompraDataNotExistsException, NotaDebitoDataNotExistsException, NotaDebitoErrorException
from ..core.documentos_electronicos_core.schemas.base_schema import ConsultaDocumento
from ..core.documentos_electronicos_core.schemas.schemas import FacturaSchema, GuiaSchema, LiquidacionCompraSchema, NotaCreditoSchema, RetencionSchema, NotaDebitoSchema

from ..app.controllers.document_controller import DocumentController
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from .bases.base_response import success_response, fails_response
from fastapi.responses import FileResponse
from src.app.middlewares.jwt_bearer import JWTBearer

import os
import logging

document_router = APIRouter()
jwt_bearer = JWTBearer()

TAG = "Facturacion electronica"

config_env = {
    **dotenv_values(".env")
}

@document_router.post("/sign_invoice", tags=[TAG])
async def firma_factura_electronica(invoice: FacturaSchema, background_tasks: BackgroundTasks, user: dict = Depends(jwt_bearer)):
    try:
        documentController = DocumentController()
        response = await documentController.send_invoice(invoice, user, background_tasks)
        return success_response(response)
    except InvoiceDataNotExistsException as e:
        logging.error(e.detail)
        return fails_response(e)
    except Exception as e:
        logging.error(e)
        return fails_response(e) #HTTPException(status_code=500, detail={"message": "Ocurrió un error al firmar el xml"})
    
@document_router.post("/envio_factura_sap", tags=[TAG], summary="Enviar factura desde SAP", 
                        description="Envía una factura electrónica desde SAP para su procesamiento.",
                        response_model=SuccessModel,
                        responses={
                            200: {"description": "Factura enviada correctamente", "model": SuccessModel},
                            400: {"description": "Error en los datos de la factura", "model": ErrorModel},
                            500: {"description": "Error interno del servidor", "model": ErrorModel},
                        })
async def envio_factura_sap(invoice: FacturaSchema, background_tasks: BackgroundTasks, user: dict = Depends(jwt_bearer)):
    try:
        documentController = DocumentController()
        response = await documentController.send_invoice_sap(invoice, user, background_tasks)
        return success_response(response)
    except XSDErrorException as e:
        logging.error(e.detail)
        return fails_response(e, 400)
    except InvoiceDataNotExistsException as e:
        logging.error(e.detail)
        return fails_response(e, status_code=400)
    except Exception as e:
        logging.error(e)
        return fails_response(e)

@document_router.post("/sign_notacredito_sap", tags=[TAG], summary="Enviar nota de crédito")
async def firma_nota_credito(nota_credito: NotaCreditoSchema, background_tasks: BackgroundTasks, user: dict = Depends(jwt_bearer)):
    try:
        documentController = DocumentController()
        response = await documentController.send_nota_credito_sap(nota_credito, user, background_tasks)
        return success_response(response)
    except XSDErrorException as e:
        logging.error(e.detail)
        return fails_response(e, 400)
    except NotaCreditoDataNotExistsException as e:
        logging.error(e.detail)
        return fails_response(e.detail)
    except Exception as e:
        logging.error(e)
        return fails_response(e)
    
@document_router.post("/envio_retention_sap", tags=[TAG])
async def firma_retencion(retencion: RetencionSchema, background_tasks: BackgroundTasks, user: dict = Depends(jwt_bearer)):
    try:
        documentController = DocumentController()
        response = await documentController.send_retention(retencion, user, background_tasks)
        return success_response(response)
    except XSDErrorException as e:
        logging.error(e.detail)
        return fails_response(e, 400)
    except RetentionDataNotExistsException as e:
        logging.error(e)
        return fails_response(e)
    except Exception as e:
        logging.error(e)
        return fails_response(e)
    
@document_router.post("/enviar_guiaremision_sap", tags=[TAG])
async def enviar_guiaremision(guiaremision: GuiaSchema, background_tasks: BackgroundTasks, user: dict = Depends(jwt_bearer)):
    try:
        documentController = DocumentController()
        response = await documentController.enviar_guiaRemision(guiaremision, user, background_tasks)
        return success_response(response)
    except XSDErrorException as e:
        logging.error(e.detail)
        return fails_response(e, 400)
    except GuiaRemisionDataNotExistsException as e:
        logging.error(e)
        return fails_response(e)
    except Exception as e:
        logging.error(e)
        return fails_response(e)
    
@document_router.post("/enviar_liquidacionCompra_sap", tags=[TAG], summary="Enviar liquidacion de compra",
                        description="Envía una liquidacion de compra desde SAP para su procesamiento.") #Refactorizar
async def enviar_liquidacion_compra(liquidacionCompra: LiquidacionCompraSchema, background_tasks: BackgroundTasks, user: dict = Depends(jwt_bearer)):
    try:
        documentController = DocumentController()
        response = await documentController.enviar_liquidacioncompra(liquidacionCompra, user, background_tasks)
        return success_response(response)
    except XSDErrorException as e:
        logging.error(e.detail)
        return fails_response(e, 400)
    except LiquidacionCompraDataNotExistsException as e:
        logging.error(e)
        return fails_response(e)
    except Exception as e:
        logging.error(e)
        return fails_response(e)
    
@document_router.post("/enviar_notadebito_sap", tags=[TAG], summary="Enviar Nota de Debito",
                        description="Envía una Nota de Debito desde SAP para su procesamiento.") #Refactorizar
async def enviar_notaDebito(notadebito: NotaDebitoSchema, background_tasks: BackgroundTasks, user: dict = Depends(jwt_bearer)):
    try:
        documentController = DocumentController()
        response = await documentController.enviar_notadebito(notadebito, user, background_tasks)
        return success_response(response)
    except XSDErrorException as e:
        logging.error(e.detail)
        return fails_response(e, 400)
    except NotaDebitoDataNotExistsException as e:
        logging.error(e)
        return fails_response(e)
    except Exception as e:
        logging.error(e)
        return fails_response(e)
    
@document_router.post("/consultar_estado", tags=[TAG], summary="Consultar estado de factura",
                        description="Consulta el estado de una factura electrónica en el SRI.")
async def consultar_estado_factura(consulta: ConsultaDocumento, user: dict = Depends(jwt_bearer)):
    try:
        documentController = DocumentController()
        response = await documentController.consultar_estado_factura(consulta, user)
        return success_response(response)
    except Exception as e:
        logging.error(e)
        return fails_response(e)

@document_router.get("/downloadxml/{carpeta}/{ruc}/{file_name}", tags=[TAG], response_class=FileResponse)
async def download_file(file_name: str, ruc: str, carpeta: str):
    file_path = config_env['DIR_BASE'] + f'/{carpeta}/{ruc}/{file_name}.xml'
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(file_path, media_type='application/xml', filename=f"{file_name}.xml")

@document_router.get("/viewpdf/{carpeta}/{ruc}/{file_name}", tags=[TAG], response_class=FileResponse)
async def view_pdf(file_name: str, ruc: str, carpeta: str):
    file_path = config_env['DIR_BASE'] + f'/{carpeta}/{ruc}/{file_name}.pdf'
    if not os.path.exists(file_path):
        logging.error("Archivo no encontrado")
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(
        file_path, 
        media_type='application/pdf', 
        filename=f"{file_name}.pdf", 
        headers={"Content-Disposition": "inline; filename=" + f"{file_name}.pdf"}
    )