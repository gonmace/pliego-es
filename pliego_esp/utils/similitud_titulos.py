from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from scipy.spatial.distance import cosine
from django.conf import settings
import os

from rich.console import Console
console = Console()

def calcular_similitud_titulos(titulo_original: str, titulo_sugerido: str) -> dict:
    """
    Calcula la similitud entre los títulos y los documentos en ChromaDB.
    
    Args:
        titulo_original (str): El título original de la especificación
        titulo_sugerido (str): El título sugerido por el sistema
        
    Returns:
        dict: Un diccionario con los resultados de la similitud
    """
    try:
        # Inicializar embeddings
        embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
        )
        
        # Obtener embeddings para ambos títulos
        embedding_original = embeddings.embed_query(titulo_original)
        embedding_sugerido = embeddings.embed_query(titulo_sugerido)
        
        # Si existe una base de datos de vectores, buscar similitudes con documentos existentes
        mejor_score = 0
        mejor_documento = None
        persist_directory = os.path.join(settings.BASE_DIR, 'chroma_db')
        
        if os.path.exists(persist_directory):
            vectorstore = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings
            )
            
            # Obtener todos los documentos con sus embeddings
            data = vectorstore.get(include=["documents", "embeddings", "metadatas"])
            
            for doc_text, vec, metadata in zip(data["documents"], data["embeddings"], data["metadatas"]):
                score_original = 1 - cosine(embedding_original, vec)
                score_sugerido = 1 - cosine(embedding_sugerido, vec)
                score_actual = max(score_original, score_sugerido)
                
                if score_actual > mejor_score:
                    mejor_score = score_actual
                    mejor_documento = {
                        "document": metadata["titulo"],
                        "nombre_archivo": metadata["nombre_archivo"],
                        "categoria": metadata["categoria"],
                        "score_original": round(score_original, 4),
                        "score_sugerido": round(score_sugerido, 4),
                        "mejor_match": "original" if score_original > score_sugerido else "sugerido"
                    }

        return {
            'success': True,
            'ranking': [mejor_documento] if mejor_documento else [],
            'estadisticas': {
                'mejor_score_original': mejor_documento['score_original'] if mejor_documento else 0,
                'mejor_score_sugerido': mejor_documento['score_sugerido'] if mejor_documento else 0,
                'mejor_match': mejor_documento['mejor_match'] if mejor_documento else "ninguno"
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        } 