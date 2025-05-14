from bs4 import BeautifulSoup
import re
import sys
import os

def limpiar_texto(texto):
    # Elimina saltos de línea, tabs, múltiples espacios
    texto = texto.replace("\n", " ").replace("\r", " ")
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def limpiar_etiquetas_texto(html, etiquetas):
    soup = BeautifulSoup(html, "html.parser")

    for etiqueta in etiquetas:
        for tag in soup.find_all(etiqueta):
            # Limpiar el texto del tag
            if tag.string:
                texto_limpio = limpiar_texto(tag.string)
                tag.string.replace_with(texto_limpio)
            elif tag.text:
                # Si tiene contenido interno como <strong>, aplicar limpieza al texto completo
                contenido_limpio = limpiar_texto(tag.get_text())
                tag.clear()
                tag.append(contenido_limpio)
            
            # Asegurar que no haya espacios al inicio o final del contenido del tag
            if tag.string:
                tag.string = tag.string.strip()
            elif tag.text:
                tag.string = tag.text.strip()

    return soup.prettify()

def procesar_archivo_con_prefijo(ruta_entrada, prefijo="14_"):
    with open(ruta_entrada, "r", encoding="utf-8") as f:
        html = f.read()

    etiquetas = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']
    html_limpio = limpiar_etiquetas_texto(html, etiquetas)

    directorio, nombre = os.path.split(ruta_entrada)
    nombre_salida = prefijo + nombre
    ruta_salida = os.path.join(directorio, nombre_salida)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html_limpio)

    print(f"✅ Archivo limpio guardado como: {ruta_salida}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python limpiar_texto_html.py <archivo_entrada.html>")
        sys.exit(1)

    archivo_entrada = sys.argv[1]
    procesar_archivo_con_prefijo(archivo_entrada)
