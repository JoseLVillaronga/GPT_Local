import sys
import subprocess
from pymongo import MongoClient
import buscador_internet as busca
import extractor_pdf as pdf_ext
import extractor_html as html_ext

def instalar_paquete(paquete):
    try:
        __import__(paquete)
    except ImportError:
        print(f"Instalando {paquete}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])

# Instalamos sentence-transformers si no está instalado
instalar_paquete("sentence_transformers")
from sentence_transformers import SentenceTransformer

def segment_text(text: str, min_size: int = 2500, chunk_size: int = 5500):
    """
    Segmenta el texto en chunks de tamaño apropiado.
    """
    if len(text) < min_size:
        return []
    
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# Define las credenciales de acceso a la base de datos
usuario = 'Admin'
password = 'sloch1618'

# Define la URL de conexión
client = MongoClient(f'mongodb://{usuario}:{password}@localhost:27017/')

# Seleccionar la base de datos
db = client['GPT_Local']

# Inicializar el modelo de embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Realizar la búsqueda
query = input("Ingrese el texto para buscar en Internet: ")
resultados = busca.buscar(query)

# Procesar cada resultado
for key, value in resultados.get("resultados", {}).items():
    print(f"\nProcesando {key}:")
    print(f"  Título     : {value['titulo']}")
    print(f"  Enlace     : {value['enlace']}")
    print(f"  Descripción: {value['descripcion']}\n")
    
    # Extraer texto según el tipo de documento
    if value['enlace'].endswith('.pdf'):
        texto_completo = pdf_ext.extraer_texto_pdf_markdown(value['enlace'])
    else:
        texto_completo = html_ext.extraer_texto_html_markdown(value['enlace'])
    
    # Segmentar el texto
    chunks = segment_text(texto_completo['texto'])
    
    # Si no hay chunks válidos, continuar con el siguiente resultado
    if not chunks:
        print(f"  Texto demasiado corto, saltando...")
        continue
    
    print(f"  Procesando {len(chunks)} segmentos...")
    
    # Procesar cada chunk
    for i, chunk in enumerate(chunks):
        # Generar embedding
        embedding = model.encode(chunk).tolist()
        
        # Crear documento para MongoDB
        documento = {
            "titulo": value['titulo'],
            "enlace": value['enlace'],
            "descripcion": value['descripcion'],
            "texto": chunk,
            "embedding": embedding,
            "longitud": len(chunk),
            "segmento": i,
            "total_segmentos": len(chunks),
            "consulta_original": query
        }
        
        # Guardar en MongoDB
        db.resultados_semanticos.insert_one(documento)
        print(f"  Guardado segmento {i+1}/{len(chunks)}")

print("\nProceso completado. Todos los resultados han sido guardados en la base de datos.")