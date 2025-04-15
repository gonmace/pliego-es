from langchain_core.messages import AIMessage
from langgraph.graph import END

from pliego_esp.graph.state import State

def off_topic_response(state: State):
    """
    Nodo que responde cuando la consulta del usuario no está relacionada
    con el contenido del Código Civil. Responde amablemente sin intentar
    contestar temas fuera del dominio.
    """
    response = (
        "Lo siento, pero solo puedo ayudarte con consultas relacionadas al Código Civil. "
        "Por favor, reformula tu pregunta para que esté relacionada con el contenido del código legal. "
        "Estoy aquí para ayudarte con temas jurídicos específicos del Código Civil."
    )
    
    return {
        "messages": state["messages"] + [AIMessage(content=response)],
        "current_node": END
    } 