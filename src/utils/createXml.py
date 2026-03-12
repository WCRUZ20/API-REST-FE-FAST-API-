import json
import xmltodict
from lxml import etree
from ..core.documentos_electronicos_core.schemas.invoice_schema import Invoice
from ..core.documentos_electronicos_core.schemas.nota_credito_schema import NotaCredito
from ..app.models.datos_facturacion import Datos_Facturacion

def jsonToXml(json_str):
    data = json.loads(json_str)

    xml_str = xmltodict.unparse(data)

    return xml_str

def createXml(info: Invoice, accessKeyInvoice: str, data_facturacion: Datos_Facturacion):
    fecha_emision_factura = str(
            info.infoTributaria.diaEmission
        ) + '/' + str(
            info.infoTributaria.mesEmission
        ) + '/' + str(
            info.infoTributaria.anioEmission)
    try:
        print('dataaaa:', data_facturacion.nombre_comercial)
        root = etree.Element('factura', attrib={
                'id': 'comprobante', 'version':'1.0.0'
            })
        infoTributaria = etree.SubElement(root, 'infoTributaria')
        ambiente = etree.SubElement(infoTributaria, 'ambiente')
        ambiente.text = ''.join(info.infoTributaria.ambiente)
        tipoEmision = etree.SubElement(infoTributaria, 'tipoEmision')
        tipoEmision.text = ''.join(info.infoTributaria.tipoEmision)
        nombreNegocio = etree.SubElement(infoTributaria, 'razonSocial')
        nombreNegocio.text = ''.join(data_facturacion.razon_social)
        nombreComercial = etree.SubElement(infoTributaria, 'nombreComercial')
        nombreComercial.text = ''.join(data_facturacion.nombre_comercial)
        ruc = etree.SubElement(infoTributaria, 'ruc')
        ruc.text = ''.join(data_facturacion.ruc)
        claveAcceso = etree.SubElement(infoTributaria, 'claveAcceso')
        claveAcceso.text = ''.join(accessKeyInvoice)
        codDoc = etree.SubElement(infoTributaria, 'codDoc')
        codDoc.text = ''.join(info.infoTributaria.codDoc)
        establecimiento = etree.SubElement(infoTributaria, 'estab')
        establecimiento.text = ''.join(info.infoTributaria.estab)
        puntoEmision = etree.SubElement(infoTributaria, 'ptoEmi')
        puntoEmision.text = ''.join(info.infoTributaria.ptoEmi)
        secuencial = etree.SubElement(infoTributaria, 'secuencial')
        secuencial.text = ''.join(info.infoTributaria.secuencial)
        direccionMatriz = etree.SubElement(infoTributaria, 'dirMatriz')
        direccionMatriz.text = ''.join(data_facturacion.direccion)
        # end info tributaria

        infoFactura = etree.SubElement(root, 'infoFactura')
        fechaEmision = etree.SubElement(infoFactura, 'fechaEmision')
        fechaEmision.text = ''.join(fecha_emision_factura)
        dirEstablecimiento = etree.SubElement(
            infoFactura, 'dirEstablecimiento')
        dirEstablecimiento.text = info.infoFactura.dirEstablecimiento    
        obligatedAccounting = etree.SubElement(
            infoFactura, 'obligadoContabilidad')
        obligatedAccounting.text = data_facturacion.obligado_contabilidad
        identificationType = etree.SubElement(
            infoFactura, 'tipoIdentificacionComprador')
        identificationType.text = info.infoFactura.tipoIdentificacionComprador
        razonSocialComprador = etree.SubElement(
            infoFactura, 'razonSocialComprador')
        razonSocialComprador.text = info.infoFactura.razonSocialComprador
        customerDni = etree.SubElement(
            infoFactura, 'identificacionComprador')
        customerDni.text = info.infoFactura.identificacionComprador
        if info.infoFactura.direccionComprador != '':
            customerAddress = etree.SubElement(
                infoFactura, 'direccionComprador')
            customerAddress.text = info.infoFactura.direccionComprador
        totalSinImpuestos = etree.SubElement(infoFactura, 'totalSinImpuestos')
        totalSinImpuestos.text = info.infoFactura.totalSinImpuestos
        totalDescuento = etree.SubElement(infoFactura, 'totalDescuento')
        totalDescuento.text = info.infoFactura.totalDescuento

        totalConImpuestos = etree.SubElement(infoFactura, 'totalConImpuestos')
        for tax in info.infoFactura.totalConImpuestos:
            totalTax = etree.SubElement(totalConImpuestos, 'totalImpuesto')
            totalTaxCode = etree.SubElement(totalTax, 'codigo')
            totalTaxCode.text = tax.codigo
            percentageCode = etree.SubElement(totalTax, 'codigoPorcentaje')
            percentageCode.text = tax.codigoPorcentaje
            taxableBase = etree.SubElement(totalTax, 'baseImponible')
            taxableBase.text = str(tax.baseImponible)
            value = etree.SubElement(totalTax, 'valor')
            value.text = str(tax.valor)

        if info.infoFactura.propina:
            # Si la propina es opcional, se verifica si existe antes de agregarla
            propina = etree.SubElement(infoFactura, 'propina')
            propina.text = str(info.infoFactura.propina)
        importeTotal = etree.SubElement(infoFactura, 'importeTotal')
        importeTotal.text = str(info.infoFactura.importeTotal)
        moneda = etree.SubElement(infoFactura, 'moneda')
        moneda.text = str(info.infoFactura.moneda)
        pagos = etree.SubElement(infoFactura, 'pagos')

        for pago_info in info.infoFactura.pagos:
            pago = etree.SubElement(pagos, 'pago')

            formaPago = etree.SubElement(pago, 'formaPago')
            formaPago.text = str(pago_info.formaPago)

            total = etree.SubElement(pago, 'total')
            total.text = str(pago_info.total)
            if pago_info.plazo:
                plazo = etree.SubElement(pago, 'plazo')
                plazo.text = str(pago_info.plazo)
            if pago_info.unidadTiempo:
                unidadTiempo = etree.SubElement(pago, 'unidadTiempo')
                unidadTiempo.text = str(pago_info.unidadTiempo)

        detalles_ = etree.SubElement(root, 'detalles')
        # fin infoFacturas
        for item in info.detalles:
            detalle = etree.SubElement(detalles_, 'detalle')
            codigoPrincipal = etree.SubElement(detalle, 'codigoPrincipal')
            codigoPrincipal.text = item.codigoPrincipal
            if item.codigoAuxiliar:
                codigoAuxiliar = etree.SubElement(detalle, 'codigoAuxiliar')
                codigoAuxiliar.text = item.codigoAuxiliar
            description = etree.SubElement(detalle, 'descripcion')
            description.text = item.descripcion
            cantidad = etree.SubElement(detalle, 'cantidad')
            cantidad.text = str(item.cantidad)
            precioUnitario = etree.SubElement(detalle, 'precioUnitario')
            precioUnitario.text = str(item.precioUnitario)
            descuento = etree.SubElement(detalle, 'descuento')
            descuento.text = str(item.descuento)
            precioTotalSinImpuesto = etree.SubElement(
                detalle, 'precioTotalSinImpuesto')
            precioTotalSinImpuesto.text = str(item.precioTotalSinImpuesto)
            if item.detallesAdicionales:    
                detallesAdicionales = etree.SubElement(
                    detalle, 'detallesAdicionales')
                for additional in item.detallesAdicionales:
                    campoAdicional = etree.SubElement(
                        detallesAdicionales, 'campoAdicional', attrib={'nombre': additional.nombre})
                    campoAdicional.text = additional.valor
            if item.impuestos:
                impuestos = etree.SubElement(detalle, 'impuestos')
                for tax in item.impuestos:
                    impuesto = etree.SubElement(impuestos, 'impuesto')
                    codigo = etree.SubElement(impuesto, 'codigo')
                    codigo.text = str(tax.codigo)
                    codigoPorcentaje = etree.SubElement(
                        impuesto, 'codigoPorcentaje')
                    codigoPorcentaje.text = tax.codigoPorcentaje
                    tarifa = etree.SubElement(impuesto, 'tarifa')
                    tarifa.text = str(tax.tarifa)
                    baseImponible = etree.SubElement(impuesto, 'baseImponible')
                    baseImponible.text = str(tax.baseImponible)
                    valor = etree.SubElement(impuesto, 'valor')
                    valor.text = str(tax.valor)

        infoAdicional = etree.SubElement(root, 'infoAdicional')
        for item in info.infoAdicional:
            campoAdicional = etree.SubElement(
                infoAdicional, 'campoAdicional', attrib={'nombre': item.nombre})
            campoAdicional.text = item.valor

        xml_string = etree.tostring(root, pretty_print=True).decode('utf-8')
        print(xml_string)
        return {
            'xmlFile': root,
            'xmlString': xml_string
        }
    except Exception as e:
        print('Error: ' + str(e))
        return {
            'xmlFile': None,
            'xmlString': None
        }
    
def createXmlNotaCredito(info: NotaCredito, accessKey: str, data_facturacion: Datos_Facturacion):
    fecha_emision_nota_credito = str(
            info.infoTributaria.diaEmission
        ) + '/' + str(
            info.infoTributaria.mesEmission
        ) + '/' + str(
            info.infoTributaria.anioEmission)

    fecha_Emision_DocSustento = str(info.infoNotaCredito.fechaEmisionDocSustento)

    try:
        root = etree.Element('notaCredito', attrib={
                'id': 'comprobante', 'version':'1.0.0'
            })
        infoTributaria = etree.SubElement(root, 'infoTributaria')
        ambiente = etree.SubElement(infoTributaria, 'ambiente')
        ambiente.text = ''.join(info.infoTributaria.ambiente)
        tipoEmision = etree.SubElement(infoTributaria, 'tipoEmision')
        tipoEmision.text = ''.join(info.infoTributaria.tipoEmision)
        nombreNegocio = etree.SubElement(infoTributaria, 'razonSocial')
        nombreNegocio.text = ''.join(data_facturacion.razon_social)
        nombreComercial = etree.SubElement(infoTributaria, 'nombreComercial')
        nombreComercial.text = ''.join(data_facturacion.nombre_comercial)
        ruc = etree.SubElement(infoTributaria, 'ruc')
        ruc.text = ''.join(data_facturacion.ruc)
        claveAcceso = etree.SubElement(infoTributaria, 'claveAcceso')
        claveAcceso.text = ''.join(accessKey)
        codDoc = etree.SubElement(infoTributaria, 'codDoc')
        codDoc.text = ''.join(info.infoTributaria.codDoc)
        establecimiento = etree.SubElement(infoTributaria, 'estab')
        establecimiento.text = ''.join(info.infoTributaria.estab)
        puntoEmision = etree.SubElement(infoTributaria, 'ptoEmi')
        puntoEmision.text = ''.join(info.infoTributaria.ptoEmi)
        secuencial = etree.SubElement(infoTributaria, 'secuencial')
        secuencial.text = ''.join(info.infoTributaria.secuencial)
        direccionMatriz = etree.SubElement(infoTributaria, 'dirMatriz')
        direccionMatriz.text = ''.join(info.infoTributaria.dirMatriz)
        # end info tributaria

        infoNotaCredito = etree.SubElement(root, 'infoNotaCredito')
        fechaEmision = etree.SubElement(infoNotaCredito, 'fechaEmision')
        fechaEmision.text = ''.join(fecha_emision_nota_credito)

        dirEstablecimiento = etree.SubElement(
            infoNotaCredito, 'dirEstablecimiento')
        dirEstablecimiento.text = info.infoNotaCredito.dirEstablecimiento

        identificationType = etree.SubElement(
            infoNotaCredito, 'tipoIdentificacionComprador')
        identificationType.text = info.infoNotaCredito.tipoIdentificacionComprador

        razonSocialComprador = etree.SubElement(
            infoNotaCredito, 'razonSocialComprador')
        razonSocialComprador.text = info.infoNotaCredito.razonSocialComprador

        customerDni = etree.SubElement(
            infoNotaCredito, 'identificacionComprador')
        customerDni.text = info.infoNotaCredito.identificacionComprador

        obligatedAccounting = etree.SubElement(
            infoNotaCredito, 'obligadoContabilidad')
        obligatedAccounting.text = data_facturacion.obligado_contabilidad

        codDocModificado = etree.SubElement(infoNotaCredito, 'codDocModificado')
        codDocModificado.text = info.infoNotaCredito.codDocModificado

        numDocModificado = etree.SubElement(infoNotaCredito, 'numDocModificado')
        numDocModificado.text = info.infoNotaCredito.numDocModificado

        fechaEmisionDocSustento = etree.SubElement(infoNotaCredito, 'fechaEmisionDocSustento')
        fechaEmisionDocSustento.text = ''.join(fecha_Emision_DocSustento)

        totalSinImpuestos = etree.SubElement(infoNotaCredito, 'totalSinImpuestos')
        totalSinImpuestos.text = info.infoNotaCredito.totalSinImpuestos

        valorModificacion = etree.SubElement(infoNotaCredito, 'valorModificacion')
        valorModificacion.text = info.infoNotaCredito.valorModificacion

        moneda = etree.SubElement(infoNotaCredito, 'moneda')
        moneda.text = info.infoNotaCredito.moneda

        totalConImpuestos = etree.SubElement(infoNotaCredito, 'totalConImpuestos')
        for tax in info.infoNotaCredito.totalConImpuestos:
            totalTax = etree.SubElement(totalConImpuestos, 'totalImpuesto')
            totalTaxCode = etree.SubElement(totalTax, 'codigo')
            totalTaxCode.text = tax.codigo
            percentageCode = etree.SubElement(totalTax, 'codigoPorcentaje')
            percentageCode.text = tax.codigoPorcentaje
            taxableBase = etree.SubElement(totalTax, 'baseImponible')
            taxableBase.text = str(tax.baseImponible)
            value = etree.SubElement(totalTax, 'valor')
            value.text = str(tax.valor)

        motivo = etree.SubElement(infoNotaCredito, 'motivo')
        motivo.text = info.infoNotaCredito.motivo
        # fin infoNotaCredito

        detalles = etree.SubElement(root, 'detalles')
        for item in info.detalles:
            detalle = etree.SubElement(detalles, 'detalle')
            codigoInterno = etree.SubElement(detalle, 'codigoInterno')
            codigoInterno.text = item.codigoInterno
            if item.codigoAdicional:
                codigoAdicional = etree.SubElement(detalle, 'codigoAdicional')
                codigoAdicional.text = item.codigoAdicional
            description = etree.SubElement(detalle, 'descripcion')
            description.text = item.descripcion
            cantidad = etree.SubElement(detalle, 'cantidad')
            cantidad.text = str(item.cantidad)
            precioUnitario = etree.SubElement(detalle, 'precioUnitario')
            precioUnitario.text = str(item.precioUnitario)
            descuento = etree.SubElement(detalle, 'descuento')
            descuento.text = str(item.descuento)
            precioTotalSinImpuesto = etree.SubElement(
                detalle, 'precioTotalSinImpuesto')
            precioTotalSinImpuesto.text = str(item.precioTotalSinImpuesto)

            if item.detallesAdicionales:    
                detallesAdicionales = etree.SubElement(
                    detalle, 'detallesAdicionales')
                for additional in item.detallesAdicionales:
                    campoAdicional = etree.SubElement(
                        detallesAdicionales, 'detAdicional', attrib={'nombre': additional.nombre, 'valor': additional.valor})

            impuestos = etree.SubElement(detalle, 'impuestos')
            for impuesto_ in item.impuestos:
                impuesto = etree.SubElement(impuestos, 'impuesto')
                codigo = etree.SubElement(impuesto, 'codigo')
                codigo.text = str(impuesto_.codigo)
                codigoPorcentaje = etree.SubElement(impuesto, 'codigoPorcentaje')
                codigoPorcentaje.text = impuesto_.codigoPorcentaje
                tarifa = etree.SubElement(impuesto, 'tarifa')
                tarifa.text = str(impuesto_.tarifa)
                baseImponible = etree.SubElement(impuesto, 'baseImponible')
                baseImponible.text = str(impuesto_.baseImponible)
                valor = etree.SubElement(impuesto, 'valor')
                valor.text = str(impuesto_.valor)

        infoAdicional = etree.SubElement(root, 'infoAdicional')
        for item in info.infoAdicional:
            campoAdicional = etree.SubElement(
                infoAdicional, 'campoAdicional', attrib={'nombre': item.nombre})
            campoAdicional.text = item.valor
        xml_string = etree.tostring(root, pretty_print=True).decode('utf-8')

        return {
            'xmlFile': root,
            'xmlString': xml_string
        }
    except Exception as e:
        print('Error: ' + str(e))
        return {
            'xmlFile': None,
            'xmlString': None,
            'error': str(e)
        }

def saveXml(xml, pathToSave):
    tree = etree.ElementTree(xml)
    contenido_xml = etree.tostring(
        tree, pretty_print=True, encoding="utf-8").decode()
    with open(pathToSave, "w") as archivo:
        archivo.write(contenido_xml)