from bs4 import BeautifulSoup
import sys
import os

def limpiar_texto(texto):
    """
    Elimina saltos de línea, espacios al inicio/final y colapsa espacios múltiples.
    """
    texto = texto.replace("\n", " ").replace("\r", " ")
    texto = ' '.join(texto.strip().split())
    return texto

def limpiar_li_con_p(html):
    soup = BeautifulSoup(html, "html.parser")

    for li in soup.find_all("li"):
        hijos = li.find_all(recursive=False)

        # Si el <li> tiene exactamente un hijo y es <p>
        if len(hijos) == 1 and hijos[0].name == "p":
            texto_limpio = limpiar_texto(hijos[0].get_text())
            hijos[0].decompose()
            li.string = texto_limpio

    return soup.prettify()

def eliminar_p_dentro_li(ruta_entrada, base):
    
    with open(ruta_entrada, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Procesar el HTML para eliminar las etiquetas p dentro de li
    html_limpio = limpiar_li_con_p(html)
    
    # Crear ruta de salida con prefijo
    directorio, nombre = os.path.split(ruta_entrada)
    nombre_salida = "14_" + nombre
    ruta_salida = os.path.join(directorio, nombre_salida)

    # Guardar el HTML procesado
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html_limpio)

    print(f"✅ Archivo procesado y guardado como: {ruta_salida}")

    return ruta_salida

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python limpiar_li.py <archivo_entrada.html>")
        sys.exit(1)

    archivo_entrada = sys.argv[1]
    eliminar_p_dentro_li(archivo_entrada)
