from lxml import etree
from ...schemas.guia_remision_schema import GuiaRemision
from .....app.models.model import Datos_Facturacion

def createXml(info: GuiaRemision, accessKey: str, data_facturacion: Datos_Facturacion):
    try:
        root = etree.Element('guiaRemision', attrib={
            'id': 'comprobante',
            'version': '1.1.0'
        })

        #infoTributaria
        infoTributaria = etree.SubElement(root, 'infoTributaria')
        etree.SubElement(infoTributaria, 'ambiente').text = info.infoTributaria.ambiente
        etree.SubElement(infoTributaria, 'tipoEmision').text = info.infoTributaria.tipoEmision
        etree.SubElement(infoTributaria, 'razonSocial').text = data_facturacion.razon_social
        if data_facturacion.nombre_comercial:
            etree.SubElement(infoTributaria, 'nombreComercial').text = data_facturacion.nombre_comercial
        etree.SubElement(infoTributaria, 'ruc').text = data_facturacion.ruc
        etree.SubElement(infoTributaria, 'claveAcceso').text = accessKey
        etree.SubElement(infoTributaria, 'codDoc').text = info.infoTributaria.codDoc
        etree.SubElement(infoTributaria, 'estab').text = info.infoTributaria.estab
        etree.SubElement(infoTributaria, 'ptoEmi').text = info.infoTributaria.ptoEmi
        etree.SubElement(infoTributaria, 'secuencial').text = info.infoTributaria.secuencial
        etree.SubElement(infoTributaria, 'dirMatriz').text = info.infoTributaria.dirMatriz

        infoGuiaRemision = etree.SubElement(root, 'infoGuiaRemision')
        if info.infoGuiaRemision.dirEstablecimiento:
            etree.SubElement(infoGuiaRemision, 'dirEstablecimiento').text = info.infoGuiaRemision.dirEstablecimiento
        etree.SubElement(infoGuiaRemision, 'dirPartida').text = info.infoGuiaRemision.dirPartida
        etree.SubElement(infoGuiaRemision, 'razonSocialTransportista').text = info.infoGuiaRemision.razonSocialTransportista
        etree.SubElement(infoGuiaRemision, 'tipoIdentificacionTransportista').text = info.infoGuiaRemision.tipoIdentificacionTransportista
        etree.SubElement(infoGuiaRemision, 'rucTransportista').text = info.infoGuiaRemision.rucTransportista
        if info.infoGuiaRemision.rise:
            etree.SubElement(infoGuiaRemision, 'rise').text = info.infoGuiaRemision.rise
        if info.infoGuiaRemision.obligadoContabilidad:
            etree.SubElement(infoGuiaRemision, 'obligadoContabilidad').text = info.infoGuiaRemision.obligadoContabilidad
        if info.infoGuiaRemision.contribuyenteEspecial:
            etree.SubElement(infoGuiaRemision, 'contribuyenteEspecial').text = info.infoGuiaRemision.contribuyenteEspecial
        etree.SubElement(infoGuiaRemision, 'fechaIniTransporte').text = info.infoGuiaRemision.fechaIniTransporte
        etree.SubElement(infoGuiaRemision, 'fechaFinTransporte').text = info.infoGuiaRemision.fechaFinTransporte
        etree.SubElement(infoGuiaRemision, 'placa').text = info.infoGuiaRemision.placa

        #Desinatarios
        destinatarios = etree.SubElement(root, 'destinatarios')
        for destinatario_ in info.destinatarios:
            destinatario = etree.SubElement(destinatarios, 'destinatario')
            etree.SubElement(destinatario, 'identificacionDestinatario').text = destinatario_.identificacionDestinatario
            etree.SubElement(destinatario, 'razonSocialDestinatario').text = destinatario_.razonSocialDestinatario
            etree.SubElement(destinatario, 'dirDestinatario').text = destinatario_.dirDestinatario
            etree.SubElement(destinatario, 'motivoTraslado').text = destinatario_.motivoTraslado
            if destinatario_.docAduaneroUnico:
                etree.SubElement(destinatario, 'docAduaneroUnico').text = destinatario_.docAduaneroUnico
            if destinatario_.codEstabDestino:
                etree.SubElement(destinatario, 'codEstabDestino').text = destinatario_.codEstabDestino
            if destinatario_.ruta:
                etree.SubElement(destinatario, 'ruta').text = destinatario_.ruta
            if destinatario_.codDocSustento:
                etree.SubElement(destinatario, 'codDocSustento').text = destinatario_.codDocSustento
            if destinatario_.numDocSustento:
                etree.SubElement(destinatario, 'numDocSustento').text = destinatario_.numDocSustento
            if destinatario_.numAutDocSustento:
                etree.SubElement(destinatario, 'numAutDocSustento').text = destinatario_.numAutDocSustento
            if destinatario_.fechaEmisionDocSustento:
                etree.SubElement(destinatario, 'fechaEmisionDocSustento').text = destinatario_.fechaEmisionDocSustento
            
            detalles = etree.SubElement(destinatario, 'detalles')
            for detalle_ in destinatario_.detalles:
                detalle = etree.SubElement(detalles, 'detalle')
                if detalle_.codigoInterno:
                    etree.SubElement(detalle, 'codigoInterno').text = detalle_.codigoInterno
                if detalle_.codigoAdicional:
                    etree.SubElement(detalle, 'codigoInterno').text = detalle_.codigoAdicional
                etree.SubElement(detalle, 'descripcion').text = detalle_.descripcion
                etree.SubElement(detalle, 'cantidad').text = str(detalle_.cantidad)
                if detalle_.detallesAdicionales:
                    detallesAdicionales = etree.SubElement(detalle, 'detallesAdicionales')
                    for detAdi  in detalle_.detallesAdicionales:
                        etree.SubElement(detallesAdicionales, 'detAdicional', attrib={'nombre': detAdi.nombre, 'valor': detAdi.valor})

        #infoAdicional
        if info.infoAdicional:
            infoAdicional = etree.SubElement(root, 'infoAdicional')
            for campoAdicional_ in info.infoAdicional:
                campoAdicional = etree.SubElement(infoAdicional, 'campoAdicional', attrib={'nombre': campoAdicional_.nombre})
                campoAdicional.text = campoAdicional_.valor
        
        xml_string = etree.tostring(root, pretty_print=True).decode('utf-8')
        return {
            'xmlFile': root,
            'xmlString': xml_string
        }

    except Exception as e:
        print('Error al generar el XML de guia de remision: ', str(e))
        return {
            'xmlFile': None,
            'xmlString': None,
            'error': str(e)
        }