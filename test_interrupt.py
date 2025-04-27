import asyncio
from pliego_esp.compile_graphs import get_workflow
from pliego_esp.graph.state import State
from langchain_core.runnables import RunnableConfig
from pliego_esp.graph.callbacks import shared_callback_handler

async def test_interrupt():
    # Obtener el workflow
    workflow = get_workflow()
    if workflow is None:
        print("Error: No se pudo obtener el workflow")
        return
        
    # Crear un estado de prueba
    state = State(
        pliego_base="Este es un pliego base de prueba",
        titulo="Título de prueba",
        parametros_clave=["param1", "param2"],
        adicionales=["adicional1", "adicional2"],
        token_cost=0.0,
        evaluaciones_otros_parametros=["Item 1 para revisar", "Item 2 para revisar"]
    )
    
    # Configuración de prueba con callbacks
    config = RunnableConfig(
        callbacks=[shared_callback_handler],
        configurable={
            "trust_remote_code": True,
            "use_cache": False
        }
    )
    
    print("\n=== PRIMERA EJECUCIÓN (DEBERÍA INTERRUMPIR) ===")
    try:
        result = await workflow.ainvoke(state, config)
        print("\nResultado de la primera ejecución:")
        print(f"Items: {result.get('items', [])}")
        
        if result.get('items'):
            print("\n=== SEGUNDA EJECUCIÓN (CON RESPUESTA) ===")
            # Simular respuesta del usuario
            result = await workflow.ainvoke(
                {"resume": "Acepto todos los items"},
                config=config
            )
            print("\nResultado de la segunda ejecución:")
            if "messages" in result:
                print(f"Mensajes: {[m.content for m in result['messages']]}")
            else:
                print(f"Resultado: {result}")
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_interrupt()) 