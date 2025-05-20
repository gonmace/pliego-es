import sys
import re
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# 1. Define tu modelo (puede ser gpt-4o, gpt-4, etc.)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

prompt_template = ChatPromptTemplate.from_template("""
Eres un especialista en redacción técnica de obras civiles. Tu tarea es **mejorar una lista de títulos de actividades de construcción** para que sean adecuados para documentos oficiales como especificaciones técnicas, presupuestos u hojas de metrados.

### Reglas de redacción:

1. **No utilices verbos** como "Colocado", "Vaciado", "Provisión", "Reparación", "Pintado", "Cambio", "Instalación", etc.  
   - En lugar de ello, describe el **elemento construido**, no el proceso.
   - Ejemplo: "Vaciado de piso de H°A°" → "Piso de Hormigón Armado".

2. **Mantén información técnica relevante**, como materiales, espesor, diámetro, tipo de tráfico, etc.
   - "e=5cm" → "Espesor 5 cm"
   - "Ø 1/4”" → "Diámetro 1/4”"
   - "H°A°" → "Hormigón Armado"
   - Usa unidades normalizadas: cm, mm, m (separadas con espacio)

3. **Elimina frases como "incluye...", "con compactado..."**, a menos que sea parte integral del tipo de elemento (ej.: "Piso antideslizante").

4. Utiliza una **estructura nominal técnica y concisa**. El título debe poder usarse en documentos como partidas de obra, sin encabezados ni artículos innecesarios.

### Formato de salida:
Devuelve la respuesta como un arreglo JSON con el siguiente formato:

[
  {{ "original": "TÍTULO ORIGINAL", "mejorado": "TÍTULO MEJORADO" }},
  ...
]

---

Títulos a mejorar:
{titulos}

Devuelve solo el JSON, sin explicaciones ni comentarios adicionales.
""")

def limpiar_texto(texto):
    # Quitar saltos de línea, tabs, múltiples espacios y dejar solo un espacio entre palabras
    texto = re.sub(r'\s+', ' ', texto.strip())
    return texto

def extraer_titulos(ruta_archivo, tag_titulo):
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            contenido = f.read()
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {ruta_archivo}")
        sys.exit(1)

    soup = BeautifulSoup(contenido, "html.parser")
    elementos = soup.find_all(tag_titulo)
    titulos_limpios = [limpiar_texto(elem.get_text()) for elem in elementos]
    
    titulos_input = "\n".join([f"- {t}" for t in titulos_limpios])
    
    chain = prompt_template | llm | JsonOutputParser()
    
    result = chain.invoke({"titulos": titulos_input})
    print(result)
    return result


