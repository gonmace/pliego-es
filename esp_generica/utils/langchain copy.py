from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt_template = ChatPromptTemplate.from_template(
"""Generar una especificación técnica **genérica** **totalmente reutilizable** en formato **Markdown (.md)** a partir de {parrafo1} más abajo.

La especificación técnica genérica debe tener el siguiente título: 
**## {titulo}**

---

*Estructura obligatoria*

Mantener las siguientes secciones, en el mismo orden y formato:

### Descripción.

### Materiales, herramientas y equipo.

### Procedimiento.

### Medición y Forma de Pago.

#### Parámetros Técnicos Recomendados

#### Adicionales

---

*Estilo y redacción*

- Profesional, técnico y claro, como en especificaciones reales de obra.  
- Imitar el estilo del ítem original en redacción y tono.
- No incluir encabezados externos al contenido generado.

---

*Reglas de generalización*

1. Considerar el Título como el parametro principal para redactar la especificación técnica.

2. **No conservar valores técnicos específicos** (ej. dimensiones, marcas, modelos). Reemplazarlos por descripciones genéricas o variables.
   - Ejemplo: Reemplazar "cinta 3M de 2 pulgadas" por "cinta antideslizante de ancho estándar".
   
3. No agregar actividades adicionales que no estén en {parrafo1}. Las actividades que consideres adicionales, deben ir en la sección adicionales.

4. Con el mejor criterio intentar incluir las actividades que estan en {parrafo1} en el procedimiento.

5. Agregar las verificaciones y mediciones que consideres necesarias y que no estén en {parrafo1}.

6. Agregar actividades finales que consideres necesarias en base a {parrafo1}.

---

*Secciones específicas*

1. **Descripción**: Describir el objetivo de la actividad en base a {parrafo1}.

2. **Materiales, herramientas y equipo**: Describe en forma de lista los siguientes elementos utilizados en la actividad, agrupados en los subtítulos indicados. La descripción debe ser concreta, técnica y específica. Usa el siguiente formato exacto (no añadir texto adicional):
- **Materiales**: [lista de materiales separados por comas].  
- **Equipo**: [lista de equipos separados por comas].  
- **Herramientas**: [lista de herramientas separadas por comas].  
- **EPP**: [lista de elementos de protección personal separados por comas].

3. **Procedimiento**: Desarrollar el procedimiento en varios párrafos rescatando y mejorando el procedimiento en {parrafo1}. El texto debe tener **fluidez técnica**, con redacción formal y secuencial. Se debe usar **negrita** para resaltar:
- **Términos clave de la actividad**  
- **Unidades de medida**  
- **Herramientas, materiales y acciones técnicas**  
- **Verbos técnicos relevantes**
Evitar mencionar el término **procedimiento** en el texto.

4. **Medición y Forma de Pago**: Redactar siempre en **tres párrafos**, correspondientes a las siguientes secciones:

- **Medición**: Describir claramente la forma en que se medirá la actividad. Indicar la **unidad de medida** en forma literal seguida de su símbolo entre paréntesis, por ejemplo: **metros cuadrados (m²)**, **metros lineales (ml)**, etc.

- **Verificación**: Señalar cómo se realizará la **verificación** de la actividad ejecutada. Si se menciona una empresa responsable, redactar como: **"por [Nombre de la empresa]"**, evitando construcciones como "la empresa [Nombre]".

- **Pago**: Explicar la forma en que se calculará el **pago**, con base en la medición y verificación descritas.

Se debe aplicar **negrita** a:
- **Acciones relevantes** (ej.: **verificación**, **medición**, **alineación**)
- **Unidades de medida** (ej.: **metros cuadrados**, **metros lineales**, etc.)

5. **Parámetros Técnicos Recomendados**: Incluir una tabla con tres columnas:
   - **Parámetro Técnico**
   - **Opciones válidas**
   - **Valor por defecto**

6. **Adicionales**: Incluir una **lista de actividades complementarias** que puedan integrarse a la especificación técnica. Estas deben ser **actividades constructivas** directamente relacionadas con el proceso principal, que se ejecutarían **antes o después** de la actividad descrita.

- Cada actividad adicional debe presentarse con un **subtítulo claro** y una **descripción breve, concreta y técnica**.
- No se deben incluir actividades de **mantenimiento**, **inspección**, ni procesos administrativos.

*Ejemplo:*  
**Preparación de suelos de fundación**: Nivelación y compactación del terreno natural antes del vaciado del piso de hormigón armado.

---

*Restricciones*

- No agregar objetivos que no se encuentre en el item original.
- No inventar detalles técnicos que no estén en el ítem original.
- No mantener marcas comerciales, medidas específicas ni textos contractuales.
- No modificar el contexto de la sección Medicion y Forma de Pago.
- El contenido debe ser completamente reutilizable para otros casos similares.

{adicionales}
---

A continuación se {parrafo2}:

{especificaciones_tecnicas}
""")

parrafo1_singular = "la especificación técnica base"
parrafo1_plural = "las especificaciones técnicas base"

parrafo2_singular = "presenta la especificación técnica original"
parrafo2_plural = "presentan las especificaciones técnicas originales"

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