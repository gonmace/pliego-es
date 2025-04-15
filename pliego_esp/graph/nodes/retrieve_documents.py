from langchain_graph_retriever import GraphRetriever
from graph_retriever.strategies import Eager
from rich.console import Console

from pliego_esp.graph.state import State
from pliego_esp.utils.utils import format_docs

from typing import List, Tuple
from langchain_core.vectorstores import VectorStore

console = Console()

class RetrieveDocuments:
    """
    Clase para recuperar y filtrar documentos utilizando un GraphRetriever.
    
    Esta clase implementa un sistema de recuperación de documentos que:
    1. Utiliza un GraphRetriever para buscar documentos relevantes
    2. Filtra documentos duplicados
    3. Aplica filtros específicos por tipo de documento
    4. Evalúa la similitud de los documentos recuperados
    
    Attributes:
        vectorstore (VectorStore): Almacén de vectores para búsqueda de similitud
        edges (List[Tuple[str, str]]): Lista de relaciones entre documentos
        strategy (Eager): Estrategia de búsqueda para el GraphRetriever
        documento_filter (List[str]): Lista de tipos de documentos a incluir
        umbral_contexto (float): Umbral de similitud para filtrar documentos
        k (int): Número de documentos a recuperar inicialmente
        start_k (int): Número de documentos iniciales para comenzar la búsqueda
        max_depth (int): Profundidad máxima para la búsqueda en el grafo
        graph_retriever (GraphRetriever): Instancia del recuperador de documentos
    """
    
    def __init__(
        self,
        vectorstore: VectorStore,
        edges: List[Tuple[str, str]] = [("id", "ID_Original")],
        strategy: Eager = Eager(k=8, start_k=6, max_depth=1),
        documento_filter: List[str] = ["CODIGO CIVIL (SUBFRAGMENTOS)", "CODIGO PROCESAL CIVIL (SUBFRAGMENTOS)"],
        umbral_contexto: float = 0.5,
        k: int = 8,
        start_k: int = 6,
        max_depth: int = 2
    ):
        """
        Inicializa una nueva instancia de RetrieveDocuments.
        
        Args:
            vectorstore (VectorStore): Almacén de vectores para búsqueda
            edges (List[Tuple[str, str]]): Relaciones entre documentos
            strategy (Eager): Estrategia de búsqueda
            documento_filter (List[str]): Tipos de documentos a incluir
            umbral_contexto (float): Umbral de similitud
            k (int): Número de documentos a recuperar
            start_k (int): Documentos iniciales para búsqueda
            max_depth (int): Profundidad máxima de búsqueda
        """
        self.vectorstore = vectorstore
        self.edges = edges
        self.strategy = strategy
        self.documento_filter = documento_filter
        self.umbral_contexto = umbral_contexto
        self.k = k
        self.start_k = start_k
        self.max_depth = max_depth
        # Inicializar el GraphRetriever con la configuración proporcionada
        self.graph_retriever = GraphRetriever(
            store=self.vectorstore,
            edges=self.edges,
            strategy=self.strategy
        )

    def _filter_duplicate_documents_by_id(self, documents):
        """
        Filtra documentos duplicados basándose en su ID.
        
        Args:
            documents: Lista de documentos a filtrar
            
        Returns:
            List: Lista de documentos únicos
        """
        unique_docs = {}
        for doc in documents:
            if doc.id not in unique_docs:
                unique_docs[doc.id] = doc
        return list(unique_docs.values())

    async def __call__(self, state: State) -> State:
        """
        Procesa el estado actual y recupera documentos relevantes.
        
        Este método implementa el flujo principal de recuperación:
        1. Obtiene la última pregunta del estado
        2. Recupera documentos usando el GraphRetriever
        3. Filtra documentos duplicados
        4. Aplica filtros por tipo de documento y similitud
        5. Actualiza el estado con el contexto encontrado
        
        Args:
            state (State): Estado actual del sistema
            
        Returns:
            State: Estado actualizado con el contexto encontrado
        """
        console.print("---retrieve_documents---", style="bold blue")

        # Obtener la consulta desde el estado
        consulta = state["query"]
                
        console.print(f"Consultas para retriever: {consulta}", style="bold blue")
        
        all_docs = []
        
        for query in consulta:
            # Recuperar documentos usando el GraphRetriever
            retrieved_docs = await self.graph_retriever.ainvoke(
                query
            )
            all_docs.extend(retrieved_docs)
        
        # Filtrar documentos duplicados
        filtered_docs = self._filter_duplicate_documents_by_id(all_docs)
        
        console.print(f"Documentos recuperados: {len(filtered_docs)}", style="blue")
        
        # Filtrar documentos según criterios específicos
        filtered_documents = [
            doc for doc in filtered_docs
            if doc.metadata.get("Documento") in self.documento_filter
            and doc.metadata.get("_similarity_score", 0) > self.umbral_contexto
        ]
        
        # Ordenar documentos por _similarity_score y seleccionar los 8 mejores
        filtered_documents.sort(key=lambda x: x.metadata.get("_similarity_score", 0), reverse=True)
        filtered_documents = filtered_documents[:7]
        
        console.print(f"Documentos finales ya filtrados: {len(filtered_documents)}", style="blue")
        
        # Calcular la similitud máxima
        similarity_scores = [doc.metadata.get("_similarity_score") for doc in filtered_documents]
        max_similarity = max(similarity_scores) if similarity_scores else 0

        console.print(f"Similitud maxima: {max_similarity}", style="blue")
        console.print(f"Umbral: {self.umbral_contexto}", style="blue")

        # Determinar si hay suficiente contexto
        if max_similarity >= self.umbral_contexto:
            console.print("Contexto valido OK", style="bold green")
            context = format_docs(filtered_documents)
        else:
            console.print("Contexto Vacio FAIL", style="bold red")
            context = ""
        
        console.print("-"*20, style="bold blue")
        
        # Actualizar el estado con el contexto encontrado
        state["context"] = context
        
        return state
