from lxml import etree

from .....app.models.model import Datos_Facturacion
from ...schemas.notadebito_schema import NotaDebito

def createXml(info: NotaDebito, accessKey: str, data_facturacion: Datos_Facturacion):
    fecha_emision_notadebito = f"{info.infoTributaria.diaEmission}/{info.infoTributaria.mesEmission}/{info.infoTributaria.anioEmission}"
    try:
        root = etree.Element('notaDebito', attrib={
            'id': 'comprobante',
            'version': '1.0.0'
        })

        # infoTributaria
        infoTributaria = etree.SubElement(root, 'infoTributaria')
        etree.SubElement(infoTributaria, 'ambiente').text = info.infoTributaria.ambiente
        etree.SubElement(infoTributaria, 'tipoEmision').text = info.infoTributaria.tipoEmision
        etree.SubElement(infoTributaria, 'razonSocial').text = data_facturacion.razon_social
        etree.SubElement(infoTributaria, 'nombreComercial').text = data_facturacion.nombre_comercial
        etree.SubElement(infoTributaria, 'ruc').text = data_facturacion.ruc
        etree.SubElement(infoTributaria, 'claveAcceso').text = accessKey
        etree.SubElement(infoTributaria, 'codDoc').text = info.infoTributaria.codDoc
        etree.SubElement(infoTributaria, 'estab').text = info.infoTributaria.estab
        etree.SubElement(infoTributaria, 'ptoEmi').text = info.infoTributaria.ptoEmi
        etree.SubElement(infoTributaria, 'secuencial').text = info.infoTributaria.secuencial
        etree.SubElement(infoTributaria, 'dirMatriz').text = data_facturacion.direccion

        # infoCompRetencion
        infoNotaDebito = etree.SubElement(root, 'infoNotaDebito')
        etree.SubElement(infoNotaDebito, 'fechaEmision').text = fecha_emision_notadebito
        etree.SubElement(infoNotaDebito, 'dirEstablecimiento').text = info.infoNotaDebito.dirEstablecimiento
        etree.SubElement(infoNotaDebito, 'tipoIdentificacionComprador').text = info.infoNotaDebito.tipoIdentificacionComprador
        etree.SubElement(infoNotaDebito, 'razonSocialComprador').text = info.infoNotaDebito.razonSocialComprador
        etree.SubElement(infoNotaDebito, 'identificacionComprador').text = info.infoNotaDebito.identificacionComprador
        if info.infoNotaDebito.contribuyenteEspecial:
            etree.SubElement(infoNotaDebito, 'contribuyenteEspecial').text = info.infoNotaDebito.contribuyenteEspecial
        etree.SubElement(infoNotaDebito, 'obligadoContabilidad').text = data_facturacion.obligado_contabilidad
        etree.SubElement(infoNotaDebito, 'codDocModificado').text = info.infoNotaDebito.codDocModificado
        etree.SubElement(infoNotaDebito, 'numDocModificado').text = info.infoNotaDebito.numDocModificado
        etree.SubElement(infoNotaDebito, 'fechaEmisionDocSustento').text = info.infoNotaDebito.fechaEmisionDocSustento
        etree.SubElement(infoNotaDebito, 'totalSinImpuestos').text = info.infoNotaDebito.totalSinImpuestos
        
        impuestos = etree.SubElement(infoNotaDebito, 'impuestos')
        for totalImpuesto in info.infoNotaDebito.impuestos: 
            impuesto = etree.SubElement(impuestos, 'impuesto')
            etree.SubElement(impuesto, 'codigo').text = totalImpuesto.codigo
            etree.SubElement(impuesto, 'codigoPorcentaje').text = totalImpuesto.codigoPorcentaje
            etree.SubElement(impuesto, 'tarifa').text = totalImpuesto.tarifa
            etree.SubElement(impuesto, 'baseImponible').text = totalImpuesto.baseImponible
            etree.SubElement(impuesto, 'valor').text = totalImpuesto.valor
        
        etree.SubElement(infoNotaDebito, 'valorTotal').text = info.infoNotaDebito.valorTotal

        #Pagos
        pagos = etree.SubElement(infoNotaDebito, 'pagos')
        for _pago in info.infoNotaDebito.pagos:
            pago = etree.SubElement(pagos, 'pago')
            etree.SubElement(pago, 'formaPago').text = _pago.formaPago
            etree.SubElement(pago, 'total').text = _pago.total
            if _pago.plazo:
                etree.SubElement(pago, 'plazo').text = _pago.plazo
            if _pago.unidadTiempo:
                etree.SubElement(pago, 'unidadTiempo').text = _pago.unidadTiempo

        motivos = etree.SubElement(root, 'motivos')
        for motivo_ in info.motivos:
            motivo = etree.SubElement(motivos, 'motivo')
            etree.SubElement(motivo, 'razon').text = motivo_.razon
            etree.SubElement(motivo, 'valor').text = motivo_.valor

        # infoAdicional
        if info.infoAdicional:
            infoAdicional = etree.SubElement(root, 'infoAdicional')
            for campo in info.infoAdicional:
                campoAdicional = etree.SubElement(infoAdicional, 'campoAdicional', attrib={'nombre': campo.nombre})
                campoAdicional.text = campo.valor

        xml_string = etree.tostring(root, pretty_print=True).decode('utf-8')

        return {
            'xmlFile': root,
            'xmlString': xml_string
        }

    except Exception as e:
        print('Error al generar el XML de retención:', str(e))
        return {
            'xmlFile': None,
            'xmlString': None,
            'error': str(e)
        }