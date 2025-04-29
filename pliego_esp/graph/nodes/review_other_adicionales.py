from pliego_esp.graph.state import State
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler

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

{actividad_adicional}

---

Evalúa si la actividad adicional puede ser una actividad complementaria aplicable de forma técnica y coherente dentro del contexto de la especificación.

Debes proporcionar tu respuesta en formato estructurado según el modelo definido.
""")

class ReviewOtherAdicionales(BaseModel):
    actividad: str = Field(description="El nombre de la actividad adicional")
    comentario: str = Field(description="Una única oración breve y objetiva que indique si la actividad adicional es complementaria y aplicable técnicamente. Aclarar que debe ser una relación técnica, no de otra naturaleza.")
    corresponde: Literal["Sí", "No", "Parcialmente"] = Field(description="Indica si la actividad adicional corresponde (Sí / No / Parcialmente)")

async def review_other_adicionales(state: State, *, config: RunnableConfig) -> State:
    console.print("------ review_other_adicionales ------", style="bold green")

    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="green")
    
    console.print(state, style="green")

    configuration = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.0,
        callbacks=[shared_callback_handler]
    )

    # Usar with_structured_output en lugar de StrOutputParser
    review_chain = prompt_template | llm.with_structured_output(ReviewOtherAdicionales)

    evaluaciones = []
    cost = 0

    for adicional in state["other_adicionales"]:
        actividad = adicional.get("actividad", "").strip()

        evaluacion = await review_chain.ainvoke({
            "especificacion_generada": state["especificacion_generada"],
            "actividad_adicional": actividad
        })
        
        console.print(f"Costo parcial después de procesar '{actividad}': ${shared_callback_handler.total_cost:.6f}", style="green")

        console.print(evaluacion)
        evaluaciones.append(
            evaluacion.model_dump()
        )
        cost += shared_callback_handler.total_cost
    
    costo_nodo = shared_callback_handler.total_cost - costo_inicial
    console.print(f"Costo total del nodo review_unassigned_parameters: ${costo_nodo:.6f}", style="green")
    console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="green")

    return {"evaluaciones_adicionales": evaluaciones}