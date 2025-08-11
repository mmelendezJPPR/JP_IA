"""
Utilidades para integración     # Construir mensajes en el formato de Anthropic
    claude_messages = []
    
    # Si hay un mensaje de sistema, agregarlo como el primer mensaje del usuario con formato especial
    if system_message:
        # El mensaje del sistema se convierte en una instrucción especial
        claude_messages.append({"role": "user", "content": f"{system_message}"})
        if len(human_messages) > 0:
            # Primer mensaje del usuario después de la instrucción
            claude_messages.append({"role": "assistant", "content": "Entendido, seguiré esas instrucciones."})
    
    # Añadir los mensajes de la conversación
    for i in range(max(len(human_messages), len(assistant_messages))):
        if i < len(human_messages):
            # Si es el primer mensaje y no hay sistema, o es cualquier otro mensaje
            if i > 0 or not system_message:
                claude_messages.append({"role": "user", "content": human_messages[i]})
        if i < len(assistant_messages):
            claude_messages.append({"role": "assistant", "content": assistant_messages[i]})
    
    # Último mensaje del usuario para solicitar respuesta (si no está ya incluido)
    if len(claude_messages) == 0 or claude_messages[-1]["role"] != "user":
        if len(human_messages) > 0:
            claude_messages.append({"role": "user", "content": human_messages[-1]})ude (Anthropic) en JP_IA
"""

import anthropic

def claude_chat_completion(client, messages, temperature=0.3, max_tokens=1000, model="claude-3-opus-20240229"):
    """
    Wrapper para la API de Claude que convierte el formato OpenAI al formato Claude
    
    Args:
        client: Cliente Anthropic inicializado
        messages: Lista de mensajes en formato OpenAI
        temperature: Temperatura para la generación (default: 0.3)
        max_tokens: Máximo de tokens para la respuesta (default: 1000)
        model: Modelo de Claude a usar (default: claude-3-opus-20240229)
        
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
    
    # Construir el prompt para Claude
    prompt = ""
    
    # Añadir mensaje del sistema al principio si existe
    if system_message:
        prompt += f"\n\nHuman: <system>{system_message}</system>\n\n"
    
    # Añadir los mensajes alternando entre Human y Assistant
    for i in range(max(len(human_messages), len(assistant_messages))):
        if i < len(human_messages):
            prompt += f"Human: {human_messages[i]}\n\n"
        if i < len(assistant_messages):
            prompt += f"Assistant: {assistant_messages[i]}\n\n"
    
    # Añadir "Assistant: " al final para que Claude continúe
    prompt += "Assistant: "
    
    try:
        # Llamar a la API de Claude con el formato correcto de mensajes
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=claude_messages
        )
        
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
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=claude_messages
            )
            
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
