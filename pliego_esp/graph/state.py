from dataclasses import dataclass, field
from typing import Dict, List, TypedDict, Any, Annotated
from langgraph.graph import MessagesState
import json
import operator

from pliego_esp.graph.nodes.match_adicionales import Adicional

@dataclass(kw_only=True)
class State(MessagesState):
    """The state of your graph / agent."""
    
    pliego_base: str = field(
        default="",
        metadata={"description": "Pliego de especificaciones base en formato Markdown."}
        )
    
    titulo: str = field(
        default="",
        metadata={"description": "Titulo de la especificación"}
        )

    # PARAMETROS PARA EL PLIEGO 
    parametros_pliego: str = field(
        default="",
        metadata={"description": "Parametros técnicos recomendados en formato Markdown"}
        )

    parsed_parametros: List[Dict[str, str]] = field(
        default_factory=list,
        metadata={"description": "Tabla de parámetros técnicos en formato lista de diccionarios"}
        )
            
    parametros_clave: List[str] = field(
        default_factory=list,
        metadata={"description": "Parametros clave para la nueva especificación"}
        )
    
    parametros_no_asignados: List[str] = field(
        default_factory=list,
        metadata={"description": "Otros parámetros clave que no coinciden en ninguno de los parametros del pliego base"}
        )
    
    other_parametros: List[Dict[str, str]] = field(
        default_factory=list,
        metadata={"description": "Otros parámetros clave que no coinciden en ninguno de los parametros del pliego base"}
        )
    
    evaluaciones_otros_parametros: List[Dict[str, str]] = field(
        default_factory=list,
        metadata={"description": "Tabla de evaluaciones de parámetros en formato lista de diccionarios"}
        )
    
    # ADICIONALES PARA EL PLIEGO 
    adicionales_pliego: List[str] = field(
        default_factory=list,
        metadata={"description": "Actividades adicionales de la especificación"}
        )
    
    evaluaciones_parametros: List[Dict[str, str]] = field(
        default_factory=list,
        metadata={"description": "Tabla de evaluaciones de parámetros en formato lista de diccionarios"}
        )
    
    parsed_adicionales: List[Dict[str, str]] = field(
        default_factory=list,
        metadata={"description": "Tabla de actividades adicionales en formato lista de diccionarios"}
        )

    adicionales: List[str] = field(
        default_factory=list,
        metadata={"description": "Adicionales para la nueva especificación"}
        )
    
    adicionales_finales: List[Dict[str, str]] = field(
        default_factory=list,
        metadata={"description": "Tabla de actividades adicionales en formato lista de diccionarios"}
        )

    other_adicionales: List[Adicional] = field(
        default_factory=list,
        metadata={"description": "Otros adicionales para la nueva especificación"}
        )
    
    evaluaciones_adicionales: List[Dict[str, str]] = field(
        default_factory=list,
        metadata={"description": "Evaluaciones de actividades adicionales en formato lista de diccionarios"}
        )
    
    # COSTOS
    token_cost: Annotated[float, operator.add] = field(
        default=0.0,
        metadata={"description": "Costo de los tokens."}
        )
    
    especificacion_generada: str = field(
        default="",
        metadata={"description": "Especificación generada en formato Markdown."}
        )
    
    def __getitem__(self, key):
        """Método para acceder a los elementos del estado como diccionario."""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"Key {key} not found in state")
    
    def __setitem__(self, key, value):
        """Método para establecer elementos del estado como diccionario."""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Key {key} not found in state")


__all__ = ["State"]