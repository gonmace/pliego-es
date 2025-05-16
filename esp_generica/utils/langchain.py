from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt_template = ChatPromptTemplate.from_template(
"""Generar una especificación técnica **genérica** **totalmente reutilizable** en formato **Markdown (.md)** a partir de **{parrafo1}** proporcionada al final.

La especificación técnica genérica debe tener el siguiente título:

## {titulo}

### 📑 Estructura obligatoria

Mantener las siguientes secciones, en el mismo orden y formato:

### Descripción.

### Materiales, herramientas y equipo.

### Procedimiento.

### Medición y Forma de Pago.

#### Parámetros Técnicos Recomendados

#### Adicionales

---

### ✍️ Estilo y redacción

- Redacción profesional, técnica y clara, similar a una especificación de obra real.
- Imita el tono del ítem original.
- No agregar encabezados adicionales fuera de los definidos en la estructura.

---

### ⚙️ Reglas de generalización

1. Utilizar el **título** como parámetro principal para redactar la especificación técnica.
2. **Eliminar valores específicos** (dimensiones, marcas, modelos). Sustituir por descripciones genéricas o variables.  
   Ejemplo: reemplazar *"cinta 3M de 2 pulgadas"* por *"cinta antideslizante de ancho estándar"*.
3. **No agregar actividades nuevas** que no estén en **{parrafo1}**. Las actividades complementarias deben ir exclusivamente en la sección **Adicionales**.
4. **Incluir exclusivamente las actividades que estén en {parrafo1}**.  
   No agregar elementos constructivos adicionales como **mallas de refuerzo, aditivos, moldes u otros componentes técnicos** si no están expresamente mencionados en dicha base. Esas actividades deben ir en la sección **Adicionales**.
4. Incluir **todas las actividades que esten en {parrafo1}**, mejorando redacción y orden.
5. Agregar las verificaciones y mediciones que consideres necesarias y que estén en **{parrafo1}**.
6. Incluir **actividades finales relevantes** si se infieren del **{parrafo1}**.

---

### 🧩 Instrucciones por sección

### 1. **Descripción**
Describir el objetivo principal de la actividad en base a la **{parrafo1}**.

### 2. **Materiales, herramientas y equipo**
Incluir una lista agrupada en los siguientes subtítulos, con redacción concreta y técnica. Usar exactamente este formato:

- **Materiales**: [lista separada por comas].  
- **Equipo**: [lista separada por comas].  
- **Herramientas**: [lista separada por comas].  
- **EPP**: [lista separada por comas].

### 3. **Procedimiento**
Redactar en **varios párrafos**, con estilo fluido, técnico y secuencial. Basado en **{parrafo1}**, mejorando su claridad.

Aplicar **negrita** a:
- **Términos clave de la actividad**
- **Unidades de medida**
- **Herramientas, materiales y acciones técnicas**
- **Verbos técnicos relevantes**

Evitar el uso del término **procedimiento** dentro del contenido.

### 4. **Medición y Forma de Pago**
Redactar siempre en **tres párrafos**, uno por subtema:

- **Medición**: Describir la forma de medir la actividad. Incluir la **unidad de medida** con nombre y símbolo (ej. **metros cuadrados (m²)**).
- **Verificación**: Indicar cómo se verificará la ejecución. Si se menciona una empresa, usar: **"por [Nombre de la empresa]"**.
- **Pago**: Indicar cómo se calculará el pago, basado en la medición y verificación.

Usar **negrita** para acciones clave y unidades de medida.

### 5. **Parámetros Técnicos Recomendados**
Incluir una tabla con las siguientes columnas:
- **Parámetro Técnico**
- **Opciones válidas**
- **Valor por defecto**

### 6. **Adicionales**
Incluir una lista de actividades **constructivas complementarias** que puedan ejecutarse **antes o después** de la actividad principal.

- Cada entrada debe tener un **subtítulo** y una **descripción técnica breve y concreta**.
- No incluir actividades de **mantenimiento**, **inspección**, ni actividades administrativas.

*Ejemplo:*  
**Preparación de suelos de fundación**: Nivelación y compactación del terreno natural antes del vaciado del piso de hormigón armado.

---

### 🚫 Restricciones

- No inventar objetivos técnicos fuera del ítem original.
- No crear detalles técnicos no presentes en el documento base.
- No incluir marcas, medidas exactas ni cláusulas contractuales.
- No modificar el contexto de la sección **Medición y Forma de Pago**.
- El contenido debe ser genérico y reutilizable para ítems similares.

{adicionales}
---

### 📄 A continuación se {parrafo2}:

{especificaciones_tecnicas}
""")

parrafo1_singular = "la especificación técnica base"
parrafo1_plural = "las especificaciones técnicas base"

parrafo2_singular = "adjunta la especificación técnica base"
parrafo2_plural = "adjuntan las especificaciones técnicas base"

def generar_documento(archivos, adicionales, titulo):
    
    parrafo1 = parrafo1_plural if len(archivos) > 1 else parrafo1_singular
    parrafo2 = parrafo2_plural if len(archivos) > 1 else parrafo2_singular
    especificaciones_tecnicas = "---"
    adicionales_str = ""
    
    if len(adicionales) > 0:
        adicionales_str = "*Adicionales*\n" + adicionales
    
    if len(archivos) > 1:    
        for i, archivo in enumerate(archivos):
            encabezado = f"\n\nEspecificación técnica {i+1}:\n---\n"
            try:
                # Leer el contenido del archivo subido
                contenido = archivo.read().decode('utf-8')
                contenido = encabezado + contenido
                especificaciones_tecnicas += contenido
                # Resetear el puntero del archivo para futuras lecturas
                archivo.seek(0)
            except Exception as e:
                print(f"Error al leer el archivo: {e}")
    
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
    )
    
    chain = prompt_template | llm | StrOutputParser()
    
    response = chain.invoke({
        "titulo": titulo,
        "parrafo1": parrafo1,
        "parrafo2": parrafo2,
        "especificaciones_tecnicas": especificaciones_tecnicas,
        "adicionales": adicionales_str
    })
    
    return response