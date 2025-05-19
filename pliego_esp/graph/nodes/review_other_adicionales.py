from pliego_esp.graph.state import State
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler
import asyncio
from functools import partial

from typing import Literal

from pydantic import BaseModel, Field

console = Console()

prompt_template = ChatPromptTemplate.from_template("""
Eres un asistente experto en construcción y redacción de especificaciones técnicas.

A continuación se presenta una especificación técnica y una actividad adicional. Tu tarea es evaluar si la actividad adicional es un complemento **aplicable técnicamente** a la especificación.

---

## Especificación técnica:

{especificacion_generada}

## Actividad adicional:

### Descripción: {descripcion_adicional}

---

Evalúa si la actividad adicional puede ser una actividad complementaria aplicable de forma técnica y coherente dentro del contexto de la especificación.

Debes proporcionar tu respuesta en formato estructurado según el modelo definido.
""")

class ReviewOtherAdicionales(BaseModel):
    actividad: str = Field(description="Nombre de la actividad adicional")
    descripcion: str = Field(description="Descripción de la actividad adicional")
    comentario: str = Field(description="Una única oración breve y objetiva que indique si la actividad adicional es complementaria y aplicable técnicamente. Aclarar que debe ser una relación técnica, no de otra naturaleza.")
    corresponde: Literal["Sí", "No", "Parcialmente"] = Field(description="Indica si la actividad adicional corresponde (Sí / No / Parcialmente)")

async def _process_adicional(review_chain, adicional, especificacion_generada):
    try:
        evaluacion = await review_chain.ainvoke({
            "especificacion_generada": especificacion_generada,
            "descripcion_adicional": adicional.get("descripcion", "")
        })
        return evaluacion.model_dump()
    except Exception as e:
        console.print(f"Error procesando adicional: {str(e)}", style="bold red")
        return None

async def review_other_adicionales(state: State, *, config: RunnableConfig) -> State:
    console.print("------ review_other_adicionales ------", style="bold green")

    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="green")

    configuration = Configuration.from_runnable_config(config)
    
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.0,
        callbacks=[shared_callback_handler]
    )

    review_chain = prompt_template | llm.with_structured_output(ReviewOtherAdicionales)

    adicionales = state.get("adicionales", [])
    adicionales_filtrados = [a for a in adicionales if a.get("nuevo")]
    
    console.print(adicionales_filtrados, style="green")
    
    # Crear tareas para procesar cada adicional
    tasks = [
        _process_adicional(
            review_chain,
            adicional,
            state["especificacion_generada"]
        )
        for adicional in adicionales_filtrados
    ]
    
    # Ejecutar todas las tareas concurrentemente
    evaluaciones = await asyncio.gather(*tasks)
    
    # Filtrar resultados None
    evaluaciones = [e for e in evaluaciones if e is not None]
    
    console.print(evaluaciones, style="bold green")    
    costo_nodo = shared_callback_handler.total_cost - costo_inicial
    console.print(f"Costo total del nodo review_unassigned_parameters: ${costo_nodo:.6f}", style="green")
    console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="green")

    return {"evaluaciones_adicionales": evaluaciones}