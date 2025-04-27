from langgraph.graph import StateGraph, START, END

from pliego_esp.graph.nodes.review_unassigned_parameters import review_unassigned_parameters
from pliego_esp.graph.nodes.add_unassigned_parameters import add_unassigned_parameters

from pliego_esp.graph.state import State

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
import uuid
from rich.console import Console
from langgraph.types import Command  # Importar Command para reanudar la interrupción

console = Console()

esp_generada = """
## Pintado de Piso Industrial

### Descripción

La actividad de **pintado de piso industrial** comprende una serie de trabajos destinados a renovar, proteger y mejorar la superficie de pavimentos. Incluye la preparación del soporte existente mediante
procesos mecánicos, la corrección de imperfecciones y la aplicación de sistemas de pintura de alto desempeño. Su objetivo es obtener una superficie resistente, nivelada y adecuada para soportar condiciones
exigentes como tránsito constante, maquinaria pesada o ambientes agresivos, garantizando durabilidad, seguridad y estética en el entorno de trabajo. Además, se incorpora un **acabado texturizado** que
proporciona características antideslizantes, mejorando la seguridad en el área de trabajo.

### Materiales, herramientas y equipo

- **Materiales**: Discos abrasivos de alta resistencia, pintura de acabado industrial (tipo uretano u otro según requerimiento), primer de adherencia, solventes para preparación y limpieza, productos para
relleno y sellado de grietas.
- **Equipo**: Amoladoras de piso, lijadoras industriales, compresores, equipos de aplicación de pintura (pistolas, rodillos, etc.).
- **Herramientas**: Elementos manuales de corte, cepillado y preparación de superficies.
- **EPP**: Casco, guantes de seguridad, gafas de protección, mascarilla con filtro, calzado de seguridad con punta reforzada, chaleco reflectante.

### Procedimiento

Se deberá **delimitar y señalizar el área de intervención** para garantizar condiciones seguras de trabajo.

El procedimiento comenzará con el **retiro de recubrimientos existentes**, mediante la eliminación de capas anteriores utilizando métodos mecánicos o químicos, asegurando que la superficie base esté limpia y
libre de contaminantes. Posteriormente, se realizará la **preparación mecánica de la superficie** mediante lijado o amolado, con el fin de eliminar residuos y zonas deterioradas, garantizando una superficie
nivelada y con textura adecuada para la adherencia del sistema de pintura.

Luego, se procederá a la **reparación de fisuras y grietas**, utilizando productos compatibles con el sistema a aplicar. Una vez reparado y limpio, se procederá a la **aplicación del primer** o capa base de
adherencia, seleccionando un producto compatible con el acabado y las condiciones de uso.

El acabado superficial se logrará mediante la **aplicación de varias capas de pintura industrial** con un **acabado texturizado**, utilizando herramientas apropiadas como rodillos o pistolas, y respetando los
tiempos de secado entre cada aplicación según especificaciones técnicas del fabricante.

Durante toda la ejecución se implementarán **controles de calidad visual y técnicos**, asegurando uniformidad, espesor adecuado y cobertura continua. El responsable de obra deberá velar por el cumplimiento de
los estándares de seguridad y desempeño previstos.

### Medición y Forma de Pago

La actividad será medida en **metros cuadrados (m²)**, considerando el área total intervenida, incluyendo preparación, reparación y aplicación del sistema completo de pintura.

La **verificación** de las superficies tratadas será realizada **por EMBOL S.A.**, tomando en cuenta la correcta ejecución del procedimiento, la calidad del acabado y el cumplimiento de los espesores
requeridos.

El **pago** se efectuará en función del avance efectivamente medido y aprobado, conforme a los valores unitarios establecidos en el contrato y previa validación de calidad de los trabajos realizados.
"""
memory_saver = MemorySaver()
async def run_node_only():
    # Estado inicial para node_b (por ejemplo, resultado esperado de node_a)
    initial_state = State(
        especificacion_generada=esp_generada,
        other_parametros=[
            {'Parámetro Técnico': 'Color', 'Opciones válidas': '-', 'Valor por defecto': '-', 'Valor Asignado': 'Pintura de 3 colores'},
            {'Parámetro Técnico': 'Revoque', 'Opciones válidas': '-', 'Valor por defecto': '-', 'Valor Asignado': 'Realizar revoque'}
        ]
    )
    conversation_id = str(uuid.uuid4())
    
    # Configurar el RunnableConfig
    config = RunnableConfig(
        recursion_limit=10,
        configurable={
            "thread_id": conversation_id
        }
    )

    try:
        # Crear un workflow simplificado solo con el nodo que queremos probar
        workflow = StateGraph(State)
        workflow.add_node("review_unassigned_parameters", review_unassigned_parameters)
        workflow.add_node("add_unassigned_parameters", add_unassigned_parameters)
        
        workflow.set_entry_point("review_unassigned_parameters")
        workflow.add_edge("review_unassigned_parameters", "add_unassigned_parameters")
        workflow.add_edge("add_unassigned_parameters", END)
        
        # Compilar el workflow
        app = workflow.compile(checkpointer=memory_saver)
        
        # Primera ejecución - esto debería interrumpirse
        console.print("\n=== PRIMERA EJECUCIÓN (DEBERÍA INTERRUMPIR) ===", style="bold yellow")
        async for event in app.astream(initial_state, config):
            if "__interrupt__" in event:
                interrupt_data = event["__interrupt__"][0]
                mensaje = interrupt_data.value["mensaje"]
                items = interrupt_data.value["items"]
                console.print("Esta interrumpido", style="bold red")
                resumed = await app.ainvoke(Command(resume="respuesta"), config=config)
            # if hasattr(event, "__interrupt__"):
            #     console.print(event, style="bold blue")
                
            # if "__interrupt__" in event:
            #     interrupt_data = result["__interrupt__"].value
            #     console.print(event["__interrupt__"][0].value["items"], style="bold red")
                
            # if event.event == "complete":
            #     console.print(event.result, style="bold blue")
            # elif event.event == "interrupt":
            #     console.print(event.result, style="bold red")
        # Verificar si hay interrupción (ítems para revisar)
        # items = result.get("items", [])
        # if items:
        #     console.print("\n=== INTERRUPCIÓN DETECTADA ===", style="bold red")
        #     for item in items:
        #         console.print(f"- {item}", style="yellow")
            
        #     # Simular respuesta del usuario (en un entorno real, esto vendría de la interfaz)
        #     respuesta_usuario = "Acepto todos los items"  # Esto es solo para prueba
            
        #     console.print("\n=== SEGUNDA EJECUCIÓN (CON RESPUESTA) ===", style="bold green")
        #     # Reanudar el workflow con la respuesta del usuario
        #     resumed_result = await app.ainvoke(
        #         Command(resume=respuesta_usuario),
        #         config=config
        #     )
            
        #     console.print("\nResultado final:", style="bold blue")
        #     console.print(resumed_result, style="bold blue")
        # else:
        #     console.print("\nNo se detectó interrupción", style="bold yellow")
        #     console.print(result, style="bold red")
        return {
            "response": resumed,
            "token_cost": 0
            }
    except Exception as e:
        print(f"Error al ejecutar el nodo: {str(e)}")


# Para correr la función async en un entorno normal:
import asyncio
asyncio.run(run_node_only())