from langchain_community.callbacks.openai_info import OpenAICallbackHandler

# Crear un único callback_handler compartido para toda la aplicación
shared_callback_handler = OpenAICallbackHandler() 