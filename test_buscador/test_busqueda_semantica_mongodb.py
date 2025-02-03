import pymongo
import nltk
import requests
import dspy
from nltk.tokenize import sent_tokenize

# Descarga del recurso de tokenización (solo la primera vez)
nltk.download('punkt')
nltk.download('punkt_tab')

# --- Intentamos importar InMemoryIndex desde dspy ---
try:
    # Se intenta importar desde dspy.indices (asegúrate de tener dspy instalado)
    from dspy.index import InMemoryIndex
    print("Se está utilizando InMemoryIndex de dspy.indices.")
except ImportError:
    print("No se encontró InMemoryIndex en dspy.indices; se usará una implementación personalizada.")
    from sentence_transformers import SentenceTransformer
    import torch

    class InMemoryIndex:
        def __init__(self, model_name="all-MiniLM-L6-v2"):
            # Crea el modelo de embeddings
            self.model = SentenceTransformer(model_name)
            # Si CUDA está disponible, mueve el modelo a GPU
            if torch.cuda.is_available():
                self.model = self.model.to("cuda")
                print("Modelo movido a CUDA.")
            else:
                print("CUDA no disponible, usando CPU.")
            self.entries = []  # Lista para almacenar cada entrada indexada

        def add(self, text, metadata):
            # Calcula el embedding del texto y lo asocia con sus metadatos.
            # Como el modelo está en el dispositivo correcto, el embedding se calculará en GPU si es posible.
            embedding = self.model.encode(text, convert_to_tensor=True)
            self.entries.append({
                "text": text,
                "metadata": metadata,
                "embedding": embedding
            })

        def search(self, query, top_k=3):
            # Calcula el embedding de la consulta en el mismo dispositivo que el modelo.
            query_embedding = self.model.encode(query, convert_to_tensor=True)
            results = []
            # Compara la similitud coseno entre la consulta y cada embedding indexado.
            for entry in self.entries:
                # Ambos tensores (query_embedding y entry["embedding"]) estarán en el mismo dispositivo.
                sim = torch.nn.functional.cosine_similarity(query_embedding, entry["embedding"], dim=0)
                results.append((sim.item(), entry))
            # Ordena los resultados de mayor a menor similitud.
            results.sort(key=lambda x: x[0], reverse=True)
            top_results = []
            for sim, entry in results[:top_k]:
                top_results.append({
                    "score": sim,
                    "text": entry["text"],
                    "metadata": entry["metadata"]
                })
            return top_results

# --- Función para dividir el texto en secciones ---
def split_text(text):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) < 2:
        return sent_tokenize(text)
    return paragraphs

# --- Función para llamar a la API local de GPT4All ---
def generate_with_gpt_api(section_text, query):
    """
    Llama al endpoint de la API local (http://localhost:4891/v1/chat/completions)
    enviando un prompt que, a partir del texto de referencia (section_text),
    extrae el párrafo o capítulo que contenga la referencia indicada en 'query'.
    Si no se encuentra la referencia, la respuesta deberá indicarlo.
    """
    api_url = "http://localhost:4891/v1/chat/completions"
    payload = {
        "model": "Llama 3.1 8B Instruct 128k",
        "messages": [
            {
                "role": "system",
                "content": f"Utiliza el siguiente texto como referencia:\n\n{section_text}"
            },
            {
                "role": "user",
                "content": (
                    f"Extrae el párrafo o capítulo que contenga la referencia a '{query}'. "
                    "Si no se encuentra, responde 'No se encontró la referencia'."
                )
            }
        ],
        "max_tokens": 4000,
        "temperature": 0.7
    }
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error al llamar a la API de GPT4All: {e}")
        return ""

# --- Función principal ---
def main():
    # Conexión a MongoDB
    usuario = 'Admin'
    password = 'sloch1618'
    client = pymongo.MongoClient(f'mongodb://{usuario}:{password}@localhost:27017/')
    db = client['GPT_Local']
    collection = db.resultados_semanticos

    # Crear el índice semántico (usando dspy o la versión personalizada)
    index = InMemoryIndex()

    # Recuperar documentos de la colección y agregar cada sección al índice
    documentos = list(collection.find({}))
    for doc in documentos:
        text = doc.get('texto', '')
        if not text:
            continue
        sections = split_text(text)
        for i, section in enumerate(sections):
            meta = {
                'document_id': str(doc.get('_id')),
                'titulo': doc.get('titulo', 'Sin título'),
                'enlace': doc.get('enlace', ''),
                'section_index': i,
                'section_text': section
            }
            index.add(section, metadata=meta)

    # Solicitar al usuario la consulta semántica
    query = input("Ingrese el término o referencia a buscar: ")

    # Recuperar los 3 resultados con mayor similitud
    resultados = index.search(query, top_k=3)
    if not resultados:
        print("No se encontraron coincidencias en el índice semántico.")
        return

    print("\nResultados refinados:")

    # Para cada resultado, llamar a la API local de GPT4All para refinar la respuesta
    for res in resultados:
        meta = res.get('metadata', {})
        section_text = meta.get('section_text', '')
        titulo = meta.get('titulo', 'Sin título')
        enlace = meta.get('enlace', 'Sin enlace')
        
        respuesta_refinada = generate_with_gpt_api(section_text, query)
        
        print(f"\nDocumento: {titulo}")
        print(f"Enlace: {enlace}")
        print("Referencia extraída:")
        print(respuesta_refinada)
        print("-" * 80)

if __name__ == "__main__":
    main()
