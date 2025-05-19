from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from django.conf import settings
from langchain_core.output_parsers import StrOutputParser

from rich.console import Console
console = Console()

def mejorar_titulo_especificacion(titulo_especificacion: str) -> dict:
    """
    Mejora el titulo de una especificación técnica usando LangChain con OpenAI.
    
    Args:
        titulo_especificacion (str): El titulo de la especificación técnica a mejorar
        
    Returns:
        dict: Un diccionario con el resultado de la mejora
    """

    console.print(f"Titulo especificacion: {titulo_especificacion}")
    try:
        # Configurar el modelo de LangChain
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            "Eres un experto en redacción técnica para especificaciones de construcción. "
            "Debes mejorar títulos técnicos para que sean más claros, uniformes y adecuados para documentos de obra y búsqueda semántica. "
            "Sigue estas reglas estrictamente:\n"
            "- No agregues ni traduzcas información técnica que no esté explícita en el título original.\n"
            "- No transformes abreviaciones técnicas comunes como H30, B500, Ø110, HR, ni valores como f'c=25 MPa. Deben mantenerse exactamente como están.\n"
            "- Si hay abreviaciones informales (como H°A°), conviértelas a su forma completa (por ejemplo, 'Hormigón Armado').\n"
            "- Usa notación técnica compacta cuando sea posible: 'espesor' → 'e=', 'diámetro' → 'Ø=', etc., solo si ya están indicados.\n"
            "- Separa los conceptos con comas, conserva el orden lógico, y usa mayúsculas solo para términos clave.\n"
            "- No repitas ni reformules la información original.\n"
            "Tu salida debe ser solo el nuevo título corregido, sin explicaciones."),
            ("user", "Mejora el siguiente título para la especificación técnica: {titulo}")
        ])

        # Crear la cadena
        chain = prompt | llm | StrOutputParser()
        
        # Ejecutar la cadena
        response = chain.invoke({"titulo": titulo_especificacion})
        
        print(f"Response: {response}")
        
        return {
            'success': True,
            'titulo_especificacion_mejorado': response
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        } 