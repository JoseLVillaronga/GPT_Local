import sys
import subprocess
import numpy as np
from typing import List, Dict, Any
import json

def instalar_paquete(paquete):
    try:
        __import__(paquete)
    except ImportError:
        print(f"Instalando {paquete}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])

# Instalamos dependencias necesarias
instalar_paquete("pymongo")
instalar_paquete("sentence_transformers")
instalar_paquete("numpy")

from sentence_transformers import SentenceTransformer
import pymongo

class SemanticChunkManager:
    def __init__(self, mongodb_uri: str, db_name: str, collection_name: str):
        """
        Inicializa el gestor de chunks semánticos.
        
        :param mongodb_uri: URI de conexión a MongoDB
        :param db_name: Nombre de la base de datos
        :param collection_name: Nombre de la colección
        """
        self.client = pymongo.MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Crear índice para búsqueda por similitud si no existe
        self.collection.create_index([("embedding", pymongo.ASCENDING)])
    
    def segment_text(self, text: str, min_size: int = 2500, chunk_size: int = 5500) -> List[str]:
        """
        Segmenta el texto en chunks de tamaño apropiado.
        
        :param text: Texto a segmentar
        :param min_size: Tamaño mínimo para considerar un texto
        :param chunk_size: Tamaño objetivo para cada chunk
        :return: Lista de chunks de texto
        """
        if len(text) < min_size:
            return []
        
        # Dividir por párrafos primero
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
    
    def store_document(self, text: str, document_name: str):
        """
        Procesa y almacena un documento en chunks.
        
        :param text: Texto del documento
        :param document_name: Nombre del documento
        """
        chunks = self.segment_text(text)
        
        for i, chunk in enumerate(chunks):
            embedding = self.model.encode(chunk)
            
            # Convertir el embedding a lista para almacenamiento en MongoDB
            embedding_list = embedding.tolist()
            
            doc = {
                "texto": chunk,
                "embedding": embedding_list,
                "longitud": len(chunk),
                "documento_origen": document_name,
                "posicion": i
            }
            
            self.collection.insert_one(doc)
            print(f"Almacenado chunk {i+1}/{len(chunks)} de {document_name}")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Busca chunks relevantes para una consulta.
        
        :param query: Texto de consulta
        :param top_k: Número de resultados a retornar
        :return: Lista de chunks más relevantes
        """
        # Generar embedding de la consulta
        query_embedding = self.model.encode(query).tolist()
        
        # Búsqueda por similitud
        pipeline = [
            {
                "$addFields": {
                    "similarity": {
                        "$reduce": {
                            "input": {"$zip": {"inputs": ["$embedding", query_embedding]}},
                            "initialValue": 0,
                            "in": {"$add": ["$$value", {"$multiply": ["$$this.0", "$$this.1"]}]}
                        }
                    }
                }
            },
            {"$sort": {"similarity": -1}},
            {"$limit": top_k},
            {"$project": {
                "_id": 0,
                "texto": 1,
                "documento_origen": 1,
                "posicion": 1,
                "similarity": 1
            }}
        ]
        
        return list(self.collection.aggregate(pipeline))

def main():
    # Ejemplo de uso
    manager = SemanticChunkManager(
        mongodb_uri="mongodb://Admin:sloch1618@localhost:27017/",
        db_name="GPT_Local",
        collection_name="semantic_chunks"
    )
    
    # Modo interactivo
    while True:
        print("\nOpciones:")
        print("1. Almacenar nuevo documento")
        print("2. Buscar en documentos")
        print("3. Salir")
        
        opcion = input("\nSeleccione una opción (1-3): ")
        
        if opcion == "1":
            nombre = input("Nombre del documento: ")
            print("Ingrese el texto (termine con una línea vacía):")
            lines = []
            while True:
                line = input()
                if line:
                    lines.append(line)
                else:
                    break
            texto = "\n".join(lines)
            manager.store_document(texto, nombre)
            print("Documento almacenado exitosamente")
            
        elif opcion == "2":
            query = input("Ingrese su consulta: ")
            results = manager.search(query)
            print("\nResultados encontrados:")
            for i, result in enumerate(results, 1):
                print(f"\n--- Resultado {i} ---")
                print(f"Documento: {result['documento_origen']}")
                print(f"Posición: {result['posicion']}")
                print(f"Similitud: {result['similarity']:.4f}")
                print("\nTexto:")
                print(result['texto'][:200] + "...")
                
        elif opcion == "3":
            break
        else:
            print("Opción no válida")

if __name__ == "__main__":
    main()
