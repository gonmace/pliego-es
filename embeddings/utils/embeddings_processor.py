import json
import os
import numpy as np
from typing import List, Dict
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from django.conf import settings

# Definir la ruta base para la base de datos vectorial
VECTOR_DB_PATH = os.path.join(settings.BASE_DIR, 'chroma_db')

def listar_embeddings() -> List[Dict]:
    """
    Lista todos los embeddings existentes en la base de datos.
    
    Returns:
        List[Dict]: Lista de documentos con sus metadatos
    """
    try:
        # Verificar si existe el directorio de la base de datos
        if not os.path.exists(VECTOR_DB_PATH):
            print(f"El directorio {VECTOR_DB_PATH} no existe")
            return []
            
        # Inicializar embeddings
        embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002"
        )
        
        # Cargar la base de datos existente
        vectorstore = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=embeddings
        )
        
        # Obtener todos los documentos
        docs = vectorstore.get()
        
        if not docs or not docs['ids']:
            print("No se encontraron documentos en la base de datos")
            return []
            
        print(f"Documentos encontrados: {len(docs['ids'])}")  # Debug log
        
        # Formatear resultados
        resultados = []
        for i, doc in enumerate(docs['ids']):
            try:
                resultados.append({
                    'id': doc,
                    'titulo': docs['metadatas'][i]['titulo'],
                    'descripcion': docs['metadatas'][i]['descripcion'],
                    'nombre_archivo': docs['metadatas'][i]['nombre_archivo']
                })
            except Exception as e:
                print(f"Error al procesar documento {i}: {str(e)}")
                continue
        
        print(f"Resultados formateados: {len(resultados)}")  # Debug log
        return resultados
        
    except Exception as e:
        print(f"Error al listar embeddings: {str(e)}")
        return []

def borrar_embedding(embedding_id: str) -> bool:
    """
    Borra un embedding específico de la base de datos.
    
    Args:
        embedding_id: ID del embedding a borrar
        
    Returns:
        bool: True si se borró correctamente, False en caso contrario
    """
    try:
        # Inicializar embeddings
        embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002"
        )
        
        # Cargar la base de datos existente
        vectorstore = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=embeddings
        )
        
        # Borrar el documento
        vectorstore.delete([embedding_id])
        
        return True
    except Exception as e:
        print(f"Error al borrar embedding: {str(e)}")
        return False

def procesar_embeddings(json_path: str) -> str:
    """
    Procesa los archivos JSON y crea embeddings usando LangChain y ChromaDB.
    
    Args:
        json_path: Ruta al archivo JSON con los datos estructurados
        
    Returns:
        str: Ruta a la base de datos de Chroma
    """
    # Inicializar el modelo de embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002"
    )
    
    # Cargar datos del JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    # Preparar documentos para ChromaDB
    documentos: List[Document] = []
    for item in datos:
        # Crear documento con el texto para embedding y metadatos
        doc = Document(
            page_content=item['texto_para_embedding'],
            metadata={
                'titulo': item['titulo'],
                'descripcion': item['descripcion'],
                'nombre_archivo': item['nombre_archivo']
            }
        )
        documentos.append(doc)
    
    # Crear directorio para la base de datos si no existe
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)
    
    # Crear y persistir la base de datos de vectores
    vectorstore = Chroma.from_documents(
        documents=documentos,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH
    )
    
    # Persistir la base de datos
    vectorstore.persist()
    
    return VECTOR_DB_PATH

def buscar_similares(query: str, n_results: int = 5) -> List[Dict]:
    """
    Busca documentos similares a una consulta.
    
    Args:
        query: Texto de la consulta
        n_results: Número de resultados a retornar
        
    Returns:
        List[Dict]: Lista de documentos similares con sus metadatos
    """
    # Inicializar embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002"
    )
    
    # Cargar la base de datos existente
    vectorstore = Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=embeddings
    )
    
    # Realizar la búsqueda
    docs = vectorstore.similarity_search_with_score(query, k=n_results)
    
    # Formatear resultados
    resultados = []
    for doc, score in docs:
        resultados.append({
            'titulo': doc.metadata['titulo'],
            'descripcion': doc.metadata['descripcion'],
            'nombre_archivo': doc.metadata['nombre_archivo'],
            'similitud': float(score),
            'contenido': doc.page_content
        })
    
    return resultados

def obtener_vector_embedding(embedding_id: str) -> Dict:
    """
    Obtiene el vector de embedding para un documento específico.
    
    Args:
        embedding_id: ID del embedding a consultar
        
    Returns:
        Dict: Diccionario con la información del vector
    """
    try:
        # Inicializar embeddings
        embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002"
        )
        
        # Cargar la base de datos existente
        vectorstore = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=embeddings
        )
        
        # Obtener el documento específico con su embedding
        docs = vectorstore.get(
            ids=[embedding_id],
            include=['embeddings', 'documents', 'metadatas']
        )
        
        # Verificar si tenemos datos válidos
        if docs is None or not isinstance(docs, dict):
            return {'error': 'No se encontraron datos'}
            
        if 'ids' not in docs or not docs['ids']:
            return {'error': 'No se encontró el ID del documento'}
            
        if 'embeddings' not in docs or not docs['embeddings']:
            return {'error': 'No se encontró el vector de embedding'}
            
        if 'metadatas' not in docs or not docs['metadatas']:
            return {'error': 'No se encontraron los metadatos'}
        
        # Obtener el vector y convertirlo a lista
        vector = docs['embeddings'][0]
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()
        elif not isinstance(vector, list):
            vector = list(vector)
            
        return {
            'id': docs['ids'][0],
            'titulo': docs['metadatas'][0]['titulo'],
            'vector': vector,
            'dimensiones': len(vector)
        }
        
    except Exception as e:
        print(f"Error al obtener vector: {str(e)}")
        return {'error': str(e)} 