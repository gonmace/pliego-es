from pliego_esp.graph.state import State
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler

from typing import Optional, Literal

from pydantic import BaseModel, Field

console = Console()

prompt_template = ChatPromptTemplate.from_template("""
Eres un asistente experto en construcción y redacción de especificaciones técnicas.

A continuación se presenta una especificación técnica y un parámetro técnico con su valor asignado. Tu tarea es evaluar si el parámetro es **aplicable técnicamente** al contexto de la especificación.

---

## Especificación técnica:

{especificacion_generada}

## Parámetro Técnico:

{parametro_tecnico}: {valor_asignado}

---

Evalúa si el parámetro técnico entregado puede aplicarse de forma técnica y coherente dentro del contexto del ítem descrito (materiales, procesos, resultados, requisitos funcionales o estéticos).

Debes proporcionar tu respuesta en formato estructurado según el modelo definido.
""")
    
class ReviewUnassignedParameters(BaseModel):
    parametro: str = Field(description="El nombre del parámetro técnico")
    valor: str = Field(description="El valor asignado al parámetro")
    comentario: str = Field(description="Una única oración breve y objetiva que indique si el parámetro técnico se relaciona con la especificación y si es aplicable técnicamente. Aclarar que debe ser una relación técnica, no de otra naturaleza.")
    corresponde: Literal["Sí", "No", "Parcialmente"] = Field(description="Indica si el parámetro corresponde (Sí / No / Parcialmente)")
    calificacion: int = Field(description="Una calificación entre 1 (no aplicable) y 10 (totalmente aplicable) basada en la relevancia del parámetro en el contexto técnico de la especificación")

async def review_unassigned_parameters(state: State, *, config: RunnableConfig) -> State:
    console.print("------ review_unassigned_parameters ------", style="bold green")

    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="green")

    configuration = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.5,
        callbacks=[shared_callback_handler]
    )

    # Usar with_structured_output en lugar de StrOutputParser
    review_chain = prompt_template | llm.with_structured_output(ReviewUnassignedParameters)

    evaluaciones = []
    cost = 0

    for parametro in state["other_parametros"]:
        parametro_nombre = parametro.get("Parámetro Técnico", "").strip()
        valor_asignado = parametro.get("Valor Asignado", "").strip()

        if not parametro_nombre or not valor_asignado:
            continue  

        evaluacion = await review_chain.ainvoke({
            "especificacion_generada": state["especificacion_generada"],
            "parametro_tecnico": parametro_nombre,
            "valor_asignado": valor_asignado
        })
        
        console.print(f"Costo parcial después de procesar '{parametro_nombre}': ${shared_callback_handler.total_cost:.6f}", style="green")

        evaluaciones.append(
            evaluacion.model_dump()
        )
        cost += shared_callback_handler.total_cost
    
    console.print(evaluaciones, style="bold green")    
    costo_nodo = shared_callback_handler.total_cost - costo_inicial
    console.print(f"Costo total del nodo review_unassigned_parameters: ${costo_nodo:.6f}", style="green")
    console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="green")

    return {"evaluaciones_otros_parametros": evaluaciones}