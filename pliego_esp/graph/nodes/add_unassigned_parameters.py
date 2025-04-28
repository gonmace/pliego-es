from pliego_esp.graph.state import State
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler
from langgraph.types import interrupt
from typing import Optional, Literal
from langchain_core.messages import HumanMessage

from pydantic import BaseModel, Field

console = Console()

prompt_template = ChatPromptTemplate.from_template("""
Eres un asistente experto en redacción técnica de documentos de construcción.

Se te proporcionará una **especificación técnica en formato Markdown**.  
Tu tarea es editar el documento para **adaptar e integrar** las **características técnicas adicionales** indicadas más abajo, siguiendo instrucciones estrictas:

---

## Instrucciones:

1. **Integrar naturalmente** las características cuyo campo `corresponde` sea `Sí`.
   - Redacta como parte natural de las secciones existentes (Descripción, Materiales, Procedimiento, etc.).
   - No mencionar que son "nuevos parámetros", ni utilizar lenguaje de modificación.

2. **Agregar como nota técnica** las características cuyo campo `corresponde` sea `No`.
   - Insertarlas de manera breve y formal en la sección más adecuada (normalmente en Procedimiento o como Observación Técnica).
   - Indicar que **no aplica** para este ítem, pero sin alterar el flujo técnico.

3. **Formato del resultado**:
   - Mantener exactamente las mismas secciones y orden del documento base.
   - Mantener la redacción técnica, profesional, clara y sin adornos innecesarios.

4. **Estilo**:
   - No agregar nuevas secciones.
   - No eliminar contenido existente.
   - Respetar el tono objetivo y técnico de la especificación base.

---

## Características Técnicas Adicionales a integrar:

{caracteristicas_adicionales}

---

## Especificación Técnica Base:

{especificacion_generada}
""")


async def add_unassigned_parameters(state: State, *, config: RunnableConfig) -> State:
    console.print("------ add_unassigned_parameters ------", style="bold blue")

    configuration = Configuration.from_runnable_config(config)
    
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.0,
        callbacks=[shared_callback_handler]
    )
    
    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="blue")

    if len(state["evaluaciones_otros_parametros"]) > 0:

        console.print(len(state["evaluaciones_otros_parametros"]), style="bold yellow")
        respuesta_humana = interrupt({
            "mensaje": "nuevos parametros",
            "items": state.get("evaluaciones_otros_parametros", [])
        })
             
        caracteristicas_adicionales = "\n".join(f"{param['parametro']}: {param['valor']}" for param in respuesta_humana if param.get("agregar") == True)
        
        # Armar el prompt
        prompt = prompt_template.format_prompt(
            caracteristicas_adicionales=caracteristicas_adicionales,
            especificacion_generada=state.get("especificacion_generada", "")
        ).to_messages()
        
        especificacion_con_parametros = llm.invoke(prompt).content
        
        # Calcular el costo del nodo
        costo_nodo = shared_callback_handler.total_cost - costo_inicial
        console.print(f"Costo total del nodo add_unassigned_parameters: ${costo_nodo:.6f}", style="bold white")
        console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="white")

        return {
            "especificacion_generada": especificacion_con_parametros,
            "token_cost": shared_callback_handler.total_cost,
        }
    else:
        console.print("No hay evaluaciones de otros parametros", style="bold red")
        return state
