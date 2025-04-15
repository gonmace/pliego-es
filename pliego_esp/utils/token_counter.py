import logging
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)

class TokenCounterCallback(BaseCallbackHandler):
    def __init__(self, model_name="gpt-4o-mini"):
        self.model_name = model_name
        self.reset_stats()
        logger.info(f"TokenCounter inicializado para modelo: {model_name}")
    
    def reset_stats(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_cost = 0.0
        logger.info("Estadísticas de tokens reiniciadas")
    
    def calculate_cost(self):
        # Tarifas por modelo (actualizar según precios actuales)
        PRICING = {
            "gpt-4o-mini": {
                "input": 0.15 / 1000000,     # $0.0015 por 1K tokens
                "output": 0.6 / 1000000     # $0.006 por 1K tokens
            }
        }
        
        pricing = PRICING.get(self.model_name, PRICING["gpt-4o-mini"])
        
        return (
            self.input_tokens * pricing["input"] + 
            self.output_tokens * pricing["output"]
        )
    
    def on_llm_end(self, response, **kwargs):
        """Se ejecuta cuando el modelo LLM finaliza y devuelve una respuesta."""
        if hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('token_usage', {})
            
            # Actualizamos la suma de tokens (acumulado)
            self.input_tokens = usage.get('prompt_tokens', 0)
            self.output_tokens = usage.get('completion_tokens', 0)
            self.total_tokens = self.input_tokens + self.output_tokens
            
            # Calculamos el costo total
            self.total_cost = self.calculate_cost()
    
    def get_token_summary(self) -> dict[str, float]:
        """Devuelve un resumen del uso de tokens."""
        return {
            "prompt_tokens": self.input_tokens or 0,
            "completion_tokens": self.output_tokens or 0,
            "total_tokens": self.input_tokens + self.output_tokens or 0,
            "cost": self.total_cost or 0
        }
