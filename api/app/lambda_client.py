import os
import json
import boto3
from fastapi import HTTPException

# Configuración del cliente Lambda
lambda_client = boto3.client(
    "lambda",
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def invocar_generar_boleta(data: dict):
    """
    Invoca la función Lambda que genera un PDF y lo almacena en S3, y devuelve el enlace al PDF.
    """
    try:
        # Llamada a la función Lambda
        response = lambda_client.invoke(
            FunctionName="generar-boleta-dev-generarBoleta",  # Cambia al nombre real de tu Lambda
            InvocationType="RequestResponse",
            Payload=json.dumps(data),
        )
        # Leer el resultado de la respuesta
        result = json.loads(response["Payload"].read())
        print(result)
        url = json.loads(result.get("body", "{}")).get("url")
        if not url:
            raise ValueError("No se pudo obtener la URL del PDF.")
        return url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al invocar Lambda: {str(e)}")
