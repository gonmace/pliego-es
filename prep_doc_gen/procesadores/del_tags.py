import sys
import os
from bs4 import BeautifulSoup

def eliminar_tags_html(ruta_entrada, tags_a_eliminar):
    try:
        print(f"Procesando archivo: {ruta_entrada}")
        print(f"Tags a eliminar: {tags_a_eliminar}")
        
        with open(ruta_entrada, "r", encoding="utf-8") as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # Eliminar los tags indicados
        for tag in tags_a_eliminar:
            elementos = soup.find_all(tag)
            print(f"Eliminando {len(elementos)} elementos del tag '{tag}'")
            for elemento in elementos:
                elemento.decompose()

        # Preparar nombre de salida: mismo nombre, precedido por "13_"
        nombre_archivo = os.path.basename(ruta_entrada)
        nuevo_nombre = "13_" + nombre_archivo
        print(f"Nuevo nombre del archivo: {nuevo_nombre}")
        
        # El directorio output debe estar dentro del directorio temp
        output_dir = os.path.join(os.path.dirname(ruta_entrada), 'output')
        print(f"Directorio de salida: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Guardar en el directorio output
        ruta_salida = os.path.join(output_dir, nuevo_nombre)
        print(f"Ruta completa de salida: {ruta_salida}")

        # Guardar el HTML modificado
        with open(ruta_salida, "w", encoding="utf-8") as file:
            file.write(soup.prettify())

        print(f"✅ Tags eliminados: {', '.join(tags_a_eliminar)}")
        print(f"📁 Archivo guardado como: {ruta_salida}")
        print(f"¿El archivo existe? {os.path.exists(ruta_salida)}")
        
        # Retornar solo el nombre del archivo
        return nuevo_nombre
        
    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {ruta_entrada}")
        print(f"Error detallado: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Error al procesar el archivo: {e}")
        print(f"Error detallado: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python eliminar_tags.py archivo.html tag1 [tag2 ...]")
        print("Ejemplo: python eliminar_tags.py documento.html table ol ul")
    else:
        archivo_entrada = sys.argv[1]
        tags_a_eliminar = sys.argv[2:]  # Lista de tags
        eliminar_tags_html(archivo_entrada, tags_a_eliminar)
