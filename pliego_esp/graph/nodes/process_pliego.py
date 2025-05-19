from pliego_esp.graph.state import State
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pliego_esp.graph.configuration import Configuration
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler
from langchain_core.messages import HumanMessage

console = Console()

def limpiar_bloque_markdown(texto):
    if texto.strip().startswith("```markdown"):
        texto = texto.strip()[len("```markdown"):].strip()
    if texto.endswith("```"):
        texto = texto[:texto.rfind("```")].strip()
    return texto

async def process_pliego(state: State, *, config: RunnableConfig) -> State:
    console.print("------ process_pliego ------", style="bold white")

    # Guardar el costo inicial
    costo_inicial = shared_callback_handler.total_cost
    console.print(f"Costo inicial: ${costo_inicial:.6f}", style="white")

    configuration = Configuration.from_runnable_config(config)
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.4,
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
- **Adicionales**: {adicionales_finales}

---

## Instrucciones de redacción por sección

### Descripción
- Presentar el propósito del ítem y sus componentes esenciales.
- Mencionar materiales clave como hormigón, mallas, selladores o aditivos si aplican, redactados de forma técnica y natural.
- **No incluir pasos constructivos, procedimientos ni acciones específicas.**

### Materiales, Herramientas y Equipo.
- Incluir exclusivamente los materiales, herramientas, equipos y EPP requeridos, según los parámetros técnicos disponibles o sus valores por defecto.
- **Integrar los Materiales, herramientas ó equipos que requiera el ítem en esta sección, no agregar una sección adicional.**

### Procedimiento.
Redacta el procedimiento en varios párrafos (sin numeración ni viñetas), describiendo el proceso constructivo paso a paso y con detalle de acuerdo a la especificación genérica. 
- Incorpora los **parámetros técnicos relevantes** en el flujo del texto.
- Incluye los **adicionales** solo si **modifican** o **complementan** el proceso.
- IMPORTANTE: Aplica negrilla en **acciones clave**, **términos técnicos**, **herramientas y materiales**, y **unidades de medida**.
- No utilices la palabra "procedimiento" dentro del contenido.
- Omite cualquier adicional que altere el desarrollo constructivo.

### Medición y Forma de Pago.
Redactar dos párrafos consecutivos, uno por cada aspecto:
- **Medición y Verificación**: indicar la unidad de medida (**metros cuadrados (m²)**) y cómo se cuantificará. Mencionar que el control será realizado por **EMBOL S.A.**, con una breve descripción del método de validación.
- **Pago**: establecer condiciones para el pago, mencionando criterios de aceptación o penalizaciones si corresponde. Además, indicar si está sujeto a condiciones, avances o verificaciones técnicas.
- Usar **negrita** en términos clave como: **verificación**, **metros cuadrados**, **multas**, etc.

---

## Estilo y restricciones

- Redacción técnica, precisa, profesional y sin ambigüedades.
- **Mantener la jerarquia de los titulos de la especificacion generica**, es decir, el título de la con ## y las secciones con ###.
- **No modificar** los títulos ni el orden de las secciones.
- **No incluir**:
  - Listas, numeraciones, encabezados adicionales ni explicaciones fuera de contexto.

---

El resultado debe ser una especificación técnica **clara, profesional y lista para incorporar directamente en documentos oficiales**.

---

## Especificación genérica:

{especificacion_base}
""")
    
    parametros_clave = state.get("parametros_clave", [])
    # Filtra parámetros clave con recomendación no vacía
    parametros_filtrados = [p for p in parametros_clave if p.get("recomendacion")]
    # Generación de líneas para el prompt
    lineas_parametros = [f"- {p['nombre']}: {p['valor']}" for p in parametros_filtrados]
    # Unir en un solo string si lo necesitas como bloque de texto
    texto_parametros = "\n".join(lineas_parametros)
    
    adicionales = state.get("adicionales", [])
    # Filtra adicionales donde 'nuevo' es False
    adicionales_filtrados = [a for a in adicionales if not a.get("nuevo")]
    # Formatear cada adicional en el formato deseado
    lineas_adicionales = [f"- {a['nombre']}: {a['descripcion']}" for a in adicionales_filtrados]
    # Unir en un solo string si lo necesitas como bloque de texto
    texto_adicionales = "\n".join(lineas_adicionales)

    # Generar la especificación
    prompt = prompt_template.format_prompt(
        titulo=state.get("titulo", ""),
        parametros_clave=texto_parametros,
        adicionales_finales=texto_adicionales,
        especificacion_base=state.get("pliego_base", "")
    ).to_messages()

    especificacion_generada = await llm.ainvoke(prompt)
    
    resultado_limpio = limpiar_bloque_markdown(especificacion_generada.content)

    console.print(resultado_limpio, style="white")
    
    costo_nodo = shared_callback_handler.total_cost - costo_inicial
    console.print(f"Costo total del nodo process_pliego: ${costo_nodo:.6f}", style="bold white")
    console.print(f"Costo acumulado hasta ahora: ${shared_callback_handler.total_cost:.6f}", style="white")
    
    console.print(20*"-", style="bold white")

    return {
        "especificacion_generada": resultado_limpio,
        "token_cost": shared_callback_handler.total_cost
    }