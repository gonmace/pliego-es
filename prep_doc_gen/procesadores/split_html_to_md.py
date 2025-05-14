import os
import re
import sys
from bs4 import BeautifulSoup
import html2text

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text.strip('-')[:80]

def html_to_markdown(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0  # No wrap text
    return h.handle(html_content)

def extraer_y_convertir(ruta_archivo, etiqueta='h2', output_dir="secciones", formato="md"):
    """
    Extrae secciones del archivo HTML basado en la etiqueta especificada y las convierte al formato deseado.
    
    Args:
        ruta_archivo (str): Ruta al archivo HTML de entrada
        etiqueta (str): Etiqueta HTML para dividir el contenido (ej: 'h2', 'h3')
        output_dir (str): Directorio de salida para los archivos
        formato (str): Formato de salida ('md' o 'html')
    """
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    secciones = []
    titulos = soup.find_all(etiqueta)

    for i, titulo in enumerate(titulos):
        contenido_actual = [str(titulo)]

        for elem in titulo.find_next_siblings():
            if elem.name == etiqueta:
                break
            contenido_actual.append(str(elem))

        secciones.append((titulo.get_text(strip=True), contenido_actual))

    os.makedirs(output_dir, exist_ok=True)

    for titulo, contenido in secciones:
        nombre_base = slugify(titulo)
        extension = ".md" if formato == "md" else ".html"
        nombre_archivo = f"{nombre_base}{extension}"
        ruta_salida = os.path.join(output_dir, nombre_archivo)

        contenido_completo = "\n".join(contenido)
        
        if formato == "md":
            contenido_completo = html_to_markdown(contenido_completo)

        with open(ruta_salida, "w", encoding="utf-8") as f:
            f.write(contenido_completo)

        print(f"✅ Archivo creado: {ruta_salida}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python split_html_to_md.py <archivo.html> [etiqueta] [formato]")
        print("  etiqueta: Etiqueta HTML para dividir (default: h2)")
        print("  formato: Formato de salida (md o html, default: md)")
        sys.exit(1)

    archivo = sys.argv[1]
    tag = sys.argv[2] if len(sys.argv) > 2 else "h2"
    formato = sys.argv[3].lower() if len(sys.argv) > 3 else "md"

    if formato not in ["md", "html"]:
        print("Error: El formato debe ser 'md' o 'html'")
        sys.exit(1)

    extraer_y_convertir(archivo, etiqueta=tag, formato=formato) 