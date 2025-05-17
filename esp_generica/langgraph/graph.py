from typing import TypedDict, List
from langgraph.graph import Graph, StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from rich.console import Console
console = Console()

class ParametroTecnico(BaseModel):
    Parámetro_Técnico: str = Field(
        description="Nombre del parámetro técnico que debe ser configurable en esta especificación (por ejemplo: espesor, resistencia, pendiente mínima)."
    )
    Opciones_válidas: str = Field(
        description="Listado o rango de valores aceptables para este parámetro (por ejemplo: 3–7 cm, H30, mínima 1%)."
    )
    Valor_por_defecto: str = Field(
        description="Valor sugerido si no se especifica otro durante el uso del ítem técnico."
    )

class Adicional(BaseModel):
    actividad: str = Field(
        description="Nombre de una actividad complementaria común al tipo de ítem. No usar 'Otros'."
    )
    descripcion: str = Field(
        description="Explicación breve y técnica de la actividad complementaria que puede aplicarse según el contexto del proyecto."
    )

class Content(BaseModel):
    descripcion: str = Field(
        description="Descripción general y técnica de la actividad principal, sin valores numéricos ni referencias comerciales. En formato Markdown."
    )
    procedimiento: str = Field(
        description="Secuencia técnica de ejecución de la actividad, en párrafos, sin pasos numerados, redactado en formato Markdown."
    )
    parametros_tecnicos: List[ParametroTecnico] = Field(
        description="Listado de parámetros técnicos editables, extraídos desde el texto original para garantizar reutilización del ítem."
    )
    adicionales: List[Adicional] = Field(
        description="Lista de actividades complementarias frecuentes, como preparación previa, curado, aditivos, etc."
    )

class MEH(BaseModel):
    materiales: str = Field(
        description="Materiales a ser usados en la actividad."
    )
    equipo: str = Field(
        description="Equipo a ser usado en la actividad."
    )
    herramientas: str = Field(
        description="Herramientas a ser usadas en la actividad."
    )
    EPP: str = Field(
        description="EPP mínimo indespensable y necesairo a ser usado en la actividad."
    )

# Definición de tipos para el estado
class State(TypedDict):
    titulo: str
    especificaciones_tecnicas: List[str]
    especificacion_base: str
    adicionales_input: str
    
    contenido: Content
    MEH: MEH
    medicion_pago: str
    
    documento_final: str

# Nodo 1: Análisis inicial y estructura
def fusionar_especificaciones(state: State) -> State:
    
    if len(state["especificaciones_tecnicas"]) == 1:
        return {
            "especificacion_base": state["especificaciones_tecnicas"][0]
            }
        
    prompt = ChatPromptTemplate.from_template("""
Tienes especificaciones técnicas de construcción que describen actividades similares  constructivas (por ejemplo, "losas de concreto", "piso de losa de HºAº de 15 cm", etc.). Tu tarea es fusionarlas en una **única especificación técnica consolidada**, siguiendo los estándares de redacción técnica para construcción.

El titulo de la especificación fusionada debe ser: {titulo}
### Instrucciones:
1. Revisa las especificaciones y comprende su propósito común.
2. Combina toda la información útil y complementaria de ambas, sin omitir detalles técnicos importantes.
3. **No repitas** información ya incluida, y **resuelve cualquier contradicción** (por ejemplo, diferentes métodos o materiales) eligiendo la alternativa más precisa, técnica o comúnmente aceptada. Si es posible, **integra ambas opciones** si son compatibles.
4. Mantén un lenguaje técnico, impersonal y coherente, con especial cuidado en:
   - Tiempos verbales (infinitivo para procedimientos, sustantivos técnicos claros)
   - Unidades de medida
   - Coherencia normativa (si se menciona alguna norma técnica)
5. La estructura final debe contener las siguientes secciones en orden:
   - **Descripción**
   - **Materiales, herramientas y equipo**
   - **Procedimiento**
   - **Medición y forma de pago**
6. La sección **Procedimiento** debe estar redactado por parrafos y no debe ser enumerada. 
7. El resultado debe estar en formato Markdown y estar listo para incorporarse a un pliego técnico.

### Entrada:

{especificaciones_tecnicas}

**Especificación 1:**
[pega aquí la primera especificación]

**Especificación 2:**
[pega aquí la segunda especificación]

### Salida esperada:
Una única especificación técnica consolidada, con estructura estandarizada, sin contradicciones ni repeticiones, y con todo el contenido complementario correctamente integrado.
""")
    especificaciones = ""
    
    for i, especificacion in enumerate(state["especificaciones_tecnicas"]):
        encabezado = f"\n**Especificación {i+1}:**\n"
        try:
            contenido = encabezado + especificacion
            especificaciones += contenido
            
        except Exception as e:
            print(f"Error al leer el archivo: {e}")
            
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({
        "especificaciones_tecnicas": especificaciones,
        "titulo": state["titulo"]
    })
    
    state["especificacion_base"] = response
    
    console.print("------ fusionar_especificaciones ------", style="bold yellow")
    console.print("Especificación base generada: ", style="yellow")
    console.print(state["especificacion_base"], style="yellow")
    
    return state


# Nodo 2: Generación de contenido
def generar_contenido(state: State) -> State:
    # Genera la descripción y el procedimiento
    
    prompt = ChatPromptTemplate.from_template("""
A partir de la **especificación técnica proporcionada** al final, necesito generar la **Descripción** y el **Procedimiento** de la misma especificación, redactados de manera **genérica**, **totalmente reutilizable**, y en formato **Markdown (.md)**.

---

### Estilo y redacción general

- Profesional, técnico y claro, para ser utilizado en especificaciones reales de obra pública o privada.  
- Imita el estilo del ítem original si existe, pero adapta el contenido para ser **universalmente aplicable**.  
- **No inventar detalles nuevos.**  
- No incluir encabezados, ni títulos externos (solo el contenido textual).  
- Utilizar **negrita** (doble asterisco `**`) para resaltar términos técnicos, materiales, unidades o acciones relevantes.  

---

### Reglas para la sección "Descripción"

- Explicar **qué incluye la actividad** y **cuál es su propósito técnico**, sin mencionar valores específicos (espesor, cantidades, marcas, etc.).
- Si el título contiene un material o tipo de producto (ej. hormigón, acero), referenciarlo en términos generales.
- **No incluir valores numéricos concretos ni productos comerciales en esta sección.**

---

### Reglas para la sección "Procedimiento"

- Redactar en **varios párrafos técnicos secuenciales**, sin numeración de pasos.
- Utilizar la información base como guía, pero reescribirla de manera genérica.
- **No incluir valores específicos (como espesores, proporciones, cantidades) ni marcas comerciales.**
- En lugar de valores o nombres comerciales, escribir en forma genérica (ej. *espesor establecido*, *aditivo impermeabilizante*).
- Usar **negrita** para:
  - **Acciones clave**  
  - **Materiales y herramientas**  
  - **Unidades de medida genéricas** (ej. **metros cuadrados**)  
  - **Términos técnicos relevantes**  

---

### Reglas para "Parámetros Técnicos"

- Todos los valores concretos (ej. **espesor: 5 cm**, **pendiente mínima**, **resistencia del material**) deben extraerse del texto base y colocarse en esta sección.
- Si un parámetro no es obligatorio, puede ir acompañado de su valor por defecto sugerido.
- Esta sección sirve para **separar los valores configurables** y permitir que el cuerpo de la especificación sea reutilizable.

---

### Reglas para "Adicionales"

- Toda mención a herramientas, métodos, recomendaciones o elementos que **puedan variar según el proyecto** o **no son estrictamente parte de la actividad principal**, deben ir como **Adicionales**.
- Las actividades adicionales deben tener **nombre específico** y no deben llamarse "Otros".
  - Ejemplos válidos: `Preparación de superficie`, `Aditivos`, `Curado del hormigón`, `Verificación de pendientes`.
- Incluir una **descripción técnica y breve** de cada actividad complementaria.

---

Debes proporcionar tu respuesta en formato estructurado según el modelo definido.

### Especificación técnica base:

{especificacion_base}
""")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | llm.with_structured_output(Content)
    
    response = chain.invoke({
        "especificacion_base": state["especificacion_base"]
    })

    state["contenido"] = response
    console.print("Contenido generado: ", style="yellow")
    console.print(state["contenido"], style="yellow")

    return state

# Nodo 3: Formateo final
def generar_MEH(state: State) -> State:
    console.print("------ generar_MEH ------", style="bold yellow")
    
    prompt = ChatPromptTemplate.from_template("""
En función de la **especificación técnica generada** y la **especificación técnica base**, necesito generar la sección **"Materiales, Equipo, Herramientas y EPP"**, redactada de manera **genérica**, **reutilizable** y en **formato Markdown (.md)**.

---

### Instrucciones generales

- El contenido debe estar redactado **totalmente en español**, utilizando **nombres técnicos y comunes utilizados en Bolivia**.
- **No usar términos en inglés** en ningún caso (por ejemplo: *gloves*, *helmet*, *mask*). Usar siempre: *guantes*, *casco*, *mascarilla*, etc.
- La redacción debe ser clara, concreta y aplicable a diferentes tipos de obras.
- No incluir valores numéricos ni referencias comerciales.
- El contenido debe ser una **lista clara y estructurada**.

---

### Formato requerido (Markdown exacto):

- **Materiales**: [elementos consumibles como cemento, aditivos, clavos, etc.].  
- **Equipo**: [máquinas o equipos mayores, como mezcladoras, compactadoras, vibradoras, etc.].  
- **Herramientas**: [herramientas manuales o menores como palas, picostas, reglas metálicas,etc.].  
- **EPP**: [Elementos de protección personal como casco, guantes, botas de seguridad, mascarilla, chaleco reflectante, etc.].

---

Debes proporcionar tu respuesta en formato estructurado según el modelo definido.

### Especificación técnica generada:

{especificacion_generada}

### Especificación técnica base:

{especificacion_base}

""")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | llm.with_structured_output(MEH)
    
    response = chain.invoke({
        "especificacion_generada": state["contenido"],
        "especificacion_base": state["especificacion_base"]
    })

    state["MEH"] = response
    
    console.print("MEH generado: ", style="yellow")
    console.print(state["MEH"], style="yellow")
    
    return state

# Nodo 4: Generación de sección de Medición y Forma de Pago
def generar_medicion_pago(state: State) -> State:
    console.print("------ generar_medicion_pago ------", style="bold yellow")
    
    prompt = ChatPromptTemplate.from_template("""
A partir de la **especificación técnica generada**, necesito generar la sección **"Medición y Forma de Pago."**, redactada de manera **genérica**, **reutilizable** y en **formato Markdown (.md)**.

---

### Instrucciones generales

Redactar en **dos párrafos**:

1. **Medición y Verificación**:  
   - Indicar claramente la **forma de medir la actividad**.  
   - Especificar la **unidad de medida** en forma literal, seguida de su símbolo entre paréntesis, por ejemplo: **metros cuadrados (m²)**, **metros lineales (ml)**.  
   - Incluir la forma de verificar el resultado (por ejemplo: controles de nivel, espesor, resistencia, etc.).  
   - Si se menciona una empresa responsable, usar la forma: **"por [Nombre de la empresa]"**.

2. **Forma de Pago**:  
   - Describir cómo se realiza el pago.  
   - Indicar si está sujeto a condiciones, avances o verificaciones técnicas.

---

### Formato obligatorio

- El contenido debe ser entregado **en texto plano Markdown**, **sin usar bloques de código** ni triple comillas.  
- **No incluir** delimitadores como ```markdown.  
- El resultado debe comenzar directamente con el título **"### Medición y Forma de Pago."** y los dos párrafos requeridos.

---

### Especificación técnica generada:

{especificacion_generada}

""")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({
        "especificacion_generada": state["contenido"]
    })
    
    state["medicion_pago"] = response
    
    console.print("Medición y Forma de Pago generado: ", style="yellow")
    console.print(state["medicion_pago"], style="yellow")
    
    return state

def consolidar_documento(state: State) -> State:
    console.print("------ consolidar_documento ------", style="bold yellow")
    
    def render_parametros_tecnicos_md(parametros: List[ParametroTecnico]) -> str:
        if not parametros:
            return "_No se definieron parámetros técnicos._"

        tabla = "### Parámetros Técnicos\n\n"
        tabla += "| Parámetro Técnico | Opciones Válidas | Valor por Defecto |\n"
        tabla += "|-------------------|------------------|--------------------|\n"
        for p in parametros:
            tabla += f"| {p.Parámetro_Técnico} | {p.Opciones_válidas} | {p.Valor_por_defecto} |\n"
        return tabla

    def render_adicionales_md(adicionales: List[Adicional]) -> str:
        if not adicionales:
            return "_No se definieron actividades adicionales._"

        resultado = "### Adicionales\n\n"
        for a in adicionales:
            resultado += f"- **{a.actividad}**: {a.descripcion.strip()}\n"
        return resultado
    
    documento_final = f"""
## {state["titulo"]}
    
### Descripción.

{state["contenido"].descripcion}

### Materiales, Herramientas y Equipo.

- **Materiales**: {state["MEH"].materiales}
- **Equipo**: {state["MEH"].equipo}
- **Herramientas**: {state["MEH"].herramientas}
- **EPP**: {state["MEH"].EPP}

### Procedimiento.

{state["contenido"].procedimiento}

{state["medicion_pago"]}
    
{render_parametros_tecnicos_md(state["contenido"].parametros_tecnicos)}

{render_adicionales_md(state["contenido"].adicionales)}
"""
    
    state["documento_final"] = documento_final
    
    console.print("Documento final generado: ", style="yellow")
    console.print(documento_final, style="yellow")
    
    return state

# Creación del grafo
def crear_grafo() -> Graph:
    workflow = StateGraph(State)
    
    # Agregar nodos
    workflow.add_node("fusionar_especificaciones", fusionar_especificaciones)
    workflow.add_node("generar_contenido", generar_contenido)
    workflow.add_node("generar_MEH", generar_MEH)
    workflow.add_node("generar_medicion_pago", generar_medicion_pago)
    workflow.add_node("consolidar_documento", consolidar_documento)
    
    # Definir el flujo
    workflow.add_edge("fusionar_especificaciones", "generar_contenido")
    workflow.add_edge("generar_contenido", "generar_MEH")
    workflow.add_edge("generar_MEH", "generar_medicion_pago")
    workflow.add_edge("generar_medicion_pago", "consolidar_documento")
    
    # Definir el nodo de entrada y salida
    workflow.set_entry_point("fusionar_especificaciones")
    workflow.set_finish_point("consolidar_documento")
    
    return workflow.compile()

# Función principal para ejecutar el grafo
def generar_documento(titulo: str, especificaciones_tecnicas: List[str], adicionales: str = "") -> str:
    grafo = crear_grafo()
    
    estado_inicial = State(
        titulo=titulo,
        especificaciones_tecnicas=especificaciones_tecnicas,
        adicionales=adicionales,
        documento_final=""
    )
    
    resultado = grafo.invoke(estado_inicial)
    return resultado["documento_final"] 