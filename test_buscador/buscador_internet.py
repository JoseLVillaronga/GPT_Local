import sys
import subprocess

def instalar_paquete(paquete):
    """
    Instala un paquete mediante pip si no está ya instalado.
    """
    try:
        __import__(paquete)
    except ImportError:
        print(f"Instalando el paquete '{paquete}'...")
        subprocess.check_call(["python", "-m", "pip", "install", paquete])

# Aseguramos que duckduckgo_search esté instalado
instalar_paquete("duckduckgo_search")

# Importamos la clase DDGS (la interfaz actual para realizar búsquedas)
from duckduckgo_search import DDGS

def buscar(consulta, max_resultados=5):
    """
    Realiza una búsqueda en Internet utilizando DuckDuckGo y devuelve los resultados en un diccionario.
    
    :param consulta: Texto a buscar.
    :param max_resultados: Número máximo de resultados a obtener.
    :return: Diccionario con la consulta y los resultados.
    
    Ejemplo de resultado:
    {
        "consulta": "python scraping",
        "resultados": {
            "resultado_1": {
                "titulo": "Título 1",
                "enlace": "http://...",
                "descripcion": "Descripción 1"
            },
            "resultado_2": {
                "titulo": "Título 2",
                "enlace": "http://...",
                "descripcion": "Descripción 2"
            },
            ...
        }
    }
    """
    try:
        with DDGS() as ddgs:
            resultados_generador = ddgs.text(consulta, max_results=max_resultados)
            resultados_lista = list(resultados_generador)
    except Exception as e:
        print(f"Ocurrió un error durante la búsqueda: {e}")
        return {"consulta": consulta, "resultados": {}}
    
    resultados_dict = {}
    for i, res in enumerate(resultados_lista, start=1):
        resultados_dict[f"resultado_{i}"] = {
            "titulo": res.get("title", "Sin título"),
            "enlace": res.get("href", "Sin enlace"),
            "descripcion": res.get("body", "Sin descripción")
        }
    
    return {"consulta": consulta, "resultados": resultados_dict}

if __name__ == "__main__":
    # Modo interactivo: se pide al usuario el texto de búsqueda y se muestran los resultados en consola.
    consulta_usuario = input("Ingrese el texto para buscar en Internet: ")
    resultados = buscar(consulta_usuario)
    print("\nResultados de la búsqueda:")
    for key, value in resultados.get("resultados", {}).items():
        print(f"{key}:")
        print(f"  Título     : {value['titulo']}")
        print(f"  Enlace     : {value['enlace']}")
        print(f"  Descripción: {value['descripcion']}\n")
