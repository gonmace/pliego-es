# add_unassigned_parameters.py

from pliego_esp.graph.state import State
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler
from langgraph.types import interrupt

console = Console()

prompt_template = ChatPromptTemplate.from_template("""
Eres un asistente experto en redacción técnica de documentos de construcción.

Se te proporcionará una **especificación técnica en formato Markdown**.  
Tu tarea es editar el documento para **agregar** las **actividades adicionales** indicadas más abajo, siguiendo instrucciones estrictas:

---

## Instrucciones:

1. **Agregar** las actividades adicionales, como un producto de la construcción y no como proceso constructivo.
   - Redacta como parte natural de las secciones existentes (Descripción, Materiales, Procedimiento, etc.).
   - No mencionar que son "nuevas actividades", ni utilizar lenguaje de modificación.

2. **Formato del resultado**:
   - Mantener exactamente las mismas secciones y orden del documento base.
   - Mantener la redacción técnica, profesional, clara y sin adornos innecesarios.

3. **Estilo**:
   - No agregar nuevas secciones.
   - No eliminar contenido existente.
   - Respetar el tono objetivo y técnico de la especificación base.

---

## Actividades Adicionales a integrar:

{actividades_adicionales}

---

## Especificación Técnica Base:

{especificacion_generada}
""")


async def add_other_adicionales(state: State, *, config: RunnableConfig) -> State:
    console.print("------ add_other_adicionales ------", style="bold cyan")

    configuration = Configuration.from_runnable_config(config)
    
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.0,
        callbacks=[shared_callback_handler]
    )
    
    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="cyan")

    if len(state["evaluaciones_adicionales"]) > 0:

        console.print("Adicionales a evaluar: ", len(state["evaluaciones_adicionales"]), style="cyan")
        
        items = state.get("evaluaciones_adicionales", [])
        
        for item in items:
            item["titulo"] = item['actividad']
            item["pregunta"] = "¿Desea que se agregue la actividad en la especificación?"
        
        respuesta_humana = interrupt({
            "action": "modal_adicionales",
            "items": items
        })
        
        for item in respuesta_humana:
            item.pop("titulo", None)
            item.pop("pregunta", None)
        

        # Contar cuántos tienen 'agregar': True
        cantidad_agregar_true = sum(1 for item in respuesta_humana if item.get('agregar') == True)
        
        console.print("Adicionales a integrar: ", cantidad_agregar_true, style="bold cyan")
        
        if cantidad_agregar_true > 0:
            
            actividades_adicionales = "\n".join(f"- {param['actividad']}" for param in respuesta_humana if param.get("agregar") == True)
            
            prompt = prompt_template.format_prompt(
                actividades_adicionales=actividades_adicionales,
                especificacion_generada=state.get("especificacion_generada", "")
            ).to_messages()
        
            especificacion_con_adicionales = await llm.ainvoke(prompt)
        
            # Calcular el costo del nodo
            costo_nodo = shared_callback_handler.total_cost - costo_inicial
            console.print(f"Costo total del nodo add_unassigned_parameters: ${costo_nodo:.6f}", style="bold cyan")
            console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="cyan")

            return {
                "especificacion_generada": especificacion_con_adicionales.content,
                "token_cost": shared_callback_handler.total_cost,
            }
        
        else:
            console.print("No hay parametros para integrar", style="bold red")
            return state
    else:
        console.print("No hay parametros para integrar", style="bold red")
        return state
