import json
import os
import boto3
from reportlab.pdfgen import canvas

# Cliente de S3
s3 = boto3.client('s3')
bucket_name = os.environ['S3_BUCKET_NAME']  # Nombre del bucket de S3 desde las variables de entorno

def generar_pdf(datos):
    """
    Genera un archivo PDF con los datos proporcionados.
    """
    # Ruta temporal para guardar el PDF
    archivo_pdf = "/tmp/boleta.pdf"
    c = canvas.Canvas(archivo_pdf)
    
    # Ejemplo de contenido del PDF
    c.drawString(100, 750, f"Grupo: {datos.get('grupo', 'N/A')}")
    c.drawString(100, 725, f"Usuario: {datos.get('usuario', 'N/A')}")
    c.drawString(100, 700, f"Equipos: {datos.get('equipos', 'N/A')}")
    
    c.save()
    return archivo_pdf

def lambda_handler(event, context):
    """
    Manejador de la función Lambda.
    Recibe un evento con datos JSON, genera un PDF y lo sube a S3.
    """
    try:
        # Cargar los datos del evento
        datos = json.loads(event['body']) if 'body' in event else event
        
        # Generar el archivo PDF
        archivo_pdf = generar_pdf(datos)
        
        # Nombre del archivo en S3
        nombre_archivo_s3 = f"boletas/{datos['usuario']}_{datos['grupo']}.pdf"
        
        # Subir el PDF a S3
        with open(archivo_pdf, 'rb') as pdf:
            s3.put_object(
                Bucket=bucket_name,
                Key=nombre_archivo_s3,
                Body=pdf,
                ContentType='application/pdf',
                ACL='public-read'
            )
        
        # Generar la URL pública del archivo en S3
        url = f"https://{bucket_name}.s3.amazonaws.com/{nombre_archivo_s3}"
        
        return {
            "statusCode": 200,
            "body": json.dumps({"url": url})
        }
    
    except Exception as e:
        print(f"Error al generar o subir el PDF: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Error al generar la boleta PDF."})
        }
