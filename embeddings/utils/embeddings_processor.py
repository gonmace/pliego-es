import json
import os
import numpy as np
from typing import List, Dict
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from django.conf import settings

from rich.console import Console
console = Console()

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
            console.print(f"[yellow]El directorio {VECTOR_DB_PATH} no existe[/yellow]")
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
            console.print("[yellow]No se encontraron documentos en la base de datos[/yellow]")
            return []
            
        console.print(f"[green]Documentos encontrados: {len(docs['ids'])}[/green]")
        
        # Formatear resultados
        resultados = []
        for i, doc in enumerate(docs['ids']):
            try:
                metadata = docs['metadatas'][i]
                resultados.append({
                    'id': doc,
                    'titulo': metadata.get('titulo', 'Sin título'),
                    'descripcion': metadata.get('descripcion', 'Sin descripción'),
                    'nombre_archivo': metadata.get('nombre_archivo', 'Sin nombre de archivo')
                })
            except Exception as e:
                console.print(f"[red]Error al procesar documento {i}: {str(e)}[/red]")
                continue
        
        console.print(f"[green]Resultados formateados: {len(resultados)}[/green]")
        return resultados
        
    except Exception as e:
        console.print(f"[red]Error al listar embeddings: {str(e)}[/red]")
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
        console.print(f"[red]Error al borrar embedding: {str(e)}[/red]")
        return False

def procesar_embeddings(json_path: str) -> str:
    """
    Procesa los archivos JSON y crea embeddings usando LangChain y ChromaDB.
    
    Args:
        json_path: Ruta al archivo JSON con los datos estructurados
        
    Returns:
        str: Ruta a la base de datos de Chroma
    """
    try:
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
            # Validar que los campos requeridos existan
            if not all(key in item for key in ['texto_para_embedding', 'titulo', 'nombre_archivo']):
                console.print(f"[red]Error: Faltan campos requeridos en el documento: {item}[/red]")
                continue
                
            # Crear documento con el texto para embedding y metadatos
            doc = Document(
                page_content=item['texto_para_embedding'],
                metadata={
                    'titulo': item['titulo'],
                    'nombre_archivo': item['nombre_archivo'],
                    'descripcion': item.get('descripcion', '')  # Campo opcional
                }
            )
            documentos.append(doc)
        
        if not documentos:
            console.print("[red]No se pudieron procesar documentos válidos[/red]")
            return ""
            
        console.print(f"[green]Procesando {len(documentos)} documentos...[/green]")
        
        # Crear directorio para la base de datos si no existe
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        
        # Crear la base de datos de vectores (la persistencia es automática)
        vectorstore = Chroma.from_documents(
            documents=documentos,
            embedding=embeddings,
            persist_directory=VECTOR_DB_PATH
        )
        
        console.print("[green]Embeddings creados exitosamente[/green]")
        return VECTOR_DB_PATH
        
    except Exception as e:
        console.print(f"[red]Error al procesar embeddings: {str(e)}[/red]")
        return ""

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
        console.print(f"[red]Error al obtener vector: {str(e)}[/red]")
        return {'error': str(e)} 