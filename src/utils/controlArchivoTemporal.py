import os
import tempfile
from dotenv import dotenv_values

VARIABLES_GLOBALES = {
    **dotenv_values('.env')
}

def createTempXmlFile1(xml, fileName):
    # Crea un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=fileName) as temp_file:
        temp_file.write(xml.encode())

    return temp_file

def createTempXmlFile(xml, fileName, ruc):
    # Define la ruta base donde se guardará el archivo
    base_directory = VARIABLES_GLOBALES['DIR_FACTURAS']
    
    # Construye la ruta completa usando el RUC y el nombre del archivo
    directory = os.path.join(base_directory, ruc)
    
    # Asegúrate de que el directorio existe
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Construye la ruta completa del archivo
    file_path = os.path.join(directory, f"{fileName}")

    # Crea el archivo en la ruta especificada y devuélvelo
    # Aquí se utiliza 'open()' para crear un archivo normal, no temporal
    temp_file = open(file_path, 'w')
    temp_file.write(xml)
    temp_file.close()

    # Reabrir el archivo en modo lectura para obtener el objeto de archivo con el atributo .name
    temp_file = open(file_path, 'r')
    
    return temp_file


def createTempFile(file, fileName):
    # Crea un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=fileName) as temp_file:
        temp_file.write(file)

    return temp_file


def removeTempFile(path: str):
    if os.path.exists(path):
        os.remove(path)

def createTempXmlFile_notacredito(xml, fileName, ruc):
    # Define la ruta base donde se guardará el archivo
    base_directory = VARIABLES_GLOBALES['DIR_NOTAS_CREDITO']
    
    # Construye la ruta completa usando el RUC y el nombre del archivo
    directory = os.path.join(base_directory, ruc)
    
    # Asegúrate de que el directorio existe
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Construye la ruta completa del archivo
    file_path = os.path.join(directory, f"{fileName}")

    # Crea el archivo en la ruta especificada y devuélvelo
    # Aquí se utiliza 'open()' para crear un archivo normal, no temporal
    temp_file = open(file_path, 'w')
    temp_file.write(xml)
    temp_file.close()

    # Reabrir el archivo en modo lectura para obtener el objeto de archivo con el atributo .name
    temp_file = open(file_path, 'r')
    
    return temp_file

def createTempXmlFileGeneral(xml, fileName, ruc, ruta):
    # Define la ruta base donde se guardará el archivo
    base_directory = ruta
    
    # Construye la ruta completa usando el RUC y el nombre del archivo
    directory = os.path.join(base_directory, ruc)
    
    # Asegúrate de que el directorio existe
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Construye la ruta completa del archivo
    file_path = os.path.join(directory, f"{fileName}")

    # Crea el archivo en la ruta especificada y devuélvelo
    # Aquí se utiliza 'open()' para crear un archivo normal, no temporal
    temp_file = open(file_path, 'w')
    temp_file.write(xml)
    temp_file.close()

    # Reabrir el archivo en modo lectura para obtener el objeto de archivo con el atributo .name
    temp_file = open(file_path, 'r')
    
    return temp_file

def overwrite_xml_file(xml_content: str, fileName, ruc, ruta) -> str:
    # Define la ruta base donde se guardará el archivo
    base_directory = ruta
    
    # Construye la ruta completa usando el RUC y el nombre del archivo
    directory = os.path.join(base_directory, ruc)
    
    # Asegúrate de que el directorio existe
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Construye la ruta completa del archivo
    file_path = os.path.join(directory, f"{fileName}")

    # Escribe el nuevo contenido (sobrescribe si ya existe)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(xml_content)

    return file_path