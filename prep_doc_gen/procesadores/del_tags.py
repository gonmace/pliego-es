import sys
import os
from bs4 import BeautifulSoup

def eliminar_tags_html(ruta_entrada, tags_a_eliminar):
    try:
        with open(ruta_entrada, "r", encoding="utf-8") as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # Eliminar los tags indicados
        for tag in tags_a_eliminar:
            for elemento in soup.find_all(tag):
                elemento.decompose()

        # Preparar nombre de salida: mismo nombre, precedido por "12_"
        directorio, nombre_archivo = os.path.split(ruta_entrada)
        nuevo_nombre = "12_" + nombre_archivo
        ruta_salida = os.path.join(directorio, nuevo_nombre)

        # Guardar el HTML modificado
        with open(ruta_salida, "w", encoding="utf-8") as file:
            file.write(soup.prettify())

        print(f"✅ Tags eliminados: {', '.join(tags_a_eliminar)}")
        print(f"📁 Archivo guardado como: {ruta_salida}")
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {ruta_entrada}")
    except Exception as e:
        print(f"❌ Error al procesar el archivo: {e}")
    
    return ruta_salida

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python eliminar_tags.py archivo.html tag1 [tag2 ...]")
        print("Ejemplo: python eliminar_tags.py documento.html table ol ul")
    else:
        archivo_entrada = sys.argv[1]
        tags_a_eliminar = sys.argv[2:]  # Lista de tags
        eliminar_tags_html(archivo_entrada, tags_a_eliminar)
