from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler

from rich.console import Console
import json

from pydantic import BaseModel, Field
from typing import List

console = Console()

class Adicional(BaseModel):
    actividad: str = Field(
        description="Nombre original de la actividad compatible encontrada. Si no hay coincidencia, usar 'otros'."
    )
    descripcion: str = Field(
        description="Descripción técnica basada en la actividad compatible, adaptada si la propuesta lo requiere. Si no hay coincidencia, es simplemente la actividad propuesta."
    )

class MatchAdicionales(BaseModel):
    adicionales_finales: List[Adicional] = Field(
        description="Lista de actividades compatibles con la especificación técnica, con descripciones originales o adaptadas."
    )
    other_adicionales: List[Adicional] = Field(
        description="Lista de actividades que no coinciden técnicamente con las actividades adicionales existentes."
    )

prompt_template = ChatPromptTemplate.from_template(
"""Eres un asistente técnico especializado en construcción.

Tienes una lista de **actividades adicionales compatibles**, cada una con un nombre y una descripción técnica.

También recibirás una **actividad propuesta**.

---

### Actividades adicionales compatibles:
{actividades_adicionales}

### Actividad propuesta:
{actividad_propuesta}

---

Tu tarea es la siguiente:

1. Determina si la actividad propuesta **coincide técnicamente** con alguna de las actividades adicionales.
   - Evalúa el **objetivo, procedimiento constructivo y materiales**.
   - Ignora diferencias en redacción superficial o nombres distintos.

2. Si hay coincidencia técnica:
   - Devuelve la actividad coincidente original como `actividad`.
   - Compara la descripción técnica original con la propuesta. Si la propuesta requiere ajustes (p. ej. exclusión de químicos), adapta la descripción original para reflejarlo.

3. Si **no hay coincidencia clara**, incluye la actividad propuesta en `other_adicionales`, usando `"Otros"` como nombre y la actividad propuesta como descripción.

Devuelve la lista `adicionales_finales` y `other_adicionales` según corresponda.
""")


async def match_adicionales(state: dict, *, config: RunnableConfig) -> dict:
    console.print("----- match_adicionales -----", style="bold green")
    costo_inicial = shared_callback_handler.total_cost
    
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="green")

    configuration = Configuration.from_runnable_config(config)
    
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.0,
        callbacks=[shared_callback_handler]
    )

    match_chain = prompt_template | llm.with_structured_output(MatchAdicionales)
    
    actividades_compatibles_json = json.dumps(state["parsed_adicionales"], ensure_ascii=False, indent=2)

    state["adicionales_finales"] = []
    state["other_adicionales"] = []
    adicionales_finales = []
    otros = []

    for actividad_propuesta in state["adicionales"]:
        
        response = await match_chain.ainvoke({
            "actividades_adicionales": actividades_compatibles_json,
            "actividad_propuesta": actividad_propuesta
        })

        if response.adicionales_finales:
            adicionales_finales.extend(response.adicionales_finales)
        else:
            otros.extend(response.other_adicionales)
        
        console.print(f"Costo parcial después de procesar '{actividad_propuesta}': ${shared_callback_handler.total_cost:.6f}", style="green")

    costo_nodo = shared_callback_handler.total_cost - costo_inicial
    console.print(f"Costo total del nodo match_adicionales: ${costo_nodo:.6f}", style="green")
    console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="green")
    
    # Guardar resultados en el state
    state["adicionales_finales"] = [a.model_dump() for a in adicionales_finales]
    console.print(f"Adicionales finales: {state['adicionales_finales']}", style="green")
    
    state["other_adicionales"] = [a.model_dump() for a in otros]
    console.print(f"Other adicionales: {state['other_adicionales']}", style="green")
    
    console.print(20*"-", style="green")
    return {
        "adicionales_finales": adicionales_finales,
        "other_adicionales": otros
    }