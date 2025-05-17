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