from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field, fields
from typing import Annotated, Any, Literal, Optional, Type, TypeVar

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import RunnableConfig, ensure_config

from rich.console import Console
console = Console()


@dataclass(kw_only=True)
class IndexConfiguration:
    """Configuration class for indexing and retrieval operations.

    This class defines the parameters needed for configuring the indexing and
    retrieval processes, including user identification, embedding model selection,
    retriever provider choice, and search parameters.
    """

    embeddings: OpenAIEmbeddings = field(
        default_factory=lambda: OpenAIEmbeddings(
            model="text-embedding-3-small"
        ),
        metadata={"description": "The OpenAI embeddings model configuration."}
    )

    vectorstore: Chroma = field(
        default_factory=lambda: Chroma(
            collection_name="langchain",
            embedding_function=OpenAIEmbeddings(
                model="text-embedding-3-small"
            ),
            persist_directory=str(Path(__file__).parent.parent.parent / "chromadb")
        ),
        metadata={"description": "The Chroma vector store configuration."}
    )

    # user_id: str = field(metadata={"description": "Unique identifier for the user."})

    # embedding_model: Annotated[str, {"__template_metadata__": {"kind": "embeddings"}},] = field(
    #     default="text-embedding-3-small",
    #     metadata={"description": "Name of the embedding model to use. Must be a valid embedding model name."},
    #     )

    # retriever_provider: Annotated[ Literal["chroma", "pinecone", "mongodb"],
    #     {"__template_metadata__": {"kind": "retriever"}},
    # ] = field(default="chroma",
    #           metadata={"description": "The vector store provider to use for retrieval. Options are 'chroma', 'pinecone', or 'mongodb'."},
    #           )

    search_kwargs: dict[str, Any] = field(
        default_factory=dict,
        metadata={
            "description": "Additional keyword arguments to pass to the search function of the retriever."
        },
    )

    @classmethod
    def from_runnable_config(
        cls: Type[T], config: Optional[RunnableConfig] = None
    ) -> T:
        """Create an IndexConfiguration instance from a RunnableConfig object.

        Args:
            cls (Type[T]): The class itself.
            config (Optional[RunnableConfig]): The configuration object to use.

        Returns:
            T: An instance of IndexConfiguration with the specified configuration.
        """
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})


T = TypeVar("T", bound=IndexConfiguration)

@dataclass(kw_only=True)
class Configuration(IndexConfiguration):
    """Clase de configuración para el agente."""
    # llm_chat: Literal["gpt-4o-mini", "gpt-3.5-turbo"] = field(default="gpt-4o-mini", metadata={"description": "Modelo de lenguaje a utilizar para chat."})
    llm_chat_temperature: float = field(default=0.1, metadata={"description": "Temperatura para el modelo de lenguaje."})
    llm_chat_model: Literal["gpt-4o-mini", "gpt-3.5-turbo"] = field(default="gpt-4o-mini", metadata={"description": "Modelo de lenguaje a utilizar para chat."})
    
    token_input_price: float = 0.15/1000000
    token_output_price: float = 0.6/1000000
    umbral_contexto: float = 0.45
    
    connection_kwargs: dict = field(default_factory=lambda: {
        "autocommit": True,
        "prepare_threshold": 0,
    }, metadata={"description": "Configuración de conexión para la base de datos"})
    
    query_system_prompt: str = field(default="""
    Eres un asistente útil y amigable. Tu objetivo es ayudar a los usuarios con sus preguntas y tareas.
    """, metadata={"description": "Prompt para la consulta del modelo."})

    query_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="gpt-4o-mini",
        metadata={
            "description": "The language model used for processing and refining queries. Should be in the form: provider/model-name."
        },
    )

