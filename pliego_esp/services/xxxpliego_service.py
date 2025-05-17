from pathlib import Path
import os
from typing import Dict, List

pliego_generado_ejemplo = """## Pintado de Piso Industrial

### Descripción  

La actividad de **pintado de piso industrial** comprende una serie de trabajos destinados a renovar, proteger y mejorar la superficie de pavimentos. Incluye la preparación del 
soporte existente mediante procesos mecánicos, la corrección de imperfecciones y la aplicación de sistemas de pintura de alto desempeño. Su objetivo es obtener una superficie 
resistente, nivelada y adecuada para soportar condiciones exigentes como tránsito constante, maquinaria pesada o ambientes agresivos, garantizando durabilidad, seguridad y 
estética en el entorno de trabajo. Adicionalmente, se llevará a cabo el **retiro de recubrimientos existentes**, mediante la eliminación de capas anteriores utilizando métodos 
mecánicos.

### Materiales, herramientas y equipo  

- **Materiales**: Discos abrasivos de alta resistencia, pintura de acabado industrial (tipo uretano u otro según requerimiento), primer de adherencia, solventes para 
preparación y limpieza, productos para relleno y sellado de grietas.  
- **Equipo**: Amoladoras de piso, lijadoras industriales, equipos de aplicación de pintura (compresores, pistolas, rodillos, etc.).  
- **Herramientas**: Elementos manuales de corte, cepillado y preparación de superficies.  
- **EPP**: Casco, guantes de seguridad, gafas de protección, mascarilla con filtro, calzado de seguridad con punta reforzada, chaleco reflectante.

### Procedimiento  

Se deberá **delimitar y señalizar el área de intervención** para garantizar condiciones seguras de trabajo.  

El procedimiento comenzará con el **retiro de recubrimientos existentes**, mediante la eliminación de capas anteriores utilizando métodos mecánicos. Posteriormente, se 
procederá a la **preparación mecánica de la superficie** mediante lijado o amolado, con el fin de eliminar residuos, contaminantes o zonas deterioradas. Este trabajo debe 
asegurar una superficie nivelada y con textura adecuada para la adherencia del sistema de pintura.

Luego, se realizará la **reparación de fisuras y grietas**, utilizando productos compatibles con el sistema a aplicar. Una vez reparado y limpio, se procederá a la **aplicación
del primer** o capa base de adherencia, seleccionando un producto compatible con el acabado y las condiciones de uso.

El acabado superficial se logrará mediante la **aplicación de varias capas de pintura industrial** con un **acabado texturizado**, utilizando herramientas apropiadas como 
rodillos o pistolas, y respetando los tiempos de secado entre cada aplicación según especificaciones técnicas del fabricante.

Durante toda la ejecución se implementarán **controles de calidad visual y técnicos**, asegurando uniformidad, espesor adecuado y cobertura continua. El responsable de obra 
deberá velar por el cumplimiento de los estándares de seguridad y desempeño previstos.

### Medición y Forma de Pago  

La actividad será medida en **metros cuadrados (m²)**, considerando el área total intervenida, incluyendo preparación, reparación y aplicación del sistema completo de pintura.

La **verificación** de las superficies tratadas será realizada **por EMBOL S.A.**, tomando en cuenta la correcta ejecución del procedimiento, la calidad del acabado y el 
cumplimiento de los espesores requeridos.

El **pago** se efectuará en función del avance efectivamente medido y aprobado, conforme a los valores unitarios establecidos en el contrato y previa validación de calidad de 
los trabajos realizados.
"""


class PliegoService:
    PLIEGO_BASE_PATH = Path(__file__).resolve().parent.parent / "pliegos_base" / "pintado_de_piso_industrial[].md"
    
    @staticmethod
    def load_pliego_generado_ejemplo() -> str:
        return pliego_generado_ejemplo
    
    @staticmethod
    def load_pliego_base() -> str:
        """Carga el contenido del pliego base desde el archivo Markdown."""
        if os.path.exists(PliegoService.PLIEGO_BASE_PATH):
            with open(PliegoService.PLIEGO_BASE_PATH, 'r', encoding='utf-8') as file:
                return file.read()
        return "Pliego de especificaciones base."
    
    @staticmethod
    def create_especificacion(
        pliego_base: str,
        titulo: str,
        parametros_clave: List[str],
        adicionales: List[str]
    ) -> Dict:
        """Crea una especificación con los datos proporcionados."""
        return {
            "pliego_base": pliego_base,
            "titulo": titulo,
            "parametros_clave": parametros_clave,
            "adicionales": adicionales
        }
    
    @staticmethod
    def parse_form_data(form_data: Dict) -> Dict:
        """Procesa los datos del formulario y los convierte al formato requerido."""
        return {
            "pliego_base": form_data["pliego_base"],
            "titulo": form_data["titulo"],
            "parametros_clave": [param.strip() for param in form_data["parametros_clave"].split(",")],
            "adicionales": [adicional.strip() for adicional in form_data["adicionales"].split(",")]
        } 