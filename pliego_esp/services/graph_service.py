# graph_service.py

from typing import Optional
from langchain_core.runnables import RunnableConfig

from pliego_esp.graph.state import State
from pliego_esp.models import TokenCost
from pliego_esp.compile_graphs import get_workflow, get_memory_saver
from pliego_esp.graph.callbacks import shared_callback_handler

from rich.console import Console
from asgiref.sync import sync_to_async
from langgraph.types import Command
from langgraph.graph import StateGraph

console = Console()

esp_generada = """
## Pintado de Piso Industrial

### Descripción

La actividad de **pintado de piso industrial** comprende una serie de trabajos destinados a renovar, proteger y mejorar la superficie de pavimentos. Incluye la preparación del soporte existente mediante procesos mecánicos, la corrección de imperfecciones y la aplicación de sistemas de pintura de alto desempeño. 

Su objetivo es obtener una superficie resistente, nivelada y adecuada para soportar condiciones exigentes como tránsito constante, maquinaria pesada o ambientes agresivos, garantizando durabilidad, seguridad y estética en el entorno de trabajo. Además, se incorpora un **acabado texturizado** que proporciona características antideslizantes, mejorando la seguridad en el área de trabajo.

### Materiales, herramientas y equipo

- **Materiales**: Discos abrasivos de alta resistencia, pintura de acabado industrial (tipo uretano u otro según requerimiento), primer de adherencia, solventes para preparación y limpieza, productos para relleno y sellado de grietas.
- **Equipo**: Amoladoras de piso, lijadoras industriales, compresores, equipos de aplicación de pintura (pistolas, rodillos, etc.).
- **Herramientas**: Elementos manuales de corte, cepillado y preparación de superficies.
- **EPP**: Casco, guantes de seguridad, gafas de protección, mascarilla con filtro, calzado de seguridad con punta reforzada, chaleco reflectante.

### Procedimiento

Se deberá **delimitar y señalizar el área de intervención** para garantizar condiciones seguras de trabajo.

El procedimiento comenzará con el **retiro de recubrimientos existentes**, mediante la eliminación de capas anteriores utilizando métodos mecánicos o químicos, asegurando que la superficie base esté limpia y libre de contaminantes. Posteriormente, se realizará la **preparación mecánica de la superficie** mediante lijado o amolado, con el fin de eliminar residuos y zonas deterioradas, garantizando una superficie nivelada y con textura adecuada para la adherencia del sistema de pintura.

Luego, se procederá a la **reparación de fisuras y grietas**, utilizando productos compatibles con el sistema a aplicar. Una vez reparado y limpio, se procederá a la **aplicación del primer** o capa base de adherencia, seleccionando un producto compatible con el acabado y las condiciones de uso.

El acabado superficial se logrará mediante la **aplicación de varias capas de pintura industrial** con un **acabado texturizado**, utilizando herramientas apropiadas como rodillos o pistolas, y respetando los tiempos de secado entre cada aplicación según especificaciones técnicas del fabricante.

Durante toda la ejecución se implementarán **controles de calidad visual y técnicos**, asegurando uniformidad, espesor adecuado y cobertura continua. El responsable de obra deberá velar por el cumplimiento de los estándares de seguridad y desempeño previstos.

### Medición y Forma de Pago

La actividad será medida en **metros cuadrados (m²)**, considerando el área total intervenida, incluyendo preparación, reparación y aplicación del sistema completo de pintura.

La **verificación** de las superficies tratadas será realizada **por EMBOL S.A.**, tomando en cuenta la correcta ejecución del procedimiento, la calidad del acabado y el cumplimiento de los espesores requeridos.

El **pago** se efectuará en función del avance efectivamente medido y aprobado, conforme a los valores unitarios establecidos en el contrato y previa validación de calidad de los trabajos realizados.
"""


class PliegoEspService:
        # Variables de clase para guardar temporalmente
    saved_config: Optional[RunnableConfig] = None
    workflow = get_workflow()
    
    
    @staticmethod
    async def process_pliego(input: dict, config: RunnableConfig, user=None, resume_data=False ) -> dict:

        workflow = PliegoEspService.workflow
        
        if workflow is None:
            return {
                "response": "Error: El sistema no está inicializado correctamente. Por favor, contacte al administrador.",
                "token_cost": 0
            }
        
        # Solo intentar obtener TokenCost si el usuario está autenticado
        if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
            try:
                # Usar sync_to_async para manejar correctamente las operaciones de base de datos
                token_cost = await sync_to_async(TokenCost.objects.get)(user=user)
                credits = token_cost.credits
                total_cost = token_cost.total_cost
                ratio = total_cost/credits*100
                if ratio > 100:
                    return {
                        "response": "No tienes suficientes créditos para continuar. Por favor, actualiza tu plan.",
                        "token_cost": 0
                    }
            except TokenCost.DoesNotExist:
                # Si no existe un registro para este usuario, usamos los valores por defecto
                pass
        
        if resume_data is False:
            # Inicializar el estado con el mensaje del usuario
            initial_state = State(
                pliego_base=input["pliego_base"],
                titulo=input["titulo"],
                parametros_clave=input["parametros_clave"],
                adicionales=input["adicionales"],
                token_cost=0.0,
                
                
                # TODO: Solo es para el grafo resumido, se debe eliminar
                especificacion_generada=esp_generada,
                other_parametros=[
                {'Parámetro Técnico': 'Color', 'Opciones válidas': '-', 'Valor por defecto': '-', 'Valor Asignado': 'Pintura de 3 colores'},
                {'Parámetro Técnico': 'Revoque', 'Opciones válidas': '-', 'Valor por defecto': '-', 'Valor Asignado': 'Realizar revoque'}
                    ],
                other_adicionales=[
                    {'actividad': 'Otros', 'descripcion': 'colocación de barreras de protección para evitar choque de los montacargas'}
                    ]
                )

            PliegoEspService.saved_config = config
            run_input = initial_state
        else:
            run_input = Command(resume=input)
            
        final_response = None
                
        # Primera invocación del workflow
        async for event in workflow.astream(run_input, config):
            clave = next(iter(event))
            console.print(clave, style="bold red")
            
            if "__interrupt__" in event:
                console.print("INTERRUPCION", style="bold red")
                interrupt_obj = event["__interrupt__"][0]
                
                return {
                    "type": clave,
                    "action": interrupt_obj.value["action"],
                    "items": interrupt_obj.value["items"],
                    "config": config
                }
            final_response = event[clave]

        # Obtener el costo total acumulado del callback_handler compartido
        token_cost = shared_callback_handler.total_cost
        
        return {
            "type": "final",
            "content": final_response["especificacion_generada"],
            "token_cost": token_cost,
            "conversation_id": config["configurable"]["thread_id"]
        }
