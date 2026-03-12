import random
import os
import logging
import pytz

from datetime import datetime
from dotenv import dotenv_values
from tortoise.transactions import atomic, in_transaction
from jinja2 import Template
from weasyprint import HTML
from decimal import Decimal
from fastapi import BackgroundTasks

from ..schemas.liquidacion_compra_schema import LiquidacionCompra
from ..schemas.base_schema import InfoToSignXml
from ..schemas.respuestas_sri_schema import map_sri_status_to_custom
from ..exceptions.liquidacion_compra_exception import LiquidacionCompraDataNotExistsException, LiquidacionCompraErrorException
from ..services.liquidacion_compra.xmlBuilder import createXml
from ....app.middlewares.audit_middleware import ModelAudit
from ....app.controllers.email_controller import EmailController
from ....core.emails.schemas.email_schema import EmailData
from ....app.models.model import User, LiquidacionCompraModel, Datos_Facturacion
from ....utils.utilsCall import PDFGenerator, DotNetCrystalClient, createAccessKey, validar_xml_con_xsd, createTempXmlFileGeneral, createTempFile, createTempXmlFile1, sign_xml_file, send_xml_to_authorization, send_xml_to_reception

UPLOAD_FOLDER = "src/assets/"

class LiquidacionCompraService():
    def __init__(self, db):
        self.db = db
        self.config = {
            **dotenv_values('.env')
        }

    def _safe_str(self, value, default=""):
        return default if value is None else str(value)

    def _build_liquidacioncompra_render_request(
        self,
        liquidacioncompra: LiquidacionCompra,
        data_facturacion,
        clave_acceso: str,
        fecha_autorizacion: str = None,
        hora_autorizacion: str = None
    ) -> dict:
        fecha_autorizacion = fecha_autorizacion or datetime.now().strftime("%d/%m/%Y")
        hora_autorizacion = hora_autorizacion or datetime.now().strftime("%H:%M:%S")

        # InfoTributaria
        info_tributaria = {
            "ambiente": self._safe_str(liquidacioncompra.infoTributaria.ambiente),
            "tipoEmision": self._safe_str(liquidacioncompra.infoTributaria.tipoEmision),
            "claveAcceso": self._safe_str(clave_acceso),
            "razonSocial": self._safe_str(data_facturacion.razon_social),
            "nombreComercial": self._safe_str(data_facturacion.nombre_comercial or data_facturacion.razon_social),
            "ruc": self._safe_str(data_facturacion.ruc),
            "codDoc": self._safe_str(liquidacioncompra.infoTributaria.codDoc),
            "estab": self._safe_str(liquidacioncompra.infoTributaria.estab),
            "ptoEmi": self._safe_str(liquidacioncompra.infoTributaria.ptoEmi),
            "secuencial": self._safe_str(liquidacioncompra.infoTributaria.secuencial),
            "dirMatriz": self._safe_str(data_facturacion.direccion),
            "diaEmission": self._safe_str(liquidacioncompra.infoTributaria.diaEmission),
            "mesEmission": self._safe_str(liquidacioncompra.infoTributaria.mesEmission),
            "anioEmission": self._safe_str(liquidacioncompra.infoTributaria.anioEmission),
            "fechaAuto": fecha_autorizacion,
            "horaAuto": hora_autorizacion
        }

        # TotalConImpuestos
        total_con_impuestos = []
        for item in (liquidacioncompra.infoLiquidacionCompra.totalConImpuestos or []):
            total_con_impuestos.append({
                "codigo": self._safe_str(item.codigo),
                "codigoPorcentaje": self._safe_str(item.codigoPorcentaje),
                "baseImponible": self._safe_str(item.baseImponible),
                "valor": self._safe_str(item.valor),
                "tarifa": self._safe_str(item.tarifa),
                "descuentoAdicional": self._safe_str(item.descuentoAdicional),
            })

        # Pagos
        pagos = []
        for item in (liquidacioncompra.infoLiquidacionCompra.pagos or []):
            pagos.append({
                "formaPago": self._safe_str(item.formaPago),
                "total": self._safe_str(item.total),
                "plazo": self._safe_str(item.plazo),
                "unidadTiempo": self._safe_str(item.unidadTiempo)
            })

        # Reembolsos
        reembolsos = []
        for reembolso in (liquidacioncompra.infoLiquidacionCompra.reembolsos or []):
            detalle_impuestos = []
            for imp in (reembolso.detalleImpuestos or []):
                detalle_impuestos.append({
                    "codigo": self._safe_str(imp.codigo),
                    "codigoPorcentaje": self._safe_str(imp.codigoPorcentaje),
                    "baseImponibleReembolso": self._safe_str(imp.baseImponibleReembolso),
                    "tarifa": self._safe_str(imp.tarifa),
                    "impuestoReembolso": self._safe_str(imp.impuestoReembolso)
                })

            reembolsos.append({
                "tipoIdentificacionProveedorReembolso": self._safe_str(reembolso.tipoIdentificacionProveedorReembolso),
                "identificacionProveedorReembolso": self._safe_str(reembolso.identificacionProveedorReembolso),
                "codPaisPagoProveedorReembolso": self._safe_str(reembolso.codPaisPagoProveedorReembolso),
                "tipoProveedorReembolso": self._safe_str(reembolso.tipoProveedorReembolso),
                "codDocReembolso": self._safe_str(reembolso.codDocReembolso),
                "estabDocReembolso": self._safe_str(reembolso.estabDocReembolso),
                "ptoEmiDocReembolso": self._safe_str(reembolso.ptoEmiDocReembolso),
                "secuencialDocReembolso": self._safe_str(reembolso.secuencialDocReembolso),
                "fechaEmisionDocReembolso": self._safe_str(reembolso.fechaEmisionDocReembolso),
                "numeroautorizacionDocReemb": self._safe_str(reembolso.numeroautorizacionDocReemb),
                "detalleImpuestos": detalle_impuestos
            })

        # InfoFactura
        infoLiquidacionCompra = {
            "fechaEmision": self._safe_str(liquidacioncompra.infoLiquidacionCompra.fechaEmision),
            "dirEstablecimiento": self._safe_str(liquidacioncompra.infoLiquidacionCompra.dirEstablecimiento),
            "contribuyenteEspecial": self._safe_str(liquidacioncompra.infoLiquidacionCompra.contribuyenteEspecial),
            "obligadoContabilidad": self._safe_str(liquidacioncompra.infoLiquidacionCompra.obligadoContabilidad or data_facturacion.obligado_contabilidad),
            "tipoIdentificacionComprador": self._safe_str(liquidacioncompra.infoLiquidacionCompra.tipoIdentificacionComprador),
            "guiaRemision": self._safe_str(liquidacioncompra.infoLiquidacionCompra.guiaRemision),
            "razonSocialComprador": self._safe_str(liquidacioncompra.infoLiquidacionCompra.razonSocialComprador),
            "identificacionComprador": self._safe_str(liquidacioncompra.infoLiquidacionCompra.identificacionComprador),
            "direccionComprador": self._safe_str(liquidacioncompra.infoLiquidacionCompra.direccionComprador),
            "totalSinImpuestos": self._safe_str(liquidacioncompra.infoLiquidacionCompra.totalSinImpuestos),
            "totalDescuento": self._safe_str(liquidacioncompra.infoLiquidacionCompra.totalDescuento),
            "totalConImpuestos": total_con_impuestos,
            "propina": self._safe_str(liquidacioncompra.infoLiquidacionCompra.propina),
            "importeTotal": self._safe_str(liquidacioncompra.infoLiquidacionCompra.importeTotal),
            "moneda": self._safe_str(liquidacioncompra.infoLiquidacionCompra.moneda),
            "pagos": pagos,
            "valorRetIva": self._safe_str(liquidacioncompra.infoLiquidacionCompra.valorRetIva),
            "valorRetRenta": self._safe_str(liquidacioncompra.infoLiquidacionCompra.valorRetRenta),
            "comercioExterior": self._safe_str(liquidacioncompra.infoLiquidacionCompra.comercioExterior),
            "IncoTermFactura": self._safe_str(liquidacioncompra.infoLiquidacionCompra.IncoTermFactura),
            "lugarIncoTerm": self._safe_str(liquidacioncompra.infoLiquidacionCompra.lugarIncoTerm),
            "paisOrigen": self._safe_str(liquidacioncompra.infoLiquidacionCompra.paisOrigen),
            "puertoEmbarque": self._safe_str(liquidacioncompra.infoLiquidacionCompra.puertoEmbarque),
            "paisDestino": self._safe_str(liquidacioncompra.infoLiquidacionCompra.paisDestino),
            "paisAdquisicion": self._safe_str(liquidacioncompra.infoLiquidacionCompra.paisAdquisicion),
            "incoTermTotalSinImpuestos": self._safe_str(liquidacioncompra.infoLiquidacionCompra.incoTermTotalSinImpuestos),
            "fleteInternacional": self._safe_str(liquidacioncompra.infoLiquidacionCompra.fleteInternacional),
            "seguroInternacional": self._safe_str(liquidacioncompra.infoLiquidacionCompra.seguroInternacional),
            "gastosAduaneros": self._safe_str(liquidacioncompra.infoLiquidacionCompra.gastosAduaneros),
            "gastosTransporteOtros": self._safe_str(liquidacioncompra.infoLiquidacionCompra.gastosTransporteOtros),
            "codDocReembolso": self._safe_str(liquidacioncompra.infoLiquidacionCompra.codDocReembolso),
            "totalComprobantesReembolso": self._safe_str(liquidacioncompra.infoLiquidacionCompra.totalComprobantesReembolso),
            "totalBaseImponibleReembolso": self._safe_str(liquidacioncompra.infoLiquidacionCompra.totalBaseImponibleReembolso),
            "totalImpuestoReembolso": self._safe_str(liquidacioncompra.infoLiquidacionCompra.totalImpuestoReembolso),
            "reembolsos": reembolsos
        }

        # Detalles
        detalles = []
        for det in (liquidacioncompra.detalles or []):
            detalles_adicionales = []
            for add in (det.detallesAdicionales or []):
                detalles_adicionales.append({
                    "nombre": self._safe_str(add.nombre),
                    "valor": self._safe_str(add.valor)
                })

            impuestos = []
            for imp in (det.impuestos or []):
                impuestos.append({
                    "codigo": self._safe_str(imp.codigo),
                    "codigoPorcentaje": self._safe_str(imp.codigoPorcentaje),
                    "baseImponible": self._safe_str(imp.baseImponible),
                    "valor": self._safe_str(imp.valor),
                    "tarifa": self._safe_str(imp.tarifa)
                })

            detalles.append({
                "codigoPrincipal": self._safe_str(det.codigoPrincipal),
                "codigoAuxiliar": self._safe_str(det.codigoAuxiliar),
                "descripcion": self._safe_str(det.descripcion),
                "cantidad": det.cantidad,
                "precioUnitario": self._safe_str(det.precioUnitario),
                "descuento": self._safe_str(det.descuento),
                "precioTotalSinImpuesto": self._safe_str(det.precioTotalSinImpuesto),
                "detallesAdicionales": detalles_adicionales,
                "impuestos": impuestos,
                "unidadMedida": self._safe_str(det.unidadMedida)
            })

        """
        # Retenciones
        retenciones = []
        for ret in (liquidacioncompra.retenciones or []):
            retenciones.append({
                "codigo": self._safe_str(ret.codigo),
                "codigoPorcentaje": self._safe_str(ret.codigoPorcentaje),
                "tarifa": self._safe_str(ret.tarifa),
                "valor": self._safe_str(ret.valor)
            })
        """

        # InfoAdicional
        info_adicional = []
        for item in (liquidacioncompra.infoAdicional or []):
            info_adicional.append({
                "nombre": self._safe_str(item.nombre),
                "valor": self._safe_str(item.valor)
            })

        payload = {
            "infoTributaria": info_tributaria,
            "infoLiquidacionCompra": infoLiquidacionCompra,
            "detalles": detalles,
            "infoAdicional": info_adicional,
            "campoAdicional1": self._safe_str(liquidacioncompra.campoAdicional1 or data_facturacion.ruta_logo or "logo.png"),
            "campoAdicional2": self._safe_str(liquidacioncompra.campoAdicional2 or "LiquidacionCompra.rpt"),
            "LogoPathOverride": None
        }

        return payload

    async def enviar_liquidacion_compra(self, liquidacionCompra: LiquidacionCompra, user_info: ModelAudit, background_tasks: BackgroundTasks):
        try:
            urlReception = self.config["URL_RECEPTION_PRUEBAS"] if liquidacionCompra.infoTributaria.ambiente == "1" else self.config["URL_RECEPTION"]
            urlAuthorization = self.config["URL_AUTHORIZATION_PRUEBAS"] if liquidacionCompra.infoTributaria.ambiente == "1" else self.config["URL_AUTHORIZATION"]

            data_facturacion = await Datos_Facturacion.get_or_none(user = user_info['created_by'])
            if not data_facturacion:
                raise LiquidacionCompraDataNotExistsException(user_info['created_by_name'])
            
            randomNumber = str(random.randint(1,99999999)).zfill(8)
            if liquidacionCompra.infoTributaria.claveAcceso:
                claveAcceso = liquidacionCompra.infoTributaria.claveAcceso
            else:
                claveAcceso = createAccessKey(liquidacionCompra.infoTributaria, randomNumber, data_facturacion)
            liquidacionCompra.infoTributaria.claveAcceso = claveAcceso

            xmlData = createXml(liquidacionCompra, claveAcceso, data_facturacion)
            xmlFileName = str(claveAcceso) + '.xml'
            xmlString = xmlData['xmlString']

            if xmlString is None:
                raise LiquidacionCompraErrorException("Error al crear el XML de liquidación de compra: " + xmlData['error'])

            xmlNoSigned = createTempXmlFile1(xmlString, xmlFileName)
            ruta = self.config['DIR_LIQUIDACION_COMPRA']
            xmlSigned = createTempXmlFileGeneral(xmlString, xmlFileName, data_facturacion.ruc, ruta)

            certificateName = data_facturacion.nombre_firma + '.p12'
            pathSignature = os.path.abspath('src/assets/firmasElectronicas/' + certificateName)

            with open(pathSignature, 'rb') as file:
                digitalSignature = file.read()
                certificateToSign = createTempFile(digitalSignature, certificateName)
            
            passwordP12 = data_facturacion.password_sign
            infoToSignXml = InfoToSignXml(
                pathXmlToSign=xmlNoSigned.name,
                pathXmlSigned=xmlSigned.name,
                pathSignatureP12=certificateToSign.name,
                passwordSignature=passwordP12
            )

            isXmlCreated = sign_xml_file(infoToSignXml)

            xsd_path = self.config['DIR_XSD_LIQUIDACIONCOMPRA']
            xmlSigned.seek(0)
            xml_string_data = xmlSigned.read()
            is_xml_valid = validar_xml_con_xsd(xml_string_data, xsd_path)

            isReceived = await send_xml_to_reception(
                pathXmlSigned=xmlSigned.name,
                urlToReception=urlReception,
            )

            isAuthorized = False
            pathPDF = ""
            if isReceived[0]:
                responseAuthorization = await send_xml_to_authorization(
                    claveAcceso,
                    urlAuthorization
                )

                isAuthorized = responseAuthorization['isValid']

                #PDF documento
                pathPDF = f"{self.config['DIR_LIQUIDACION_COMPRA']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                if isAuthorized:
                    #xml_autorizado = responseAuthorization['xml']
                    #overwrite_xml_file(xml_autorizado, xmlFileName, data_facturacion.ruc, ruta)
                    '''
                    pdfGenerator = PDFGenerator(self.db)
                    pdfGenerator.generar_ride_liquidacioncompra(
                        liquidacionCompra,
                        claveAcceso,
                        data_facturacion,
                        datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
                        datetime.now().strftime("%d/%m/%Y")
                    )
                    '''
                    
                    fecha_auto = datetime.now().strftime("%d/%m/%Y")
                    hora_auto = datetime.now().strftime("%H:%M:%S")

                    payload = self._build_liquidacioncompra_render_request(
                        liquidacioncompra=liquidacionCompra,
                        data_facturacion=data_facturacion,
                        clave_acceso=claveAcceso,
                        fecha_autorizacion=fecha_auto,
                        hora_autorizacion=hora_auto
                    )

                    dotnet = DotNetCrystalClient(self.config['URL_API_PDF'])
                    output_pdf = f"{self.config['DIR_LIQUIDACION_COMPRA']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                    await dotnet.render_liquidacioncompra(payload, output_pdf)

                    listaDatosAdicionales = liquidacionCompra.infoAdicional if liquidacionCompra.infoAdicional else []
                    email = ""

                    for dtAdicional in listaDatosAdicionales:
                        if dtAdicional.nombre in ("Correo", "Email", "email", "correo", "EMAIL", "CORREO"):
                            email += dtAdicional.valor

                    emailData = EmailData(
                        identificacion = liquidacionCompra.infoLiquidacionCompra.identificacionProveedor,
                        usuario = liquidacionCompra.infoLiquidacionCompra.identificacionProveedor,
                        contrasenia = liquidacionCompra.infoLiquidacionCompra.identificacionProveedor,
                        nombre_usuario = liquidacionCompra.infoLiquidacionCompra.identificacionProveedor,
                        email_receptor = email,
                        subject="Liquidacion de Compra - SOLSAP " + liquidacionCompra.infoTributaria.estab + '-' + liquidacionCompra.infoTributaria.ptoEmi + '-' + liquidacionCompra.infoTributaria.secuencial
                    )

                    emailController = EmailController()

                    autorizaciones = responseAuthorization['response_sri']
                    logging.info("Liquidacion de compra autorizada correctamente")
                    if 'autorizaciones' in autorizaciones and 'autorizacion' in autorizaciones['autorizaciones']:
                        autorizacion = autorizaciones['autorizaciones']['autorizacion'][0]
                        mensaje = ""
                        codigo_estado = map_sri_status_to_custom(sri_status=responseAuthorization['status'])
                        id_retencion = await self.crear_registro_liquidacioncompra(liquidacionCompra, claveAcceso, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, 0, mensaje)
                        background_tasks.add_task(emailController.send_mail, emailData, liquidacionCompra, user_info, 'liquidacioncompra', id_documento=id_retencion)
                        return {
                            'result': {
                                'codigo': codigo_estado,
                                'mensaje': responseAuthorization['status'],
                                'claveAcceso': claveAcceso
                            }
                        }
                else:
                    print(responseAuthorization)
                    autorizaciones = responseAuthorization['response_sri']
                    if 'autorizaciones' in autorizaciones and 'autorizacion' in autorizaciones['autorizaciones']:
                        autorizacion = autorizaciones['autorizaciones']['autorizacion'][0]
                        mensaje = autorizacion['mensajes']['mensaje'][0]['mensaje'] if 'mensajes' in autorizacion else ''
                        identificador = autorizacion['mensajes']['mensaje'][0]['identificador'] if 'mensajes' in autorizacion else ''
                        identificador_adicional = autorizacion['mensajes']['mensaje'][0]['informacionAdicional'] if 'mensajes' in autorizacion else ''
                        codigo_estado = map_sri_status_to_custom(sri_status=responseAuthorization['status'], identificador=identificador)
                        id_retencion = await self.crear_registro_liquidacioncompra(liquidacionCompra, claveAcceso, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, identificador, mensaje)
                        return {
                            'result': {
                                'codigo': codigo_estado,
                                'claveAcceso': claveAcceso,
                                'mensaje': identificador + ' - ' + mensaje + ' - ' + identificador_adicional
                            }
                        }
            else:
                identificador = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['identificador'] if 'comprobantes' in isReceived[1] else ''
                codigo_estado = map_sri_status_to_custom(sri_status=isReceived[1]['estado'], identificador=identificador)
                mensaje = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['mensaje'] if 'comprobantes' in isReceived[1] else ''
                identificador_adicional = isReceived[1]['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['informacionAdicional'] if 'comprobantes' in isReceived[1] else ''
                if not identificador_adicional:
                    identificador_adicional = ''
                id_retencion = await self.crear_registro_liquidacioncompra(liquidacionCompra, claveAcceso, user_info, xmlSigned.name, pathPDF, data_facturacion, isReceived[1]['estado'], codigo_estado, identificador, mensaje)
                return {
                        'result': {
                            'codigo': codigo_estado,
                            'claveAcceso': claveAcceso,
                            'mensaje': identificador + ' - ' + mensaje + ' - ' + identificador_adicional
                        }
                    }
        except LiquidacionCompraErrorException as e:
            logging.error(e)
            raise e
        
    @atomic()
    async def crear_registro_liquidacioncompra(self, liquidacionCompra: LiquidacionCompra, claveAcceso: str, user_info: ModelAudit, pathXml: str, pathPDF: str, data_facturacion: Datos_Facturacion, estado: str, estado_sap: str, estado_sri: str, mensaje_sri: str):
        async with in_transaction():
            try:
                usuario = await User.get_or_none(id=user_info['created_by'])
                if not usuario:
                    raise LiquidacionCompraDataNotExistsException('Usuario no encontrado')
                
                numero_liquidacioncompra = f"{liquidacionCompra.infoTributaria.estab}-{liquidacionCompra.infoTributaria.ptoEmi}-{liquidacionCompra.infoTributaria.secuencial}"
                liquidacioncompra_db = await LiquidacionCompraModel.get_or_none(numero_liquidacion=numero_liquidacioncompra, ruc_emisor=data_facturacion.ruc)
                ecuador = pytz.timezone("America/Guayaquil")

                iva_total = Decimal(0.00)
                if liquidacionCompra.infoLiquidacionCompra.totalConImpuestos:
                    for impuesto in liquidacionCompra.infoLiquidacionCompra.totalConImpuestos:
                        iva_total += Decimal(impuesto.valor)

                if liquidacioncompra_db:
                    liquidacioncompra_db.ruc_emisor = data_facturacion.ruc
                    liquidacioncompra_db.ruc_receptor = liquidacionCompra.infoLiquidacionCompra.identificacionProveedor
                    liquidacioncompra_db.clave_acceso = claveAcceso
                    liquidacioncompra_db.numero_autorizacion = liquidacionCompra.infoTributaria.claveAcceso
                    liquidacioncompra_db.numero_liquidacion = numero_liquidacioncompra
                    liquidacioncompra_db.fecha_emision = datetime.now(ecuador)
                    liquidacioncompra_db.fecha_autorizacion = datetime.now(ecuador)
                    liquidacioncompra_db.ruta_xml = pathXml
                    liquidacioncompra_db.ruta_pdf = pathPDF
                    liquidacioncompra_db.estado = estado
                    liquidacioncompra_db.subtotal = Decimal(liquidacionCompra.infoLiquidacionCompra.totalSinImpuestos)
                    liquidacioncompra_db.iva = iva_total
                    liquidacioncompra_db.total = Decimal(liquidacionCompra.infoLiquidacionCompra.importeTotal)
                    liquidacioncompra_db.estado_sap = estado_sap
                    liquidacioncompra_db.estado_sri = estado_sri
                    liquidacioncompra_db.mensaje_sri = mensaje_sri
                    liquidacioncompra_db.updated = datetime.now(ecuador)
                    liquidacioncompra_db.updated_by = user_info['created_by']
                    liquidacioncompra_db.updated_by_name = user_info['created_by_name']
                    await liquidacioncompra_db.save()
                else:
                    liquidacioncompra_db = await LiquidacionCompraModel.create(
                        ruc_emisor=data_facturacion.ruc,
                        ruc_receptor=liquidacionCompra.infoLiquidacionCompra.identificacionProveedor,
                        user=usuario,
                        numero_liquidacion=numero_liquidacioncompra,
                        clave_acceso=claveAcceso,
                        numero_autorizacion=liquidacionCompra.infoTributaria.claveAcceso,
                        fecha_emision=datetime.now(ecuador),
                        fecha_autorizacion=datetime.now(ecuador),
                        ruta_xml=pathXml,
                        ruta_pdf=pathPDF,
                        iva=iva_total,
                        subtotal=Decimal(liquidacionCompra.infoLiquidacionCompra.totalSinImpuestos),
                        total=Decimal(liquidacionCompra.infoLiquidacionCompra.importeTotal),
                        estado=estado,
                        estado_sap=estado_sap,
                        estado_sri=estado_sri,
                        mensaje_sri=mensaje_sri,
                        created = user_info['created'],
                        created_by=user_info['created_by'],
                        created_by_name=user_info['created_by_name'],
                    )

                return liquidacioncompra_db.id

            except Exception as e:
                logging.error(f"Error al crear el registro de liquidación de compra: {str(e)}")
                raise LiquidacionCompraErrorException(f"Error al crear el registro de liquidación de compra: {str(e)}")