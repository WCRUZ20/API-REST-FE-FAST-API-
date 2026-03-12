from lxml import etree
import os

from ..core.documentos_electronicos_core.exceptions.xsd_exception import XSDErrorException

def validar_xml_con_xsd(xml_str: str, xsd_path: str) -> bool:
    try:
        # Cargar el esquema XSD
        with open(xsd_path, 'rb') as xsd_file:
            schema_doc = etree.XML(xsd_file.read())
            schema = etree.XMLSchema(schema_doc)

        # Parsear el XML
        xml_doc = etree.fromstring(xml_str.encode('utf-8'))

        # Validar
        schema.assertValid(xml_doc)
        return True
    except etree.DocumentInvalid as e:
        raise XSDErrorException(f"XML inválido según el XSD: {e}")
    except Exception as e:
        raise XSDErrorException(f"Error al validar XML: {e}")
