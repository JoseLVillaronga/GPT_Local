import sys
import subprocess

def instalar_paquete(paquete, nombre_modulo=None):
    """
    Instala un paquete mediante pip si no está ya instalado.
    
    :param paquete: Nombre del paquete para instalar con pip.
    :param nombre_modulo: Nombre del módulo a importar (si es distinto del nombre del paquete).
    """
    nombre_modulo = nombre_modulo or paquete
    try:
        __import__(nombre_modulo)
    except ImportError:
        print(f"Instalando el paquete '{paquete}'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])

# Instalamos las dependencias necesarias
instalar_paquete("requests")
instalar_paquete("PyPDF2", "PyPDF2")

# Importamos los módulos ya instalados
import io
import requests
from PyPDF2 import PdfReader

def extraer_texto_pdf_markdown(url):
    """
    Descarga un documento PDF desde una URL y extrae el texto, 
    preservando la puntuación, los saltos de línea y respetando (en la medida
    de lo posible) ciertos estilos formateables a Markdown. 
    
    Cada página se convierte en una sección Markdown con un encabezado que 
    indica el número de página y se separa del resto del contenido mediante 
    una regla horizontal.
    
    :param url: URL del documento PDF a descargar.
    :return: Diccionario con la URL y el texto extraído en formato Markdown.
             Ejemplo:
             {
                 "url": "http://ejemplo.com/documento.pdf",
                 "texto": "# Documento extraído\n\n## Página 1\n\nTexto extraído...\n\n---\n\n## Página 2\n\nTexto extraído..."
             }
    """
    try:
        # Descarga el archivo PDF
        respuesta = requests.get(url)
        respuesta.raise_for_status()  # Lanza excepción si hay error en la descarga

        # Usamos BytesIO para leer el PDF en memoria
        pdf_bytes = io.BytesIO(respuesta.content)
        lector = PdfReader(pdf_bytes)
        
        texto_markdown = "# Documento extraído\n\n"
        # Iteramos sobre cada página del PDF
        for indice, pagina in enumerate(lector.pages):
            texto = pagina.extract_text()
            if texto:
                # Se incluye un encabezado indicando la página
                texto_markdown += f"## Página {indice + 1}\n\n"
                
                # Si se detectan posibles patrones de estilo, se pueden convertir.
                # Por ejemplo, si una línea parece ser un título (todo en mayúsculas)
                # se puede formatear en negrita. (Esta es una heurística muy básica.)
                lineas = texto.splitlines()
                lineas_formateadas = []
                for linea in lineas:
                    linea_strip = linea.strip()
                    # Heurística: si la línea es corta y está en mayúsculas, se asume título.
                    if len(linea_strip) < 50 and linea_strip.isupper():
                        linea_strip = f"**{linea_strip}**"  # Se pone en negrita
                    lineas_formateadas.append(linea_strip)
                
                texto_formateado = "\n".join(lineas_formateadas)
                texto_markdown += texto_formateado + "\n\n---\n\n"  # Separador de página
        
        return {"url": url, "texto": texto_markdown}
    
    except Exception as e:
        print(f"Error al procesar el PDF: {e}")
        return {"url": url, "texto": ""}

if __name__ == "__main__":
    # Modo interactivo: se pide al usuario la URL del PDF a descargar
    url_usuario = input("Ingrese la URL del documento PDF: ").strip()
    resultado = extraer_texto_pdf_markdown(url_usuario)
    print("\nTexto extraído en formato Markdown:")
    print(resultado["texto"])
