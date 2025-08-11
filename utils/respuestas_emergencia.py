"""
Módulo para respuestas de emergencia cuando la API de OpenAI no está disponible
"""

import re

def generar_respuesta_emergencia(pregunta, tomos_mejorados):
    """
    Genera una respuesta de emergencia basada en búsqueda de texto simple
    cuando la API de OpenAI no está disponible
    
    Args:
        pregunta (str): La pregunta del usuario
        tomos_mejorados (dict): Diccionario con el contenido de los tomos
        
    Returns:
        str: Respuesta generada
    """
    pregunta = pregunta.lower()
    
    # Definir palabras clave comunes para búsquedas
    keywords = {
        'permiso': ['permiso', 'permisos', 'autorización', 'licencia'],
        'construcción': ['construcción', 'edificación', 'obra', 'construir'],
        'uso': ['uso', 'ocupación', 'utilización'],
        'urbanización': ['urbanización', 'urbanizar', 'lotificación'],
        'calificación': ['calificación', 'zonificación', 'distrito', 'zona'],
        'histórico': ['histórico', 'histórica', 'patrimonio', 'conservación'],
        'ambiente': ['ambiente', 'ambiental', 'ecológico', 'natural'],
        'querella': ['querella', 'queja', 'reclamación', 'denuncia']
    }
    
    # Identificar palabras clave en la pregunta
    temas_relevantes = []
    for tema, palabras in keywords.items():
        if any(palabra in pregunta for palabra in palabras):
            temas_relevantes.append(tema)
    
    # Si no se identificaron temas, dar respuesta genérica
    if not temas_relevantes:
        return """
Lo siento, no puedo generar una respuesta específica en este momento debido a limitaciones técnicas.

Para obtener una respuesta más precisa, podrías:
- Reformular la pregunta con términos más específicos
- Contactar directamente con la Junta de Planificación de Puerto Rico
- Especificar el tomo o área de regulación que te interesa

Contacto oficial:
- Junta de Planificación de Puerto Rico
- Oficina de Gerencia de Permisos (OGPe)
        """
    
    # Determinar qué tomos consultar según los temas
    tomos_a_consultar = []
    
    if 'permiso' in temas_relevantes and 'construcción' in temas_relevantes:
        tomos_a_consultar.extend([3, 4, 8])
    elif 'permiso' in temas_relevantes:
        tomos_a_consultar.extend([1, 3])
    elif 'uso' in temas_relevantes:
        tomos_a_consultar.extend([3, 6])
    elif 'calificación' in temas_relevantes:
        tomos_a_consultar.extend([6])
    elif 'urbanización' in temas_relevantes:
        tomos_a_consultar.extend([5])
    elif 'histórico' in temas_relevantes:
        tomos_a_consultar.extend([10])
    elif 'ambiente' in temas_relevantes:
        tomos_a_consultar.extend([9])
    elif 'querella' in temas_relevantes:
        tomos_a_consultar.extend([11])
    else:
        tomos_a_consultar = [2, 3, 6]  # Tomos con información general
    
    # Siempre consultar el glosario
    tomos_a_consultar.append(12)
    
    # Eliminar duplicados y ordenar
    tomos_a_consultar = sorted(list(set(tomos_a_consultar)))
    
    # Buscar información relevante en los tomos seleccionados
    resultados = []
    
    # Construir expresión regular con los términos principales de la pregunta
    # Eliminar palabras comunes
    palabras_comunes = ['que', 'el', 'la', 'los', 'las', 'un', 'una', 'es', 'son', 'para', 'por', 'como', 'cómo']
    palabras_pregunta = [p for p in pregunta.split() if p not in palabras_comunes and len(p) > 2]
    
    # Construir patrón de búsqueda
    patron = '|'.join(palabras_pregunta)
    
    # Buscar en cada tomo
    for num_tomo in tomos_a_consultar:
        if num_tomo not in tomos_mejorados:
            continue
            
        contenido = tomos_mejorados[num_tomo]
        
        # Dividir en párrafos
        parrafos = contenido.split('\n\n')
        
        # Buscar párrafos relevantes
        for parrafo in parrafos:
            if all(palabra in parrafo.lower() for palabra in palabras_pregunta):
                # Párrafo contiene todas las palabras clave
                resultados.append((5, num_tomo, parrafo))
            elif re.search(patron, parrafo.lower()):
                # Párrafo contiene algunas palabras clave
                relevancia = sum(1 for palabra in palabras_pregunta if palabra in parrafo.lower())
                resultados.append((relevancia, num_tomo, parrafo))
    
    # Ordenar resultados por relevancia (mayor a menor)
    resultados.sort(reverse=True)
    
    # Limitar a los 3 resultados más relevantes
    mejores_resultados = resultados[:3]
    
    # Si no hay resultados, dar respuesta genérica
    if not mejores_resultados:
        return f"""
Actualmente estoy en modo de emergencia debido a limitaciones técnicas con la API de OpenAI.

No he podido encontrar información específica sobre tu consulta relacionada con: {', '.join(temas_relevantes)}.

He buscado en los tomos: {', '.join(str(t) for t in tomos_a_consultar)} sin éxito.

Por favor:
1. Reformula tu pregunta con términos más específicos
2. Consulta directamente con la Junta de Planificación
3. Especifica el tomo exacto donde crees que está la información
        """
    
    # Construir respuesta
    respuesta = f"""
⚠️ **MODO DE EMERGENCIA ACTIVADO** - Respuesta generada sin acceso a la API de OpenAI

He encontrado información relacionada con tu consulta sobre: {', '.join(temas_relevantes)}
Información extraída de los tomos: {', '.join(str(resultado[1]) for resultado in mejores_resultados)}

"""
    
    # Añadir fragmentos relevantes
    for i, (relevancia, num_tomo, parrafo) in enumerate(mejores_resultados):
        # Limpiar el párrafo (eliminar saltos de línea excesivos, etc)
        parrafo_limpio = re.sub(r'\s+', ' ', parrafo).strip()
        
        # Añadir a la respuesta
        respuesta += f"""
📌 **Fragmento {i+1}** (Tomo {num_tomo}):
{parrafo_limpio}

"""
    
    respuesta += """
---
⚠️ Nota: Esta respuesta fue generada en modo de emergencia debido a problemas con la API de OpenAI.
La precisión podría ser menor que en funcionamiento normal.

Para obtener información más precisa, por favor contacta directamente con la Junta de Planificación de Puerto Rico.
"""
    
    return respuesta
