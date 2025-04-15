from django.apps import AppConfig
from rich.console import Console

console = Console()

class PliegoEspConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pliego_esp'
    
    def ready(self):
        """
        Este método se ejecuta cuando Django inicia la aplicación.
        Aquí cargamos los grafos una sola vez.
        """
        try:
            # Importamos aquí para evitar importaciones circulares
            from pliego_esp.compile_graphs import initialize_graphs
            
            # Inicializar los grafos
            if initialize_graphs():
                console.print("[PliegoEspConfig] Grafos inicializados correctamente", style="bold green")
            else:
                console.print("[PliegoEspConfig] Error al inicializar los grafos", style="bold red")
                
        except Exception as e:
            console.print(f"[PliegoEspConfig] Error en la inicialización: {str(e)}", style="bold red")
