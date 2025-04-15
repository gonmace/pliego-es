from dataclasses import dataclass, field
from typing import Dict, List
from langgraph.graph import MessagesState

@dataclass(kw_only=True)
class State(MessagesState):
    """The state of your graph / agent."""
    
    pliego_base: str = field(
        default="",
        metadata={"description": "Pliego de especificaciones base en formato Markdown."}
        )
    
    parametros: str = field(
        metadata={"description": "Parametros de la especificación"}
        )
    
    adicionales: List[str] = field(
        default_factory=list,
        metadata={"description": "Actividades adicionales de la especificación"}
        )
    
    token_cost: float = field(
        default=0,
        metadata={"description": "Costo de los tokens."}
        )

    # @classmethod
    # def update_token_info(cls, state: dict, new_token_info: Dict[str, float]) -> dict:
    #     """Actualiza el campo 'token_info' de un dict de estado."""
    #     current_token_info = state.get("token_info", {})
    #     for key, value in new_token_info.items():
    #         if key in current_token_info:
    #             current_token_info[key] += value
    #         else:
    #             current_token_info[key] = value
    #     state["token_info"] = current_token_info
    #     return state


__all__ = ["State"]