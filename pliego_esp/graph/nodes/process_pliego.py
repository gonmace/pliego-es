from pliego_esp.graph.state import State
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler
from langchain_core.messages import HumanMessage

console = Console()

async def process_pliego(state: State, *, config: RunnableConfig) -> State:
    console.print("------ process_pliego ------", style="bold white")

    # Guardar el costo inicial
    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="white")

    configuration = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(
        model=configuration.chat_model,
        temperature=0.5,
        callbacks=[shared_callback_handler]
    )

    # Preparar el prompt para generar la especificación técnica
    prompt_template = ChatPromptTemplate.from_template("""
Por favor genera una especificación técnica en formato **Markdown (.md)**, tomando como base la **especificación genérica** proporcionada más abajo, respetando estrictamente la estructura, el estilo y el orden de la especificación original.

---

## Objetivo de la tarea

Adaptar la especificación genérica al nuevo ítem indicado, incorporando únicamente:

- Los **parámetros técnicos relevantes**, usando su **Valor Asignado**.
- Los **adicionales**, integrados en las secciones que correspondan, considerando el orden de ejecución del ítem.

---

## Detalles de la nueva especificación

- **Título del ítem**: {titulo}
- **Parámetros técnicos relevantes**: {parametros_clave}
- **Adicionales**: {adicionales}

---

## Instrucciones de redacción por sección

### Descripción
- Presentar el propósito del ítem y sus componentes esenciales.
- Mencionar materiales clave como hormigón, mallas, selladores o aditivos si aplican, redactados de forma técnica y natural.
- **No incluir pasos constructivos, procedimientos ni acciones específicas.**

### Materiales, herramientas y equipo
- Incluir exclusivamente los materiales, herramientas, equipos y EPP requeridos, según los parámetros técnicos disponibles o sus valores por defecto.
- **Integrar los Materiales, herramientas ó equipos que requiera el ítem en esta sección, no agregar una sección adicional.**

### Procedimiento
- Redactar en párrafos, sin numeración ni viñetas.
- Describir el proceso constructivo incorporando:
  - Los parámetros técnicos relevantes.
  - Los adicionales, **solo si modifican o complementan el procedimiento**.
- Omitir los adicionales que no alteran el desarrollo del procedimiento.
- Resaltar con **negrita** las acciones clave del proceso (ej. **Hormigonado**, **Limpieza**, **Verificación**, etc.).

### Medición y Forma de Pago
Redactar tres párrafos consecutivos, uno por cada aspecto:

1. **Medición**: indicar la unidad de medida (**metros cuadrados (m²)**) y cómo se cuantificará.
2. **Verificación**: detallar que el control será realizado por **EMBOL S.A.**, con una breve descripción del método de validación.
3. **Pago**: establecer condiciones para el pago, mencionando criterios de aceptación o penalizaciones si corresponde.

- Usar **negrita** únicamente en términos clave como **verificación**, **metros cuadrados**, **multas**, etc.

---

## Estilo y restricciones

- Redacción técnica, precisa, profesional y sin ambigüedades.
- **No modificar** los títulos ni el orden de las secciones.
- **No incluir**:
  - Listas, numeraciones, encabezados adicionales ni explicaciones fuera de contexto.

---

El resultado debe ser una especificación técnica **clara, profesional y lista para incorporar directamente en documentos oficiales**.

---

## Especificación genérica:

{especificacion_base}
""")


    # Preparar los datos para el prompt
    parametros_clave = "\n".join([f"- {param}" for param in state.get("parametros_clave", [])])
    adicionales_finales = "\n".join([f"- {a}" for a in state.get("adicionales_finales", [])])
    
    # Generar la especificación
    prompt = prompt_template.format_prompt(
        titulo=state.get("titulo", ""),
        parametros_clave=parametros_clave,
        adicionales=adicionales_finales,
        especificacion_base=state.get("pliego_base", "")
    ).to_messages()

    # console.print(prompt, style="bold white")
    
    especificacion_generada = llm.invoke(prompt).content

    # Calcular el costo del nodo
    costo_nodo = shared_callback_handler.total_cost - costo_inicial
    console.print(f"Costo total del nodo process_pliego: ${costo_nodo:.6f}", style="bold white")
    console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="white")
    
    state["messages"] = [
        HumanMessage(content=f"{especificacion_generada}")
    ]
    console.print(especificacion_generada, style="white")
    console.print(20*"-", style="bold white")
    return {
        "messages": state["messages"],
        "especificacion_generada": especificacion_generada,
        "token_cost": shared_callback_handler.total_cost
    }