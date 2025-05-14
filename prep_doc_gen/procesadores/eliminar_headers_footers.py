#eliminar_headers_footers.py
import sys
from docx import Document
import os

def delete_headers_footers(doc_path, base_dir):
    # Load the document
    doc = Document(doc_path)

    # Eliminar encabezados y pies de página de todas las secciones
    for section in doc.sections:
        headers = [section.header, section.first_page_header, section.even_page_header]
        footers = [section.footer, section.first_page_footer, section.even_page_footer]

        for header in headers:
            for element in header._element:
                header._element.remove(element)

        for footer in footers:
            for element in footer._element:
                footer._element.remove(element)

    # Obtener el directorio base y el nombre del archivo
    base_dir = os.path.dirname(doc_path)
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Crear el nombre del archivo de salida
    filename = os.path.basename(doc_path)
    output_filename = '10_' + filename
    output_path = os.path.join(output_dir, output_filename)
    
    # Guardar el documento
    doc.save(output_path)
    print(f"Documento guardado como: {output_path}")
    return output_filename
# Uso
# Ejecutar desde terminal
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python eliminar_encabezados.py archivo.docx")
    else:
        delete_headers_footers(sys.argv[1])
