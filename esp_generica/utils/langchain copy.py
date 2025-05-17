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

---

### 📄 A continuación se {parrafo2}:

##  Acera De Cemento e=5 cm 

###  Descripción 

La actividad consiste en la construcción de una acera de cemento con un espesor de 5 cm. Este tipo de infraestructura está diseñada para proporcionar un camino seguro y duradero para el tránsito peatonal en las instalaciones de la planta. La acera será construida utilizando técnicas y materiales específicos que garanticen su funcionalidad y longevidad. 

###  Materiales, herramientas y equipo 

  * Materiales: Cemento Portland, arena, grava, agua, y mallazo de refuerzo si es necesario. 
  * Equipos: Mezcladora de concreto, vibradora de concreto. 
  * Herramientas: Palas, nivel, reglas, cortadora de concreto, carretillas, cintas métricas, moldes o formas. 
  * Personal: Ingenieros civiles, operarios de construcción, ayudantes. 
  * EPP: Cascos, guantes de trabajo, gafas de seguridad, botas con puntera de acero. 



###  Procedimiento 

Comenzar con la preparación del sitio, asegurando que la superficie esté nivelada y compactada adecuadamente. Seguir con la colocación de formas o moldes que definirán los límites y la forma de la acera. 

Preparar la mezcla de concreto en la proporción correcta utilizando cemento, arena, grava y agua. Verificar la consistencia del concreto para asegurar una buena trabajabilidad y durabilidad. Verter el concreto en las formas preparadas, utilizando técnicas de vibrado para eliminar las burbujas de aire y asegurar una superficie uniforme y compacta. 

Nivelar el concreto con reglas y alisar la superficie con llanas. Permitir que el concreto cure adecuadamente, aplicando métodos de curado como el riego regular o la utilización de compuestos de curado para prevenir la evaporación rápida del agua. 

Retirar las formas una vez que el concreto haya alcanzado suficiente dureza y realizar los cortes de contracción para controlar las fisuras. Limpiar el área y asegurar la disposición adecuada de los residuos generados. 

EMBOL S.A. se deslinda de cualquier responsabilidad asociada a la actividad de transporte y disposición de los residuos generados. La empresa contratista es responsable de llevar a cabo la actividad de manera segura y conforme a todas las normativas y regulaciones aplicables. 

###  Medición y Precio 

La medición para el pago de esta actividad se realizará en metros cuadrados, basándose en la superficie total efectivamente construida conforme a las especificaciones técnicas. 

El pago se efectuará de acuerdo con la cantidad de metros cuadrados de acera de cemento completados, siguiendo los términos y condiciones del contrato establecido con el contratista. El pago final estará condicionado al avance y aprobación de EMBOL S.A., asegurando que la construcción cumpla con todos los estándares de calidad y seguridad. 

""")

parrafo1 = "la especificación técnica base"

parrafo2 = "adjunta la especificación técnica base"














from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt_template = ChatPromptTemplate.from_template(
"""Generar una especificación técnica **genérica** **totalmente reutilizable** en formato **Markdown (.md)** a partir de **{parrafo1}** proporcionada al final.

## Titulo.

La especificación técnica genérica debe tener el siguiente título: ## {titulo}

### Estructura obligatoria.

Mantener las siguientes secciones, en el mismo orden y formato:

- Descripción.
- Materiales, herramientas y equipo.
- Procedimiento.
- Medición y Forma de Pago.
- Parámetros Técnicos Recomendados.
- Adicionales.

### Estilo y redacción

Profesional, técnico y claro, como en especificaciones reales de obra.  
Imitar el estilo del ítem original en redacción y tono.
No incluir encabezados externos al contenido generado.
Usar **negrita** (doble asterisco `**`) para resaltar términos clave o técnicos importantes unicamente en el **Procedimiento** y **Medicion y Forma de Pago**, tales como unidades de medición (ej. **metros lineales**) y acciones relevantes del procedimiento

### Reglas de generalización

1. Redactar el documento basándose exclusivamente en el contenido de **{parrafo1}**.
2. **No conservar valores técnicos específicos** (ej. dimensiones, marcas, modelos). Reemplazarlos por descripciones genéricas o variables.
   - Ejemplo: Reemplazar "cinta 3M de 2 pulgadas" por "cinta antideslizante".
3. No inventar actividades o materiales que no estén mencionados en **{parrafo1}**.
4. **Todas las actividades descritas en {parrafo1} deben estar incluidas y ordenadas lógicamente**.
5. Si se infieren tareas finales relevantes (limpieza, retiro de moldes, etc.), pueden ser incluidas si no contradicen la base.
6. Las actividades complementarias deben ir solo en la sección **Adicionales**.
7. El contenido debe ser aplicable a distintas actividades similares.

### Redacción de la sección "Descripción"

Redactar en forma general pero técnica, describiendo **qué abarca la actividad**, **qué objetivo técnico o funcional tiene**.  
Incorporar el **nombre de la especificación técnica** y el tipo de material, espesor, si están presentes en el título (ej. "[Material_principal]" y "[espesor]").  
Mantener una redacción similar a **{parrafo1}**, pero reemplazando valores, variables en expresiones genéricas.
No inventar nuevas aplicaciones, mantener el propósito general tal como se deduce de {parrafo1}.

### Reglas de la sección "Materiales, herramientas y equipo"

Listar con formato exacto:
- **Materiales**: [elementos separados por comas].  
- **Equipo**: [máquinas y dispositivos].  
- **Herramientas**: [herramientas manuales o menores].  
- **EPP**: [elementos de protección personal].

### Reglas de la sección "Procedimiento"

Redactar en **múltiples párrafos técnicos secuenciales**, sin numerar pasos.
Usar la información de **{parrafo1}** para generar el procedimiento.
Aplicar **negrita** para resaltar:
- **Acciones clave**
- **Términos técnicos**
- **Herramientas y materiales**
- **Unidades de medida**
Evitar mencionar la palabra “procedimiento” dentro del contenido.

### Reglas de la sección "Materiales, herramientas y equipo"

Listar con formato exacto:
- **Materiales**: [elementos separados por comas].  
- **Equipo**: [máquinas y dispositivos].  
- **Herramientas**: [herramientas manuales o menores].  
- **EPP**: [elementos de protección personal].

### Reglas específicas para "Medición y Forma de Pago"

Redactar en **tres párrafos**, correspondientes a:  
  **Medición**,  
  **Verificación**,  
  **Pago**.
En el primer párrafo (**Medición**), debe indicarse claramente: La forma de medir la actividad y la **unidad de medida** expresada en forma literal y con símbolo entre paréntesis (por ejemplo: **metros cuadrados (m²)**, **metros lineales (ml)**, etc.).  
En el segundo párrafo (**Verificación**), si se menciona una empresa responsable, redactar como: **"por [Nombre de la empresa]"**, evitando expresiones como "la empresa [Nombre]".
En el tercer párrafo (**Pago**), debe indicarse claramente la forma de pago y si la misma esta sujeta algun resultyado (ejem. resitencia del Hormigón)
Aplicar **negrita** únicamente a acciones relevantes o unidades de medida en esta sección (ej. **verificación**, **metros cuadrados**, **alineación**, etc.).

### Reglas de la sección "Parámetros Técnicos Recomendados"

En la sección incluir una tabla con tres columnas:
- **Parámetro Técnico**
- **Opciones válidas**
- **Valor por defecto**  

### Reglas de la sección "Adicionales".

En la sección, listar actividades complementarias comunes a este tipo de ítem. No deben estar incluidas en la redacción principal.
- Formato: **Subtítulo** seguido de **descripción técnica breve**.
- No incluir inspecciones, mantenimiento ni tareas administrativas.
*Ejemplo:*  
**Preparación de terreno**: Limpieza, nivelación y compactación del terreno previo a la instalación del sistema.

---

## 🚫 Restricciones
- No generar medidas, marcas ni modelos comerciales.
- No agregar objetivos técnicos no mencionados en **{parrafo1}**.
- No incluir cláusulas contractuales.
- No modificar la estructura ni el orden del documento.
- El contenido debe ser reutilizable y adaptable a proyectos similares.

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
    
    print("=======")
    print(especificaciones_tecnicas)
    print("=======")
    
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