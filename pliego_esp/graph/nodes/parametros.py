# graph/nodes/inicio.py
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.callbacks.openai_info import OpenAICallbackHandler
from langchain.callbacks.manager import CallbackManager

from pliego_esp.graph.configuration import Configuration
from pliego_esp.graph.state import State

from rich.console import Console
console = Console()

async def parametros(state: State, *, config: RunnableConfig) -> State:
    console.print("-----Parametros-----", style="bold yellow")
    configuration = Configuration.from_runnable_config(config)
    
    # Configurar el modelo con el callback manager
    chat_model = ChatOpenAI(
        model=configuration.llm_4o_mini,
        temperature=0.0
    ,
    )
    prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "Eres un experto en construcción encargado de ajustar tablas técnicas de especificaciones."),
    ("human",
     """Vas a trabajar con una **tabla técnica en formato Markdown** que contiene los siguientes campos:

- `"Parámetro Técnico"`: nombre del parámetro que debe ser evaluado.
- `"Opciones válidas"`: lista de valores técnicamente aceptables para ese parámetro.
- `"Valor por defecto"`: el valor que se debe usar si no se proporciona otro.
- `"Valor Asignado"`: campo que debes completar.

También recibirás una lista de **parámetros clave** del proyecto, que podrían coincidir con algunos de los parámetros técnicos.

---

### Tu tarea:

Procesa la tabla **fila por fila** siguiendo exactamente estos pasos en orden:

#### Paso 1: Analizar el parámetro técnico de esa fila.
- Determina cuál es el parámetro técnico.

#### Paso 2: Buscar coincidencia con los parámetros clave.
- Revisa si algún valor de `{parametros_clave}` **coincide en concepto** con ese parámetro.
  - Si sí: asigna ese valor al campo `"Valor Asignado"`.
  - Si no: ve al paso 3.

#### Paso 3: Usar valor por defecto si no hay coincidencia.
- Si no encontraste un valor desde los parámetros clave, y `"Valor por defecto"` tiene un valor distinto de `-`, copia ese valor en `"Valor Asignado"`.

#### Paso 4: Validar el valor asignado.
- Compara el `"Valor Asignado"` con las `"Opciones válidas"` para ese parámetro.
  - Si el valor coincide exactamente o es una redacción técnica aceptable (por ejemplo: incluye una de las opciones válidas como palabra central), **se acepta tal cual**.
  - Si el valor no aparece o representa un significado extendido, agrega un asterisco `*` al final.

#### Paso 5: Si el parámetro clave no coincide con ningún parámetro técnico existente, crea una nueva fila.
- Usa como nombre del parámetro técnico un título adecuado. Si no puedes generar uno, usa `"Otros"`.
- Deja `"Opciones válidas"` y `"Valor por defecto"` vacíos o con guiones.
- Escribe el valor del parámetro clave en `"Valor Asignado"`, aplicando la validación del paso 4.

---

### Tabla original:

{tabla_parametros_md}

### Parámetros clave del proyecto:

{parametros_clave}

---

### Resultado

Devuelve la tabla Markdown resultante con la columna `"Valor Asignado"` completada, **siguiendo el procedimiento anterior estrictamente, fila por fila**.  
No agregues explicaciones ni comentarios, solo la tabla completa.
""")
])
    

# Eres un asistente experto en redacción de pliegos técnicos para construcción.
# Por favor genera únicamente un arreglo JSON con los parámetros técnicos a ser usados para una especificación técnica.

# ### Instrucciones detalladas para construir el JSON:

# 1. Agrega los parámetros de la tabla que cuentan con **valor por defecto**, debiendo ser el **valor** el **valor por defecto**.

# 2. Si un parámetro clave coincide con un parámetro del JSON (generado en el paso 1), reemplaza su valor por el del parámetro clave, **solo si se refieren claramente al mismo concepto técnico** (por ejemplo: "Tipo de acabado" y "Acabado texturizado").
#    - **No consideres coincidencias ambiguas o que representen conceptos diferentes**, aunque tengan palabras similares (por ejemplo, "Tipo de pintura" ≠ "Color de pintura").
#    - No agregues nuevos parámetros que no estén presentes en el paso 1.


# """),
#     ("human", """
# Tienes la siguiente tabla de parámetros técnicos:

# {tabla_parametros_md}

# Y una lista de parámetros clave:

# {parametros_clave}

# Devuelve una lista JSON como:
# [
# {{ "parámetro": "Tipo de acabado", "valor": "texturizado" }},
# ...
# ]
# """)])

    chain = prompt | chat_model | StrOutputParser()
    
    # Inputs del usuario
    inputs = {
        "tabla_parametros_md": state["parametros_pliego"],
        "parametros_clave": state["parametros_clave"],
    }
    
    # # Crear un callback handler para OpenAI
    callback_handler = OpenAICallbackHandler()
    # # Llamada y parsing con el callback manager
    response = await chain.ainvoke(
        inputs,
        config={"callbacks": [callback_handler]}
    )
    console.print(response, style="bold yellow")
    # # Actualización del estado con la respuesta procesada
    # state["parametros_pliego"] = json_response
    
    # # Actualizar el costo de tokens en el estado
    # state["token_cost"] = callback_handler.total_cost
    
    # console.print(json_response, style="bold yellow")
    # console.print(f"Total Cost (USD): ${str(callback_handler.total_cost)}")
    # console.print(f"Prompt Tokens: {callback_handler.prompt_tokens}")
    # console.print(f"Completion Tokens: {callback_handler.completion_tokens}")
    # console.print(f"Successful Requests: {callback_handler.successful_requests}")

    # console.print(20*"-", style="bold yellow")
    state["messages"] = [
        HumanMessage(content=f"Pliego base: {state['pliego_base']}\nTitulo: {state['titulo']}\nParametros clave: {state['parametros_clave']}\nAdicionales: {state['adicionales']}")
    ]
    
    return state