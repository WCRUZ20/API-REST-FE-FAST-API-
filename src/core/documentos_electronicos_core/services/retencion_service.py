import os
import random
import random as rd
import logging
import pytz
from datetime import datetime
from dotenv import dotenv_values
from fastapi import BackgroundTasks
from tortoise.transactions import atomic, in_transaction

from ..schemas.retention_schema import Retention
from ..schemas.base_schema import InfoToSignXml
from ..schemas.respuestas_sri_schema import map_sri_status_to_custom
from ..services.retenciones.xmlBuilder import createXml
from ..exceptions.retencion_exception import RetentionDataNotExistsException, RetentionErrorException
from ....app.models.model import Datos_Facturacion, User, Factura, RetentionModel
from ....app.middlewares.audit_middleware import ModelAudit
from ....app.controllers.email_controller import EmailController
from ....core.emails.schemas.email_schema import EmailData
from ....utils.utilsCall import PDFGenerator, DotNetCrystalClient, createAccessKey, validar_xml_con_xsd, generar_codigo_barras_base64, createTempXmlFileGeneral, createTempFile, createTempXmlFile1, sign_xml_file, send_xml_to_authorization, send_xml_to_reception


class RetentionService():
    def __init__(self, db):
        self.db = db
        self.config = {
            **dotenv_values('.env'),
        }

    def _safe_str(self, value, default=""):
        return default if value is None else str(value)

    def _build_retencion_render_request(
        self,
        retencion: Retention,
        data_facturacion,
        clave_acceso: str,
        fecha_autorizacion: str = None,
        hora_autorizacion: str = None
    ) -> dict:
        fecha_autorizacion = fecha_autorizacion or datetime.now().strftime("%d/%m/%Y")
        hora_autorizacion = hora_autorizacion or datetime.now().strftime("%H:%M:%S")

        # InfoTributaria
        info_tributaria = {
            "ambiente": self._safe_str(retencion.infoTributaria.ambiente),
            "tipoEmision": self._safe_str(retencion.infoTributaria.tipoEmision),
            "claveAcceso": self._safe_str(clave_acceso),
            "razonSocial": self._safe_str(data_facturacion.razon_social),
            "nombreComercial": self._safe_str(data_facturacion.nombre_comercial or data_facturacion.razon_social),
            "ruc": self._safe_str(data_facturacion.ruc),
            "codDoc": self._safe_str(retencion.infoTributaria.codDoc),
            "estab": self._safe_str(retencion.infoTributaria.estab),
            "ptoEmi": self._safe_str(retencion.infoTributaria.ptoEmi),
            "secuencial": self._safe_str(retencion.infoTributaria.secuencial),
            "dirMatriz": self._safe_str(data_facturacion.direccion),
            "diaEmission": self._safe_str(retencion.infoTributaria.diaEmission),
            "mesEmission": self._safe_str(retencion.infoTributaria.mesEmission),
            "anioEmission": self._safe_str(retencion.infoTributaria.anioEmission),
            "fechaAuto": fecha_autorizacion,
            "horaAuto": hora_autorizacion
        }

        # InfoNotaCredito
        infoCompRetencion = {
            "fechaEmision": self._safe_str(retencion.infoCompRetencion.fechaEmision),
            "dirEstablecimiento": self._safe_str(retencion.infoCompRetencion.dirEstablecimiento),
            "contribuyenteEspecial": self._safe_str(retencion.infoCompRetencion.contribuyenteEspecial),
            "obligadoContabilidad": self._safe_str(retencion.infoCompRetencion.obligadoContabilidad or data_facturacion.obligado_contabilidad),
            "tipoIdentificacionSujetoRetenido": self._safe_str(retencion.infoCompRetencion.tipoIdentificacionSujetoRetenido),
            "tipoSujetoRetenido": self._safe_str(retencion.infoCompRetencion.tipoSujetoRetenido),
            "parteRel": self._safe_str(retencion.infoCompRetencion.parteRel),
            "razonSocialSujetoRetenido": self._safe_str(retencion.infoCompRetencion.razonSocialSujetoRetenido),
            "identificacionSujetoRetenido": self._safe_str(retencion.infoCompRetencion.identificacionSujetoRetenido),
            "periodoFiscal": self._safe_str(retencion.infoCompRetencion.periodoFiscal)
        }

        docsSustento = []
        for docsSustItem in (retencion.docsSustento or []):
            
            # TotalConImpuestos
            impuestosDocSustento = []
            for item in (docsSustItem.impuestosDocSustento or []):
                impuestosDocSustento.append({
                    "codImpuestoDocSustento": self._safe_str(item.codImpuestoDocSustento),
                    "codigoPorcentaje": self._safe_str(item.codigoPorcentaje),
                    "baseImponible": self._safe_str(item.baseImponible),
                    "valor": self._safe_str(item.valorImpuesto),
                    "tarifa": self._safe_str(item.tarifa)
                })

            retenciones = []
            for item in (docsSustItem.retenciones or []):
                dividendos = {
                    "fechaPagoDiv": self._safe_str(item.dividendos.fechaPagoDiv),
                    "imRentaSoc": self._safe_str(item.dividendos.imRentaSoc),
                    "ejerFisUtDiv": self._safe_str(item.dividendos.ejerFisUtDiv)
                }
                retenciones.append({
                    "codigo": self._safe_str(item.codigo),
                    "codigoRetencion": self._safe_str(item.codigoRetencion),
                    "baseImponible": self._safe_str(item.baseImponible),
                    "porcentajeRetener": self._safe_str(item.porcentajeRetener),
                    "valorRetenido": self._safe_str(item.valorRetenido),
                    "dividendos": dividendos
                })

            pagos = []
            for item in (docsSustItem.pagos or []):
                pagos.append({
                    "formaPago": self._safe_str(item.formaPago),
                    "total": self._safe_str(item.total),
                })

            docsSustento.append({
                "codSustento": self._safe_str(docsSustItem.codSustento),
                "codDocSustento": self._safe_str(docsSustItem.codDocSustento),
                "numDocSustento": self._safe_str(docsSustItem.numDocSustento),
                "factura_relacionada": self._safe_str(docsSustItem.factura_relacionada),
                "fechaEmisionDocSustento": self._safe_str(docsSustItem.fechaEmisionDocSustento),
                "fechaRegistroContable": self._safe_str(docsSustItem.fechaRegistroContable),
                "numAutDocSustento": self._safe_str(docsSustItem.numAutDocSustento),
                "pagoLocExt": self._safe_str(docsSustItem.pagoLocExt),
                "tipoRegi": self._safe_str(docsSustItem.tipoRegi),
                "paisEfecPago": self._safe_str(docsSustItem.paisEfecPago),
                "aplicConvDobTrib": self._safe_str(docsSustItem.aplicConvDobTrib),
                "pagExtSujRetNorLeg": self._safe_str(docsSustItem.pagExtSujRetNorLeg),
                "pagRegFis": self._safe_str(docsSustItem.pagRegFis),
                "totalComprobantesReembolso": self._safe_str(docsSustItem.totalComprobantesReembolso),
                "totalBaseImponibleReembolso": self._safe_str(docsSustItem.totalBaseImponibleReembolso),
                "totalSinImpuestos": self._safe_str(docsSustItem.totalSinImpuestos),
                "importeTotal": self._safe_str(docsSustItem.importeTotal),
                "impuestosDocSustento": impuestosDocSustento,
                "retenciones": retenciones,
                "pagos": pagos,
            })     
               
        # InfoAdicional
        info_adicional = []
        for item in (retencion.infoAdicional or []):
            info_adicional.append({
                "nombre": self._safe_str(item.nombre),
                "valor": self._safe_str(item.valor)
            })

        payload = {
            "infoTributaria": info_tributaria,
            "infoCompRetencion": infoCompRetencion,
            "infoAdicional": info_adicional,
            "campoAdicional1": self._safe_str(retencion.campoAdicional1 or data_facturacion.ruta_logo or "logo.png"),
            "campoAdicional2": self._safe_str(retencion.campoAdicional2 or "Retencion.rpt"),
            "LogoPathOverride": None
        }

        return payload
    
    async def process_retention_in_background(self, retention: Retention, urlReception, urlAuthorization, user_info, background_tasks: BackgroundTasks):
        data_facturacion = await Datos_Facturacion.get_or_none(user = user_info['created_by'])
        if not data_facturacion:
            raise RetentionDataNotExistsException(user_info['created_by_name'])
    
        claveAcceso = retention.info.accessKey
        xmlData = createXml(retention, claveAcceso, data_facturacion)
        xmlFileName = str(claveAcceso) + '.xml'

        xmlString = xmlData['xmlString']

        xmlNoSigned = createTempXmlFile1(xmlString, xmlFileName)
        ruta = r'C:/Proyectos/Facturacion/FACTURACION_ELECTRONICA_SRI/retenciones'
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

            if isAuthorized:
                logging.info("Retencion autorizada correctamente")

    async def envio_retencion_sap(self, retencion: Retention, user_info: ModelAudit, background_tasks: BackgroundTasks):
        try:
            urlReception = self.config["URL_RECEPTION_PRUEBAS"] if retencion.infoTributaria.tipoEmision == "1" else self.config["URL_RECEPTION"]
            urlAuthorization = self.config["URL_AUTHORIZATION_PRUEBAS"] if retencion.infoTributaria.tipoEmision == "1" else self.config["URL_AUTHORIZATION"]

            data_facturacion = await Datos_Facturacion.get_or_none(user = user_info['created_by'])
            if not data_facturacion:
                raise RetentionDataNotExistsException(user_info['created_by_name'])
            
            randomNumber = str(random.randint(1,99999999)).zfill(8)

            claveAcceso = ""
            if retencion.infoTributaria.claveAcceso:
                registroRetencion = await RetentionModel.get_or_none(clave_acceso=retencion.infoTributaria.claveAcceso)

                if not registroRetencion:
                    claveAcceso = createAccessKey(retencion.infoTributaria, randomNumber, data_facturacion)
                else:
                    claveAcceso = retencion.infoTributaria.claveAcceso
            else:
                claveAcceso = createAccessKey(retencion.infoTributaria, randomNumber, data_facturacion)

            retencion.infoTributaria.claveAcceso = claveAcceso

            xmlData = createXml(retencion, claveAcceso, data_facturacion)

            xmlFileName = str(claveAcceso) + '.xml'

            xmlString = xmlData['xmlString']

            if xmlString is None:
                raise RetentionErrorException("Error al crear el XML de la retención: " + xmlData['error'])
            
            #create temp files to create xml
            xmlNoSigned = createTempXmlFile1(xmlString, xmlFileName)
            ruta = self.config['DIR_RETENCIONES']
            xmlSigned = createTempXmlFileGeneral(xmlString, xmlFileName, data_facturacion.ruc, ruta)

            #get digital signature
            certificateName = data_facturacion.nombre_firma + '.p12'
            pathSignature = os.path.abspath('src/assets/firmasElectronicas/' + certificateName)
            with open(pathSignature, 'rb') as file:
                digitalSignature = file.read()
                certificateToSign = createTempFile(digitalSignature, certificateName)

            #password p12
            passwordP12 = data_facturacion.password_sign
            infoToSignXml = InfoToSignXml(
                pathXmlToSign=xmlNoSigned.name,
                pathXmlSigned=xmlSigned.name,
                pathSignatureP12=certificateToSign.name,
                passwordSignature=passwordP12
            )

            isXmlCreated = sign_xml_file(infoToSignXml)

            xsd_path = self.config['DIR_XSD_RETENCION']
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

                pathPDF = f"{self.config['DIR_RETENCIONES']}/{data_facturacion.ruc}/{claveAcceso}.pdf"

                if isAuthorized:
                    #pdfGenerator = PDFGenerator(self.db)
                    #pdfGenerator.generar_ride_retencion(retencion, claveAcceso, data_facturacion, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), datetime.now().strftime("%d/%m/%Y"))

                    fecha_auto = datetime.now().strftime("%d/%m/%Y")
                    hora_auto = datetime.now().strftime("%H:%M:%S")

                    payload = self._build_retencion_render_request(
                        retencion=retencion,
                        data_facturacion=data_facturacion,
                        clave_acceso=claveAcceso,
                        fecha_autorizacion=fecha_auto,
                        hora_autorizacion=hora_auto
                    )

                    dotnet = DotNetCrystalClient(self.config['URL_API_PDF'])
                    output_pdf = f"{self.config['DIR_RETENCIONES']}/{data_facturacion.ruc}/{claveAcceso}.pdf"
                    await dotnet.render_retencion(payload, output_pdf)

                    listaDatosAdicionales = retencion.infoAdicional if retencion.infoAdicional else []
                    email = ""

                    for dtAdicional in listaDatosAdicionales:
                        if dtAdicional.nombre in ("Correo", "Email", "email", "correo", "EMAIL", "CORREO"):
                            email += dtAdicional.valor
                    
                    emailData = EmailData(
                        identificacion = retencion.infoCompRetencion.identificacionSujetoRetenido,
                        usuario = retencion.infoCompRetencion.identificacionSujetoRetenido,
                        contrasenia = retencion.infoCompRetencion.identificacionSujetoRetenido,
                        nombre_usuario = retencion.infoCompRetencion.razonSocialSujetoRetenido,
                        email_receptor = email,
                        subject="Comprobante de Retención - SOLSAP " + retencion.infoTributaria.estab + '-' + retencion.infoTributaria.ptoEmi + '-' + retencion.infoTributaria.secuencial
                    )

                    emailController = EmailController()

                    autorizaciones = responseAuthorization['response_sri']
                    if 'autorizaciones' in autorizaciones and 'autorizacion' in autorizaciones['autorizaciones']:
                        autorizacion = autorizaciones['autorizaciones']['autorizacion'][0]
                        mensaje = ""
                        codigo_estado = map_sri_status_to_custom(sri_status=responseAuthorization['status'])
                        id_retencion = await self.crear_registro_retencion(retencion, claveAcceso, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, 0, mensaje)
                        background_tasks.add_task(emailController.send_mail, emailData, retencion, user_info, 'retenciones', id_documento=id_retencion)
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
                        id_retencion = await self.crear_registro_retencion(retencion, claveAcceso, user_info, xmlSigned.name, pathPDF, data_facturacion, responseAuthorization["status"], codigo_estado, identificador, mensaje)
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
                id_retencion = await self.crear_registro_retencion(retencion, claveAcceso, user_info, xmlSigned.name, pathPDF, data_facturacion, isReceived[1]['estado'], codigo_estado, identificador, mensaje)
                return {
                    'result': {
                        'codigo': codigo_estado,
                        'claveAcceso': claveAcceso,
                        'mensaje': identificador + ' - ' + mensaje + ' - ' + identificador_adicional
                    }
                }
        except RetentionDataNotExistsException as e:
            logging.error(e)
            raise e

    @atomic()
    async def crear_registro_retencion(self, retencion: Retention, claveAcceso: str, user_info: ModelAudit, pathXml, pathPdf, data_facturacion, estado, estado_sap, estado_sri, mensaje_sri):
        async with in_transaction():
            try:
                usuario = await User.get_or_none(id=user_info['created_by'])
                if not usuario:
                    raise RetentionDataNotExistsException('Usuario no encontrado')

                numero_factura_related = retencion.docsSustento[0].factura_relacionada if retencion.docsSustento else None
                factura_related = await Factura.get_or_none(numero_factura=numero_factura_related)
                if not factura_related:
                    raise RetentionDataNotExistsException('Factura relacionada no encontrada')
                
                numero_retencion = f"{retencion.infoTributaria.estab}-{retencion.infoTributaria.ptoEmi}-{retencion.infoTributaria.secuencial}"

                compRetencion = await RetentionModel.get_or_none(numero_retencion=numero_retencion, ruc_emisor=data_facturacion.ruc)
                ecuador = pytz.timezone("America/Guayaquil")

                if compRetencion:
                    compRetencion.ruc_emisor = data_facturacion.ruc
                    compRetencion.ruc_receptor = retencion.infoCompRetencion.identificacionSujetoRetenido
                    compRetencion.clave_acceso = claveAcceso
                    compRetencion.numero_autorizacion = retencion.infoTributaria.claveAcceso
                    compRetencion.fecha_emision = datetime.now(ecuador)
                    compRetencion.fecha_autorizacion = datetime.now(ecuador)
                    compRetencion.ruta_xml = pathXml
                    compRetencion.ruta_pdf = pathPdf
                    compRetencion.estado = estado
                    compRetencion.estado_sap = estado_sap
                    compRetencion.estado_sri = estado_sri
                    compRetencion.mensaje_sri = mensaje_sri
                    compRetencion.updated = datetime.now(ecuador)
                    compRetencion.updated_by = user_info['created_by']
                    compRetencion.updated_by_name = user_info['created_by_name']
                    await compRetencion.save()
                else:
                    compRetencion = await RetentionModel.create(
                        ruc_emisor=data_facturacion.ruc,
                        ruc_receptor=retencion.infoCompRetencion.identificacionSujetoRetenido,
                        user=usuario,
                        factura_relacionada=factura_related,
                        numero_retencion=numero_retencion,
                        clave_acceso=claveAcceso,
                        numero_autorizacion=retencion.infoTributaria.claveAcceso,
                        fecha_emision=datetime.now(ecuador),
                        fecha_autorizacion=datetime.now(ecuador),
                        ruta_xml=pathXml,
                        ruta_pdf=pathPdf,
                        estado=estado,
                        estado_sap=estado_sap,
                        estado_sri=estado_sri,
                        mensaje_sri=mensaje_sri,
                        created = user_info['created'],
                        created_by=user_info['created_by'],
                        created_by_name=user_info['created_by_name'],
                    )

                return compRetencion.id

            except Exception as e:
                raise RetentionErrorException(f"Error al crear o actualizar el registro de retención: {str(e)}")
