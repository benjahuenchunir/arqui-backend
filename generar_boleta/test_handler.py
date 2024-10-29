import os

os.environ['S3_BUCKET_NAME'] = 'test-bucket'

from handler import generar_pdf

def test_generar_pdf():
    datos = {
        "grupo": "grupo1",
        "usuario": "user1",
        "equipos": "equipo1"
    }
    archivo_pdf = generar_pdf(datos)
    assert os.path.exists(archivo_pdf)

if __name__ == '__main__':
    test_generar_pdf()
