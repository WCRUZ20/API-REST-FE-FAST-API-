# Implementar API
1. Clonar repositorio desde `https://github.com/SOLSAP/FACTURACION_ELECTRONICA_SRI.git`
2. Crear el ambiente para instalar las dependencias necesarias con el comando `py -m venv nombreAmbiente`
3. Activar ambiente con `nombreAmbiente\Scripts\activate`
4. Ejecutar comando `pip install -r requirements.txt`, este comando instalará todas las dependencias
5. Levantar API con `uvicorn main:app --reload`