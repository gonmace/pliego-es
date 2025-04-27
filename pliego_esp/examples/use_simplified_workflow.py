"""
Ejemplo de uso del grafo simplificado para evaluar el nodo process_pliego
sin ejecutar los nodos anteriores.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

from pliego_esp.graph.state import State
from pliego_esp.services.graph_service import PliegoEspService
from pliego_esp.graph.configuration import Configuration

# Cargar variables de entorno
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path, override=True)

async def main():
    """
    Función principal que demuestra cómo usar el grafo simplificado.
    """
    # Crear un estado preprocesado con los datos necesarios para process_pliego
    # Estos datos normalmente serían el resultado de ejecutar los nodos anteriores
    preprocessed_state = State(
        pliego_base="""
# Especificación Técnica: Hormigonado de Estructuras

## Descripción
El hormigonado de estructuras consiste en la colocación y compactación del hormigón en elementos estructurales como columnas, vigas, losas y fundaciones. Este proceso es fundamental para garantizar la integridad estructural y durabilidad de la obra.

## Materiales, herramientas y equipo
- Hormigón estructural de resistencia especificada
- Encofrados de madera o metálicos
- Vibradores de hormigón
- Herramientas de acabado (llana, regla, etc.)
- Equipos de protección personal (EPP)

## Procedimiento
**Preparación**: Verificar que los encofrados estén correctamente instalados y fijados. **Limpieza** de la superficie donde se colocará el hormigón. **Hormigonado**: Colocar el hormigón en capas de espesor uniforme, realizando la compactación con vibradores para eliminar burbujas de aire. **Acabado**: Alisar la superficie según los requerimientos del proyecto.

## Medición y Forma de Pago
La medición se realizará en **metros cuadrados (m²)** de superficie hormigonada, calculada según las dimensiones especificadas en los planos.

La **verificación** será realizada por **EMBOL S.A.** mediante inspección visual y pruebas de resistencia según normativa vigente.

El pago se efectuará mensualmente, previa presentación de certificados de avance de obra y cumplimiento de especificaciones técnicas.
""",
        titulo="Hormigonado de Losa de Entrepiso",
        parametros_clave=["Resistencia del hormigón: 210 kg/cm²", "Espesor de la losa: 15 cm"],
        adicionales=["Inclusión de fibras de acero", "Tratamiento de superficie con endurecedor"],
        # Datos adicionales que normalmente serían generados por los nodos anteriores
        parametros_pliego="Resistencia del hormigón: 210 kg/cm²\nEspesor de la losa: 15 cm",
        parsed_parametros=[
            {"Parámetro": "Resistencia del hormigón", "Valor": "210 kg/cm²"},
            {"Parámetro": "Espesor de la losa", "Valor": "15 cm"}
        ],
        parametros_no_asignados=[],
        other_parametros=[],
        adicionales_pliego=["Inclusión de fibras de acero", "Tratamiento de superficie con endurecedor"],
        parsed_adicionales=[
            {"Adicional": "Inclusión de fibras de acero", "Descripción": "Adición de fibras de acero al hormigón para mejorar su resistencia a tracción"},
            {"Adicional": "Tratamiento de superficie con endurecedor", "Descripción": "Aplicación de endurecedor superficial para mejorar la resistencia al desgaste"}
        ],
        adicionales_finales=[
            {"Adicional": "Inclusión de fibras de acero", "Descripción": "Adición de fibras de acero al hormigón para mejorar su resistencia a tracción"},
            {"Adicional": "Tratamiento de superficie con endurecedor", "Descripción": "Aplicación de endurecedor superficial para mejorar la resistencia al desgaste"}
        ],
        other_adicionales=[],
        token_cost=0.0
    )
    
    # Crear la configuración para el workflow
    config = RunnableConfig(
        configurable={
            "chat_model": "gpt-4o",
            "temperature": 0.5
        }
    )
    
    # Procesar el mensaje utilizando el estado preprocesado
    result = await PliegoEspService.process_message_from_state(preprocessed_state, config)
    
    # Imprimir el resultado
    print("\n=== Resultado ===")
    print(result["response"])
    print(f"\nCosto de tokens: ${result['token_cost']:.6f}")

if __name__ == "__main__":
    asyncio.run(main()) 