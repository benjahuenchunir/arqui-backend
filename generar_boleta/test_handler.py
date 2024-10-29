import os
import unittest
from handler import generar_pdf

class TestGenerarPDF(unittest.TestCase):
    def test_generar_pdf(self):
        # Sample input data
        datos = {
            "grupo": "Grupo A",
            "usuario": "Usuario1",
            "equipos": "Equipo1, Equipo2"
        }
        
        # Call the function
        archivo_pdf = generar_pdf(datos)
        
        # Check if the file path is correct
        self.assertEqual(archivo_pdf, "/tmp/boleta.pdf")
        
        # Check if the file exists
        self.assertTrue(os.path.exists(archivo_pdf))
        
        # Optionally, check the content of the PDF
        # This part can be more complex and may require a PDF parsing library
        
        # Clean up the generated file
        os.remove(archivo_pdf)

if __name__ == '__main__':
    unittest.main()