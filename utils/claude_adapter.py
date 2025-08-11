"""
Utilidades para integración de la API de Claude (Anthropic) en JP_IA
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
        # Llamar a la API de Claude
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
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
                messages=[
                    {"role": "user", "content": prompt}
                ]
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
