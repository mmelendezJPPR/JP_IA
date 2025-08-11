"""
Utilidades para integración de la API de Claude (Anthropic) en JP_IA
"""

import anthropic

def claude_chat_completion(client, messages, temperature=0.3, max_tokens=1000, model="claude-3-sonnet-20240229"):
    """
    Wrapper para la API de Claude que convierte el formato OpenAI al formato Claude
    
    Args:
        client: Cliente Anthropic inicializado
        messages: Lista de mensajes en formato OpenAI
        temperature: Temperatura para la generación (default: 0.3)
        max_tokens: Máximo de tokens para la respuesta (default: 1000)
        model: Modelo de Claude a usar (default: claude-3-sonnet-20240229)
        
    Returns:
        Un objeto de respuesta compatible con el formato OpenAI
    """
    # Convertir mensajes de formato OpenAI a Claude
    system_message = ""
    human_messages = []
    assistant_messages = []
    
    for msg in messages:
        if msg["role"] == "system":
            system_message = msg["content"]
        elif msg["role"] == "user":
            human_messages.append(msg["content"])
        elif msg["role"] == "assistant":
            assistant_messages.append(msg["content"])
    
    # Construir mensajes en el formato de Anthropic
    anthropic_messages = []
    
    # Si hay un mensaje de sistema, usarlo como system prompt
    system_prompt = system_message if system_message else None
    
    # Añadir los mensajes alternando entre usuario y asistente
    for i in range(max(len(human_messages), len(assistant_messages))):
        if i < len(human_messages):
            anthropic_messages.append({"role": "user", "content": human_messages[i]})
        if i < len(assistant_messages):
            anthropic_messages.append({"role": "assistant", "content": assistant_messages[i]})
    
    # Si no hay mensajes o el último no es del usuario, añadir el último mensaje del usuario
    if not anthropic_messages or (anthropic_messages and anthropic_messages[-1]["role"] != "user"):
        if human_messages:
            anthropic_messages.append({"role": "user", "content": human_messages[-1]})
    
    try:
        # Preparar los parámetros para la llamada a la API
        params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anthropic_messages
        }
        
        # Añadir system si está definido
        if system_prompt:
            params["system"] = system_prompt
            
        # Llamar a la API de Claude
        response = client.messages.create(**params)
        
        # Convertir la respuesta de Claude al formato similar a OpenAI
        mock_openai_response = type('MockResponse', (), {})()
        mock_openai_response.choices = [
            type('MockChoice', (), {})()
        ]
        mock_openai_response.choices[0].message = type('MockMessage', (), {})()
        mock_openai_response.choices[0].message.content = response.content[0].text
        
        return mock_openai_response
        
    except Exception as e:
        # Registrar el error y reintentarlo con Claude Haiku (modelo más pequeño y económico)
        print(f"Error al llamar a Claude: {e}. Reintentando con Claude Haiku...")
        try:
            # Cambiar al modelo más económico y mantener los mismos parámetros
            params["model"] = "claude-3-haiku-20240307"
            response = client.messages.create(**params)
            
            # Convertir la respuesta de Claude al formato similar a OpenAI
            mock_openai_response = type('MockResponse', (), {})()
            mock_openai_response.choices = [
                type('MockChoice', (), {})()
            ]
            mock_openai_response.choices[0].message = type('MockMessage', (), {})()
            mock_openai_response.choices[0].message.content = response.content[0].text
            
            return mock_openai_response
            
        except Exception as e2:
            print(f"Error con Claude Haiku: {e2}")
            # Crear una respuesta mock para evitar errores críticos
            mock_openai_response = type('MockResponse', (), {})()
            mock_openai_response.choices = [
                type('MockChoice', (), {})()
            ]
            mock_openai_response.choices[0].message = type('MockMessage', (), {})()
            mock_openai_response.choices[0].message.content = "Lo siento, no puedo generar una respuesta en este momento."
            
            return mock_openai_response
