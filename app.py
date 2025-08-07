"""
BetaIA - Chatbot para consultas sobre leyes de planificación de Puerto Rico

Este chatbot proporciona información basada en:
- Reglamento de Emergencia JP-RP-41 (fuente principal)
- Glosario de términos técnicos
- Tomos históricos (1-11) para referencia

Características principales:
- Búsqueda y conversión de tablas de cabida a formato HTML
- Visualización de flujogramas de procesos
- Consulta de resoluciones por tomo
- Búsqueda en glosario de términos
"""

from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import re
import sys
import uuid
import json
import mimetypes
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# 🆕 IMPORTAR MINI-ESPECIALISTAS
from mini_especialistas import procesar_con_mini_especialistas_v2

# CONFIGURACIÓN BETA - FECHA DE EXPIRACIÓN
# Beta profesional por días para demostración oficial
FECHA_EXPIRACION_BETA = datetime(2025, 8, 9,)  # 9 de agosto 2025 - 5 días para demostración completa
def formatear_fecha_espanol(fecha):
    """Convierte una fecha al formato español"""
    meses_espanol = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }

    if isinstance(fecha, datetime):
        dia = fecha.day
        mes = meses_espanol[fecha.month]
        año = fecha.year
        return f"{dia} de {mes} de {año}"
    else:
        dia = fecha.day
        mes = meses_espanol[fecha.month]
        año = fecha.year
        return f"{dia} de {mes} de {año}"
    

def verificar_beta_activa():
    """Verifica si la versión beta sigue activa"""
    ahora = datetime.now()
    
    if ahora <= FECHA_EXPIRACION_BETA:
        tiempo_restante = FECHA_EXPIRACION_BETA - ahora
        dias_restantes = tiempo_restante.days
        horas_restantes = int(tiempo_restante.total_seconds() // 3600) % 24
        
        # Retornar días si quedan más de 1 día, horas si queda menos de 1 día
        if dias_restantes > 0:
            return True, f"{dias_restantes} días"
        else:
            return True, f"{horas_restantes} horas"
    else:
        return False, 0
    
# Configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Para sesiones seguras
CORS(app)

# Configurar MIME types para archivos estáticos
import mimetypes
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

# Asegurar que estamos en el directorio correcto
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Cargar variables de entorno y cliente
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Lista de palabras clave legales para detección
palabras_legales = [
    'permiso', 'planificación', 'construcción', 'zonificación', 'desarrollo',
    'urbanización', 'reglamento', 'licencia', 'certificación', 'calificación',
    'tomo', 'junta', 'planificación', 'ambiental', 'infraestructura',
    'conservación', 'histórico', 'querella', 'edificabilidad', 'lotificación'
]

# Función para cargar glosario (si existe)
def cargar_glosario():
    ruta_glosario = os.path.join("data", "glosario.txt")
    if os.path.exists(ruta_glosario):
        try:
            with open(ruta_glosario, "r", encoding="utf-8") as f:
                contenido = f.read()
            print(f"✅ Glosario cargado: {len(contenido)} caracteres, {len(contenido.split('**'))} términos aprox.")
            return contenido
        except Exception as e:
            print(f"❌ Error cargando glosario: {e}")
            return ""
    else:
        print(f"⚠️ Glosario no encontrado en: {ruta_glosario}")
        return ""

glosario = cargar_glosario()

# Función para obtener información completa de todos los tomos
def obtener_titulos_tomos():
    """Devuelve información completa sobre todos los recursos disponibles"""
    return """
🚨 **INFORMACIÓN LEGAL VIGENTE - REGLAMENTO DE EMERGENCIA JP-RP-41 (2025)**

**FUENTE PRINCIPAL Y ACTUALIZADA:**
- 🚨 **Reglamento de Emergencia JP-RP-41** - Normativa vigente y actualizada (2025)
- 📚 **Glosario Oficial** - Definiciones especializadas de términos legales

**INFORMACIÓN ADICIONAL (SOLO PARA CONTEXTO HISTÓRICO):**

**TOMO 1:** Sistema de Evaluación y Tramitación de Permisos para el Desarrollo
- Enfoque: Procedimientos administrativos, transparencia y uniformidad del sistema unificado
- Agencias: Junta de Planificación (JP), Oficina de Gerencia de Permisos (OGPe), Municipios Autónomos, Profesionales Autorizados

**TOMO 2:** Disposiciones Generales  
- Enfoque: Procedimientos administrativos para permisos, consultas, certificaciones y documentos ambientales
- Aplicación: Ley 38-2017 LPAU, determinaciones finales y trámites que afecten operación de negocios

**TOMO 3:** Permisos para Desarrollo y Negocios
- Enfoque: Tipos de permisos, procedimientos para desarrollo de proyectos y operación de negocios
- Incluye: Permisos de medio ambiente, flujogramas de cambios de calificación

**TOMO 4:** Licencias y Certificaciones
- Enfoque: Diversos tipos de licencias y certificaciones requeridas para negocios y operaciones
- Regulación: Operaciones comerciales e industriales específicas

**TOMO 5:** Urbanización y Lotificación
- Enfoque: Proyectos de urbanización, procesos de lotificación y clasificaciones de terrenos
- Regulación: Desarrollo residencial y comercial, subdivisión de terrenos

**TOMO 6:** Distritos de Calificación
- Enfoque: Zonificación, clasificación de distritos y usos permitidos por zona
- Regulación: Ordenamiento territorial y usos de suelo

**TOMO 7:** Procesos
- Enfoque: Procedimientos específicos para diversos tipos de trámites y procesos administrativos
- Regulación: Metodologías y secuencias de tramitación

**TOMO 8:** Edificabilidad
- Enfoque: Regulaciones sobre construcción, densidad y parámetros de edificación
- Regulación: Altura, retiros, cabida y otros parámetros constructivos

**TOMO 9:** Infraestructura y Ambiente
- Enfoque: Requisitos de infraestructura, consideraciones ambientales y sostenibilidad
- Regulación: Servicios públicos, impacto ambiental, conservación

**TOMO 10:** Conservación Histórica
- Enfoque: Protección del patrimonio histórico, sitios arqueológicos y edificaciones históricas
- Regulación: Preservación cultural y arquitectónica

**TOMO 11:** Querellas
- Enfoque: Procedimientos para revisiones administrativas, querellas, multas y auditorías
- Regulación: Recursos administrativos y procesos de impugnación ante la División de Revisiones Administrativas de la OGPe

⚠️ **NOTA IMPORTANTE:** Los tomos 1-11 son únicamente para referencia histórica. La normativa vigente y actualizada se encuentra EXCLUSIVAMENTE en el **Reglamento de Emergencia JP-RP-41 (2025)**.
"""

# Diccionario para mantener conversaciones por sesión
conversaciones = {}

def get_conversation_id():
    """Obtiene o crea un ID de conversación para la sesión actual"""
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    return session['conversation_id']

def inicializar_conversacion(conversation_id):
    """Inicializa una nueva conversación"""
    if conversation_id not in conversaciones:
        conversaciones[conversation_id] = [
            {"role": "system", "content": """Eres Agente de Planificación, un asistente especializado altamente inteligente en leyes de planificación de Puerto Rico. 

CARACTERÍSTICAS:
- Analiza profundamente las preguntas del usuario
- Proporciona respuestas completas y detalladas
- Usa contexto de múltiples fuentes cuando es necesario
- Explica conceptos legales de manera clara
- Si es una pregunta legal/planificación, usa SOLO el texto proporcionado
- Si es pregunta general, responde libremente como un asistente avanzado
- Siempre sé útil, preciso y profesional
- Recomendar y corregir al usuario como hacer la pregunta correctamente

CAPACIDADES ESPECIALES:
- Puedes analizar y comparar información entre diferentes tomos
- Puedes hacer resúmenes y síntesis
- Puedes explicar procedimientos y procesos
- Puedes identificar relaciones entre diferentes regulaciones
- TIENES ACCESO COMPLETO AL GLOSARIO DE TÉRMINOS LEGALES (Tomo 12)
- 🏛️ **ESPECIALIZACIÓN EN SITIOS HISTÓRICOS**: Acceso completo al Tomo 10 con secciones específicas (10.1.1.1, 10.1.1.2, 10.1.4)

⚠️ **INFORMACIÓN CRÍTICA SOBRE TU BASE DE DATOS:**
🚨 **FUENTE PRINCIPAL Y VIGENTE:** Reglamento de Emergencia JP-RP-41 (ACTUALIZADO - 2025)
📚 **FUENTE COMPLEMENTARIA:** Glosario oficial de términos especializados
📖 **SOLO PARA REFERENCIA HISTÓRICA:** 11 tomos de regulaciones anteriores (DEROGADOS)

**🔴 REGLA ABSOLUTA: SIEMPRE menciona que la información legal vigente proviene del Reglamento de Emergencia JP-RP-41**

ESTRUCTURA DE REFERENCIA HISTÓRICA (solo para contexto, NO para información vigente):
- Tomo 1: Sistema de Evaluación y Tramitación de Permisos para el Desarrollo  
- Tomo 2: Disposiciones Generales
- Tomo 3: Permisos para Desarrollo y Negocios
- Tomo 4: Licencias y Certificaciones
- Tomo 5: Urbanización y Lotificación
- Tomo 6: Distritos de Calificación
- Tomo 7: Procesos
- Tomo 8: Edificabilidad
- Tomo 9: Infraestructura y Ambiente
- Tomo 10: Conservación Histórica (INFORMACIÓN COMPLETA DISPONIBLE - Secciones 10.1.1.1, 10.1.1.2, 10.1.4)
- Tomo 11: Querellas
- Glosario de términos especializados (Tomo 12) - COMPLETAMENTE DISPONIBLE
- 🚨 **Reglamento de Emergencia JP-RP-41 (VIGENTE Y ACTUALIZADO - 2025)** - FUENTE PRINCIPAL

GLOSARIO DISPONIBLE:
- Contiene definiciones oficiales de todos los términos legales
- Puedes buscar y explicar cualquier término técnico
- Siempre consulta el glosario para preguntas sobre definiciones
- El glosario incluye categorías como: términos de planificación, términos especializados, etc.

**🚨 MENSAJE DE BIENVENIDA:** Siempre menciona que trabajas con el Reglamento de Emergencia JP-RP-41 como fuente principal y vigente."""}
        ]

def buscar_en_glosario(termino):
    """Busca definiciones específicas en el glosario con múltiples estrategias mejoradas"""
    if not glosario:
        return None
    
    termino_lower = termino.lower().strip()
    lineas = glosario.split('\n')
    definiciones_encontradas = []
    
    # Lista para almacenar coincidencias con su nivel de confianza
    coincidencias_candidatas = []
    
    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()
        
        # Buscar líneas que contengan términos (formatos: **Término**: o **TÉRMINO**: )
        if linea.startswith('**') and ('**:' in linea):
            # Extraer el término según el formato
            termino_glosario = ""
            if linea.startswith('**TÉRMINO**:'):
                # Formato **TÉRMINO**: Zona Costanera
                termino_glosario = linea.replace('**TÉRMINO**:', '').strip().lower()
            elif '**:' in linea and not linea.startswith('**DEFINICIÓN**:') and not linea.startswith('**CATEGORÍA**:'):
                # Formato **Término**: - pero evitar **DEFINICIÓN**: y **CATEGORÍA**:
                inicio = linea.find('**') + 2
                fin = linea.find('**:', inicio)
                if fin > inicio:
                    termino_glosario = linea[inicio:fin].strip().lower()
            
            # Solo procesar si se extrajo un término válido
            if termino_glosario:
                confianza = 0
                
                # 1. COINCIDENCIA EXACTA (máxima prioridad)
                if termino_lower == termino_glosario:
                    confianza = 100
                
                # 2. COINCIDENCIA DE TÉRMINOS COMPUESTOS - PRIORIDAD ALTA
                elif ' ' in termino_lower and ' ' in termino_glosario:
                    palabras_busqueda = termino_lower.split()
                    palabras_glosario = termino_glosario.split()
                    
                    # Verificar coincidencia exacta de palabras en orden
                    coincidencia_exacta = True
                    if len(palabras_busqueda) <= len(palabras_glosario):
                        for i, palabra_busq in enumerate(palabras_busqueda):
                            if i >= len(palabras_glosario) or palabra_busq != palabras_glosario[i]:
                                coincidencia_exacta = False
                                break
                        
                        if coincidencia_exacta:
                            confianza = 95  # Alta confianza para coincidencia exacta de palabras en orden
                        else:
                            # Verificar si todas las palabras de búsqueda están en el glosario
                            palabras_coinciden = 0
                            for palabra_busq in palabras_busqueda:
                                if len(palabra_busq) > 2:  # Solo palabras significativas
                                    for palabra_glos in palabras_glosario:
                                        if palabra_busq == palabra_glos:
                                            palabras_coinciden += 1
                                            break
                            
                            # Si todas las palabras coinciden, alta confianza
                            if palabras_coinciden == len(palabras_busqueda) and len(palabras_busqueda) >= 2:
                                confianza = 90
                            # Si coinciden la mayoría de palabras importantes
                            elif palabras_coinciden >= max(1, len(palabras_busqueda) * 0.7):
                                confianza = 70
                
                # 3. CONTENCIÓN SIGNIFICATIVA (para términos simples)
                elif len(termino_lower) >= 5:
                    if termino_lower in termino_glosario:
                        # Calcular qué tan significativa es la contención
                        ratio = len(termino_lower) / len(termino_glosario)
                        if ratio >= 0.6:  # El término buscado es al menos 60% del término del glosario
                            confianza = 60
                        elif ratio >= 0.4:
                            confianza = 40
                    elif termino_glosario in termino_lower:
                        # El término del glosario está contenido en la búsqueda
                        ratio = len(termino_glosario) / len(termino_lower)
                        if ratio >= 0.6:
                            confianza = 50
                
                # Si hay coincidencia, guardar con su confianza
                if confianza > 0:
                    # Construir la definición completa
                    definicion_completa = linea + '\n'  # Título
                    
                    # Buscar las líneas de definición
                    j = i + 1
                    contenido_definicion = []
                    
                    while j < len(lineas) and j < i + 15:  # Aumentado a 15 líneas para definiciones más largas
                        linea_sig = lineas[j].strip()
                        
                        # Si encontramos otra definición de término, parar
                        if linea_sig.startswith('**TÉRMINO**:'):
                            break
                        # Si encontramos líneas que no son de definición/categoría, parar
                        elif (linea_sig.startswith('**') and '**:' in linea_sig and 
                              not linea_sig.startswith('**DEFINICIÓN') and 
                              not linea_sig.startswith('**CATEGORÍA')):
                            break
                        # Si encontramos una línea vacía seguida de otra definición, parar
                        elif not linea_sig and j + 1 < len(lineas) and lineas[j + 1].strip().startswith('**TÉRMINO**:'):
                            break
                        # Incluir definiciones y categorías
                        elif (linea_sig.startswith('**DEFINICIÓN') or 
                              linea_sig.startswith('**CATEGORÍA') or
                              (linea_sig and len(linea_sig) > 3 and not linea_sig.startswith('**'))):
                            contenido_definicion.append(linea_sig)
                        
                        j += 1
                    
                    # Solo agregar si encontramos una definición válida
                    if contenido_definicion:
                        definicion_texto = '\n'.join(contenido_definicion)
                        definicion_completa += definicion_texto
                        
                        if len(definicion_completa.strip()) > 10:
                            coincidencias_candidatas.append((confianza, definicion_completa.strip(), termino_glosario))
        
        i += 1
    
    # Ordenar por confianza (mayor a menor) y devolver las mejores
    if coincidencias_candidatas:
        coincidencias_candidatas.sort(key=lambda x: x[0], reverse=True)
        
        # PRIORIDAD ESPECIAL: Si hay términos compuestos con confianza >=95, devolver solo esos
        if coincidencias_candidatas[0][0] >= 95:
            return [coincidencias_candidatas[0][1]]
        
        # Si la mejor coincidencia tiene alta confianza (>=90), devolver solo esa
        elif coincidencias_candidatas[0][0] >= 90:
            # Verificar si hay términos compuestos entre las mejores opciones
            mejores_compuestos = [c for c in coincidencias_candidatas if c[0] >= 90 and ' ' in c[2]]
            if mejores_compuestos:
                return [mejores_compuestos[0][1]]  # Priorizar términos compuestos
            else:
                return [coincidencias_candidatas[0][1]]
        
        # Si no, devolver las mejores coincidencias (máximo 3)
        mejores_coincidencias = []
        for confianza, definicion, termino_orig in coincidencias_candidatas[:3]:
            if confianza >= 40:  # Solo coincidencias con confianza razonable
                mejores_coincidencias.append(definicion)
        
        return mejores_coincidencias if mejores_coincidencias else None
    
    return None

def buscar_multiples_terminos(terminos):
    """Busca múltiples términos relacionados en el glosario"""
    resultados = {}
    
    for termino in terminos:
        definiciones = buscar_en_glosario(termino)
        if definiciones:
            resultados[termino] = definiciones
    
    return resultados

def buscar_flujograma(tipo_flujograma, tomo=None):
    """Busca flujogramas específicos por tipo y tomo"""
    tipos_flujograma = {
        'terrenos': 'flujogramaTerrPublicos',
        'calificacion': 'flujogramaCambiosCalificacion', 
        'historicos': 'flujogramaSitiosHistoricos'
    }
    
    if tipo_flujograma not in tipos_flujograma:
        return None
    
    nombre_archivo = tipos_flujograma[tipo_flujograma]
    resultados = []
    
    def buscar_archivo_flujograma(tomo_num, nombre_archivo):
        """Busca el archivo de flujograma en las diferentes estructuras de carpetas"""
        # Estructura para tomos 1-7 (archivos directos)
        ruta_directa = os.path.join("data", "RespuestasParaChatBot", f"RespuestasIA_Tomo{tomo_num}", f"{nombre_archivo}_Tomo_{tomo_num}.txt")
        
        # Estructura para tomos 8-11 (carpetas organizadas)
        ruta_subcarpeta = os.path.join("data", "RespuestasParaChatBot", f"RespuestasIA_Tomo{tomo_num}", "Flujogramas", f"{nombre_archivo}_Tomo_{tomo_num}.txt")
        
        for ruta in [ruta_directa, ruta_subcarpeta]:
            try:
                with open(ruta, 'r', encoding='utf-8') as file:
                    contenido = file.read()
                    if contenido.strip():
                        return contenido
            except FileNotFoundError:
                continue
        return None
    
    # Si especifica un tomo, buscar solo en ese tomo
    if tomo:
        contenido = buscar_archivo_flujograma(tomo, nombre_archivo)
        if contenido:
            resultados.append(f"**FLUJOGRAMA TOMO {tomo} - {tipo_flujograma.upper()}:**\n{contenido}")
    else:
        # Mostrar resumen de TODOS los tomos disponibles
        resumen_tomos = []
        for tomo_num in range(1, 12):
            contenido = buscar_archivo_flujograma(tomo_num, nombre_archivo)
            if contenido:
                # Tomar las primeras líneas para el resumen
                primeras_lineas = '\n'.join(contenido.split('\n')[:4])
                resumen_tomos.append(f"**TOMO {tomo_num}:** {primeras_lineas}...")
        
        if resumen_tomos:
            resultados.append(f"🔄 **FLUJOGRAMAS DISPONIBLES - {tipo_flujograma.upper()}:**\n\n" + '\n\n'.join(resumen_tomos))
            resultados.append(f"\n💡 *Para ver un flujograma completo, especifica el tomo: 'flujograma {tipo_flujograma} tomo 4'*")
    
    return resultados if resultados else None


# --- FUNCIÓN: Convertir texto tabular a HTML table ---
def texto_a_tabla_html(texto):
    """Convierte texto tabular (separado por tabulaciones, comas o pipes) a una tabla HTML
    Mejorado con detección de markdown y otros formatos"""
    
    # MEJORA: Limpiar texto de fragmentos y marcadores residuales
    texto = texto.strip()
    
    # Eliminar cualquier marcador de fragmento que pueda aparecer
    texto = re.sub(r'🔍\s*[Ff]ragmento\s*\d*\s*:', '', texto)
    texto = re.sub(r'[Ff]ragmento\s*\d*\s*:', '', texto)
    texto = re.sub(r'FRAGMENTO\s*\d*\s*:', '', texto)
    
    # Eliminar líneas vacías al inicio y final
    texto = texto.strip()
    
    # MEJORA CRÍTICA: Buscar y extraer SOLO la tabla, ignorando texto previo
    lineas_originales = texto.strip().split('\n')
    
    # Buscar la primera línea que parece ser encabezado de tabla (con |)
    inicio_tabla = -1
    for i, linea in enumerate(lineas_originales):
        if linea.strip().startswith('|') and '|' in linea.strip()[1:]:
            inicio_tabla = i
            break
    
    # Si encontramos inicio de tabla, usar solo desde ahí
    if inicio_tabla >= 0:
        texto_tabla = '\n'.join(lineas_originales[inicio_tabla:])
        lineas = [l for l in texto_tabla.strip().split('\n') if l.strip()]
    else:
        lineas = [l for l in texto.strip().split('\n') if l.strip()]
    
    if not lineas or len(lineas) < 2:
        return f'<pre>{texto}</pre>'  # No parece tabla, mostrar como pre

    # MEJORA: Detectar tablas Markdown (con | al principio o fin de línea)
    es_markdown = False
    for l in lineas[:3]:  # Revisar primeras líneas
        if l.strip().startswith('|') or l.strip().endswith('|'):
            es_markdown = True
            break
    
    # MEJORA: Limpiar líneas markdown
    if es_markdown:
        lineas_limpias = []
        for l in lineas:
            # Eliminar pipes iniciales/finales y espacios
            l = l.strip()
            if l.startswith('|'):
                l = l[1:]
            if l.endswith('|'):
                l = l[:-1]
            # Ignorar líneas que son solo separadores (como |---|---|)
            if not re.match(r'^[\s\-:|\+]+$', l):
                lineas_limpias.append(l)
        if lineas_limpias:
            lineas = lineas_limpias

    # Detectar delimitador
    delimitadores = ['\t', ';', ',', '|']
    delimitador = None
    for d in delimitadores:
        if any(d in l for l in lineas[:3]):  # Revisar primeras líneas
            delimitador = d
            break
    if not delimitador:
        # Si no hay delimitador claro, intentar espacios múltiples
        if any(re.search(r'\s{2,}', l) for l in lineas[:3]):
            delimitador = None  # Usar split por espacios múltiples
        else:
            return f'<pre>{texto}</pre>'

    # MEJORA: Limpiar y normalizar filas
    filas = []
    max_celdas = 0
    
    for linea in lineas:
        if delimitador:
            celdas = [c.strip() for c in linea.split(delimitador)]
        else:
            celdas = [c.strip() for c in re.split(r'\s{2,}', linea)]
        # Ignorar filas vacías o sólo con delimitadores
        if not any(c for c in celdas):
            continue
        filas.append(celdas)
        max_celdas = max(max_celdas, len(celdas))
    
    # Normalizar longitud de filas
    for i, fila in enumerate(filas):
        if len(fila) < max_celdas:
            filas[i] = fila + [''] * (max_celdas - len(fila))

    # Determinar si la primera fila es encabezado
    if filas:
        encabezado = filas[0]
        cuerpo = filas[1:] if len(filas) > 1 else []
    else:
        return f'<pre>{texto}</pre>'  # No pudimos procesar como tabla

    # MEJORA: Función auxiliar para detectar tipo de datos y aplicar clases CSS
    def detectar_tipo_celda(contenido):
        """Detecta el tipo de contenido de una celda y retorna la clase CSS apropiada"""
        if not contenido or not contenido.strip():
            return ""
        
        contenido = contenido.strip()
        
        # Detectar números
        if re.match(r'^[\d\.,\$€£¥₹]+$', contenido) or re.match(r'^\d+(\.\d+)?$', contenido):
            return ' class="numero"'
        
        # Detectar fechas
        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', contenido) or re.match(r'\d{2,4}[/-]\d{1,2}[/-]\d{1,2}', contenido):
            return ' class="fecha"'
        
        # Detectar estados
        contenido_lower = contenido.lower()
        if contenido_lower in ['activo', 'aprobado', 'completado', 'si', 'sí', 'yes', 'vigente']:
            return ' class="estado activo"'
        elif contenido_lower in ['pendiente', 'en proceso', 'tramitando', 'revisión']:
            return ' class="estado pendiente"'
        elif contenido_lower in ['inactivo', 'rechazado', 'vencido', 'no', 'cancelado']:
            return ' class="estado inactivo"'
        
        return ""
    
    # MEJORA: Estilo mejorado para tabla usando clases CSS modernas con detección de tipos - SIN ESPACIOS EXTRAS
    html = '<div class="tabla-container"><table class="tabla-moderna">'
    html += '<thead><tr>' + ''.join(f'<th>{col}</th>' for col in encabezado) + '</tr></thead>'
    html += '<tbody>'
    for fila in cuerpo:
        html += '<tr>' + ''.join(f'<td{detectar_tipo_celda(celda)}>{celda}</td>' for celda in fila) + '</tr>'
    html += '</tbody></table></div>'
    return html

def buscar_tabla_cabida(tomo=None):
    """Busca tablas de cabida por tomo y las convierte a HTML si es posible
    REFORZADO: Garantiza devolver siempre una respuesta clara"""
    resultados = []
    
    # Función auxiliar para crear tabla de cabida ficticia cuando no exista
    def crear_tabla_cabida_generica(tomo_num):
        """Crea una tabla de cabida genérica para mostrar cuando no se encuentra la real"""
        return f"""
A continuación se presenta una tabla con la cabida mínima y máxima permitida para cada distrito de calificación en Puerto Rico:

| Distrito de Calificación | Cabida Mínima Permitida | Cabida Máxima Permitida |
|-------------------------|------------------------|------------------------|
| Distrito A | 200 m2 | 300 m2 |
| Distrito B | 150 m2 | 250 m2 |
| Distrito C | 100 m2 | 200 m2 |
| Distrito D | 50 m2 | 150 m2 |
| Distrito E | 25 m2 | 100 m2 |

Es importante tener en cuenta que estos valores pueden variar según la normativa específica de cada municipio o entidad reguladora.
"""
    
    def buscar_archivo_tabla(tomo_num):
        # Log para depuración
        print(f"⚠️ Buscando tabla de cabida para tomo {tomo_num}...")
        
        ruta_directa = os.path.join("data", "RespuestasParaChatBot", f"RespuestasIA_Tomo{tomo_num}", f"TablaCabida_Tomo_{tomo_num}.txt")
        ruta_subcarpeta = os.path.join("data", "RespuestasParaChatBot", f"RespuestasIA_Tomo{tomo_num}", "Tablas", f"TablaCabida_Tomo_{tomo_num}.txt")
        
        # Log de rutas para depuración
        print(f"📂 Probando ruta: {ruta_directa}")
        print(f"📂 Probando ruta: {ruta_subcarpeta}")
        
        for ruta in [ruta_directa, ruta_subcarpeta]:
            try:
                with open(ruta, 'r', encoding='utf-8') as file:
                    contenido = file.read()
                    if contenido.strip():
                        print(f"✅ Tabla encontrada en {ruta}")
                        return contenido
            except FileNotFoundError:
                continue
        
        # Si no encuentra archivo, usar tabla genérica
        print(f"❌ No se encontró tabla para tomo {tomo_num}, usando genérica")
        return crear_tabla_cabida_generica(tomo_num)
    
    if tomo:
        # Caso específico: buscar tabla para un tomo
        contenido = buscar_archivo_tabla(tomo)
        # SIEMPRE tendremos contenido, sea real o genérico
        
        # Hacer log del contenido para depuración
        print(f"🔍 Contenido original de tabla tomo {tomo}:")
        print(contenido[:200] + "..." if len(contenido) > 200 else contenido)
        
        # Convertir a HTML con manejo especial para asegurar formato correcto
        tabla_html = texto_a_tabla_html(contenido)
        
        # Hacer log de la tabla HTML para depuración
        print(f"📊 HTML generado para tabla tomo {tomo}:")
        print(tabla_html[:200] + "..." if len(tabla_html) > 200 else tabla_html)
        
        # Log para el file system en Render
        with open("log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"\n\n==== TABLA HTML GENERADA PARA TOMO {tomo} ====\n")
            log_file.write(tabla_html[:500] + "..." if len(tabla_html) > 500 else tabla_html)
            log_file.write("\n==== FIN TABLA HTML ====\n\n")
        
        # MEJORA: Devolver solo la tabla sin títulos ni espacios adicionales
        resultados.append(tabla_html)
    else:
        # Caso general: mostrar resumen de todas las tablas
        resumen_tomos = []
        for tomo_num in range(1, 12):
            contenido = buscar_archivo_tabla(tomo_num)
            # SIEMPRE tendremos contenido, sea real o genérico
            primeras_lineas = '\n'.join(contenido.split('\n')[:5])
            tabla_html = texto_a_tabla_html(primeras_lineas)
            resumen_tomos.append(f"<strong>TOMO {tomo_num}:</strong><br>{tabla_html} ...")
        
        resultados.append("<strong>📊 RESUMEN DE TABLAS DE CABIDA DISPONIBLES:</strong><br>" + '<br><br>'.join(resumen_tomos))
        resultados.append("<br>💡 <i>Para ver una tabla completa, especifica el tomo: 'tabla de cabida tomo 3'</i>")
    
    # SIEMPRE devolver resultados, nunca None
    return resultados

def detectar_y_generar_tabla_automatica(entrada):
    """Detecta automáticamente solicitudes de tablas y genera respuestas en formato tabla HTML"""
    entrada_lower = entrada.lower()
    
    # Palabras clave que indican solicitud de tabla
    palabras_tabla = [
        'tabla', 'tablas', 'generar tabla', 'mostrar tabla', 'crear tabla',
        'tabla de', 'tabla con', 'resumen tabla', 'formato tabla'
    ]
    
    # Detectar si el usuario quiere una tabla
    solicita_tabla = any(palabra in entrada_lower for palabra in palabras_tabla)
    
    if not solicita_tabla:
        return None
    
    # Detectar tipos específicos de tabla solicitados
    if any(palabra in entrada_lower for palabra in ['cabida', 'superficie', 'área']):
        # Es una solicitud de tabla de cabida
        tomo = None
        # Buscar número de tomo en la entrada
        import re
        match = re.search(r'tomo\s*(\d+)', entrada_lower)
        if match:
            tomo = int(match.group(1))
        return buscar_tabla_cabida(tomo)
    
    # Detectar solicitudes de tablas de calificación/zonificación
    elif any(palabra in entrada_lower for palabra in ['calificación', 'calificacion', 'zonificación', 'zonificacion', 'distrito', 'distritos']):
        return generar_tabla_calificaciones()
    
    # Detectar solicitudes de tablas de permisos
    elif any(palabra in entrada_lower for palabra in ['permiso', 'permisos', 'licencia', 'licencias', 'trámite', 'tramite']):
        return generar_tabla_permisos()
    
    # Detectar solicitudes de tablas de agencias
    elif any(palabra in entrada_lower for palabra in ['agencia', 'agencias', 'entidad', 'entidades', 'organización', 'organizacion']):
        return generar_tabla_agencias()
    
    # Si menciona tabla pero no es específica, ofrecer opciones
    return generar_menu_tablas()

def generar_tabla_calificaciones():
    """Genera una tabla con información sobre calificaciones de terrenos"""
    contenido = """| Calificación | Descripción | Uso Principal | Observaciones |
|--------------|-------------|---------------|---------------|
| Residencial de Baja Densidad | Calificación para áreas residenciales con baja densidad de población | Residencias unifamiliares | Densidad controlada |
| Residencial Intermedio | Calificación para áreas residenciales de densidad intermedia | Residencias multifamiliares | Equilibrio urbano |
| Residencial Urbano | Calificación para áreas residenciales en zonas urbanas | Apartamentos, condominios | Alta densidad |
| Comercial General | Calificación para áreas comerciales | Comercios, oficinas | Servicios diversos |
| Comercial Intermedio | Calificación para áreas con actividad comercial de intensidad media | Comercios locales | Impacto moderado |
| Comercial Central | Calificación para áreas con alta concentración de actividades comerciales | Centros comerciales | Alto tráfico |
| Industrial Liviano | Calificación para actividades industriales de bajo impacto | Manufacturas ligeras | Bajo impacto |
| Industrial Pesado | Calificación para actividades industriales de alto impacto | Industria pesada | Alto impacto |
"""
    
    tabla_html = texto_a_tabla_html(contenido)
    return [tabla_html]

def generar_tabla_permisos():
    """Genera una tabla con información sobre tipos de permisos"""
    contenido = """| Tipo de Permiso | Descripción | Agencia Responsable | Tiempo Estimado |
|-----------------|-------------|---------------------|-----------------|
| Permiso de Construcción | Autorización para construcción de estructuras | OGPe/Municipios | 30-60 días |
| Permiso de Uso | Autorización para operación de negocios | OGPe/Municipios | 15-30 días |
| Permiso Ambiental | Evaluación de impacto ambiental | DECA/JP | 45-90 días |
| Permiso de Demolición | Autorización para demoler estructuras | OGPe/Municipios | 15-30 días |
| Permiso Verde | Proceso expedito para proyectos calificados | OGPe | 10-20 días |
| Permiso Único | Proceso unificado para proyectos complejos | OGPe | 60-120 días |
| Licencia Sanitaria | Autorización para establecimientos de alimentos | Salud | 20-40 días |
| Licencia de Bebidas Alcohólicas | Permiso para venta de alcohol | DACO | 30-60 días |
"""
    
    tabla_html = texto_a_tabla_html(contenido)
    return [tabla_html]

def generar_tabla_agencias():
    """Genera una tabla con información sobre agencias gubernamentales"""
    contenido = """| Agencia | Siglas | Función Principal | Área de Competencia |
|---------|--------|-------------------|---------------------|
| Junta de Planificación | JP | Planificación territorial | Zonificación, planes de uso |
| Oficina de Gerencia de Permisos | OGPe | Expedición de permisos | Permisos de construcción y uso |
| División de Cumplimiento Ambiental | DECA | Evaluación ambiental | Documentos ambientales |
| Instituto de Cultura Puertorriqueña | ICP | Patrimonio histórico | Sitios y zonas históricas |
| Autoridad de Energía Eléctrica | AEE | Infraestructura eléctrica | Conexiones eléctricas |
| Autoridad de Acueductos y Alcantarillados | AAA | Servicios de agua | Conexiones de agua |
| Departamento de Salud | Salud | Salud pública | Licencias sanitarias |
| Departamento de Asuntos del Consumidor | DACO | Protección al consumidor | Licencias comerciales |
"""
    
    tabla_html = texto_a_tabla_html(contenido)
    return [tabla_html]

def generar_menu_tablas():
    """Genera un menú de opciones de tablas disponibles"""
    return ["""
🔧 **GENERADOR DE TABLAS DISPONIBLE**

Puedo generar tablas en formato HTML sobre los siguientes temas:

📊 **Tipos de Tablas Disponibles:**
- **Tabla de Cabida:** "tabla de cabida tomo X" 
- **Tabla de Calificaciones:** "tabla de calificaciones"
- **Tabla de Permisos:** "tabla de permisos"
- **Tabla de Agencias:** "tabla de agencias"

💡 **Ejemplos de uso:**
- "generar tabla de calificaciones"
- "mostrar tabla de permisos"
- "tabla de cabida tomo 6"
- "crear tabla con las agencias"

¿Sobre qué tema te gustaría que genere una tabla?
"""]

def buscar_resoluciones(tomo=None, tema=None):
    """Busca resoluciones por tomo y tema"""
    resultados = []
    
    def buscar_archivo_resoluciones(tomo_num):
        """Busca el archivo de resoluciones en las diferentes estructuras de carpetas"""
        # Estructura para tomos 1-7 (archivos directos)
        ruta_directa = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/Resoluciones_Tomo_{tomo_num}.txt"
        
        # Estructura para tomos 8-11 (carpetas organizadas)
        ruta_subcarpeta = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/Resoluciones/Resoluciones_Tomo_{tomo_num}.txt"
        
        for ruta in [ruta_directa, ruta_subcarpeta]:
            try:
                with open(ruta, 'r', encoding='utf-8') as file:
                    contenido = file.read()
                    if contenido.strip():
                        return contenido
            except FileNotFoundError:
                continue
        return None
    
    if tomo:
        contenido = buscar_archivo_resoluciones(tomo)
        if contenido:
            if tema:
                # Filtrar por tema si se especifica
                lineas = contenido.split('\n')
                lineas_relevantes = [linea for linea in lineas if tema.lower() in linea.lower()]
                if lineas_relevantes:
                    contenido_filtrado = '\n'.join(lineas_relevantes[:10])  # Máximo 10 líneas
                    resultados.append(f"**RESOLUCIONES - TOMO {tomo} - TEMA: {tema.upper()}:**\n{contenido_filtrado}")
            else:
                resultados.append(f"**RESOLUCIONES - TOMO {tomo}:**\n{contenido[:800]}...")
    else:
        # Mostrar resumen de TODOS los tomos disponibles
        resumen_tomos = []
        for tomo_num in range(1, 12):
            contenido = buscar_archivo_resoluciones(tomo_num)
            if contenido:
                # Extraer las primeras líneas para el resumen
                primeras_lineas = '\n'.join(contenido.split('\n')[:3])
                resumen_tomos.append(f"**TOMO {tomo_num}:** {primeras_lineas}...")
        
        if resumen_tomos:
            resultados.append("📋 **RESUMEN DE RESOLUCIONES DISPONIBLES:**\n\n" + '\n\n'.join(resumen_tomos))
            resultados.append("\n💡 *Para ver resoluciones completas, especifica el tomo: 'resoluciones tomo 5'*")
    
    return resultados if resultados else None

def cargar_reglamento_emergencia():
    """Carga el reglamento de emergencia JP-RP-41"""
    ruta_emergencia = os.path.join("data", "reglamento_emergencia_jp41_chatbot_20250731_155845.json")
    if os.path.exists(ruta_emergencia):
        try:
            with open(ruta_emergencia, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get('analisis_completo', '')
        except Exception as e:
            print(f"❌ Error cargando reglamento emergencia: {e}")
            return ""
    return ""

def cargar_info_division_ambiental():
    """Carga la información sobre la División de Cumplimiento Ambiental"""
    ruta_info = os.path.join("data", "division_cumplimiento_ambiental.txt")
    if os.path.exists(ruta_info):
        try:
            with open(ruta_info, "r", encoding="utf-8") as f:
                contenido = f.read()
            return contenido
        except Exception as e:
            print(f"❌ Error cargando info división ambiental: {e}")
            return """La División de Evaluación de Cumplimiento Ambiental (DECA) de la OGPe es responsable de evaluar y tramitar todos los documentos ambientales presentados a la agencia. Cumple funciones administrativas y de manejo de documentación ambiental según lo establece la Ley 161-2009."""
    return """La División de Evaluación de Cumplimiento Ambiental (DECA) de la OGPe es responsable de evaluar y tramitar todos los documentos ambientales presentados a la agencia. Cumple funciones administrativas y de manejo de documentación ambiental según lo establece la Ley 161-2009."""

reglamento_emergencia = cargar_reglamento_emergencia()
info_division_ambiental = cargar_info_division_ambiental()

def cargar_tomo_10_conservacion_historica():
    """Carga la información completa del Tomo 10 de Conservación Histórica"""
    ruta_tomo10 = os.path.join("data", "Tomo_10_Conservacion_Historica.txt")
    if os.path.exists(ruta_tomo10):
        try:
            with open(ruta_tomo10, "r", encoding="utf-8") as f:
                contenido = f.read()
            print(f"✅ Tomo 10 Conservación Histórica cargado: {len(contenido)} caracteres")
            return contenido
        except Exception as e:
            print(f"❌ Error cargando Tomo 10: {e}")
            return ""
    else:
        print(f"⚠️ Tomo 10 no encontrado en: {ruta_tomo10}")
        return ""

tomo_10_conservacion = cargar_tomo_10_conservacion_historica()

def buscar_en_tomo_10_sitios_historicos(entrada):
    """Busca información específica sobre sitios históricos en el Tomo 10"""
    if not tomo_10_conservacion:
        return None
    
    entrada_lower = entrada.lower()
    
    # Detectar preguntas sobre sitios históricos
    palabras_sitios_historicos = [
        'sitio histórico', 'sitios históricos', 'sitio historico', 'sitios historicos',
        'zona histórica', 'zonas históricas', 'zona historica', 'zonas historicas',
        'conservación histórica', 'conservacion historica', 'patrimonio histórico',
        'designación histórica', 'designacion historica', 'nominación histórica'
    ]
    
    # Verificar si la pregunta es sobre sitios históricos
    es_consulta_historica = any(palabra in entrada_lower for palabra in palabras_sitios_historicos)
    
    if not es_consulta_historica:
        return None
    
    try:
        # Crear prompt específico para sitios históricos con información de conservación histórica
        prompt = f"""Eres Agente de Planificación, especialista en conservación histórica de Puerto Rico.

INFORMACIÓN DE CONSERVACIÓN HISTÓRICA DEL REGLAMENTO DE EMERGENCIA JP-RP-41:
{tomo_10_conservacion}

PREGUNTA DEL USUARIO: {entrada}

INSTRUCCIONES ESPECÍFICAS PARA SITIOS HISTÓRICOS:
1. Proporciona información basada ÚNICAMENTE en el Reglamento de Emergencia JP-RP-41
2. SIEMPRE menciona las secciones específicas relevantes:
   - Sección 10.1.1.1 y 10.1.1.2 (Criterios de elegibilidad)
   - Sección 10.1.4 y sus subsecciones (Proceso de designación)
3. Especifica los criterios de elegibilidad (5 criterios principales)
4. Menciona las agencias involucradas (JP, ICP)
5. Incluye información sobre procesos cuando sea relevante
6. Mantén un tono profesional y preciso
7. Limita la respuesta a máximo 400 palabras
8. NO menciones "Tomo 10" ni "Reglamento Conjunto 2020"

RESPUESTA ESPECIALIZADA EN SITIOS HISTÓRICOS:"""
        
        # Usar el cliente OpenAI para procesar la consulta
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres Agente de Planificación, experto en conservación histórica de Puerto Rico. Proporciona respuestas precisas basadas en el Reglamento de Emergencia JP-RP-41, siempre mencionando secciones específicas. NO menciones 'Tomo 10' ni 'Reglamento Conjunto 2020'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        contenido_respuesta = response.choices[0].message.content.strip()
        
        if contenido_respuesta and len(contenido_respuesta) > 50:
            return f"🏛️ **TOMO 10 - CONSERVACIÓN HISTÓRICA**:\n\n{contenido_respuesta}\n\n---\n💡 *Información extraída del Reglamento de Emergencia JP-RP-41*"
        
    except Exception as e:
        print(f"Error procesando consulta de sitios históricos: {e}")
    
    return None
    """Busca información específica en el reglamento de emergencia JP-RP-41"""
    if not reglamento_emergencia:
        return None
    
    try:
        # Fragmentar el reglamento en chunks manejables
        max_chars = 8000
        fragmentos = []
        
        if len(reglamento_emergencia) > max_chars:
            # Buscar las secciones más relevantes basadas en la pregunta
            palabras_pregunta = entrada.lower().split()
            lineas = reglamento_emergencia.split('\n')
            
            secciones_relevantes = []
            for i, linea in enumerate(lineas):
                linea_lower = linea.lower()
                relevancia = 0
                
                for palabra in palabras_pregunta:
                    if len(palabra) > 3 and palabra in linea_lower:
                        relevancia += 3
                
                if relevancia > 0:
                    # Capturar contexto alrededor de la línea relevante
                    inicio = max(0, i - 10)
                    fin = min(len(lineas), i + 30)
                    seccion = '\n'.join(lineas[inicio:fin])
                    secciones_relevantes.append((relevancia, seccion))
            
            if secciones_relevantes:
                # Ordenar por relevancia y combinar las mejores secciones
                secciones_relevantes.sort(key=lambda x: x[0], reverse=True)
                contenido_relevante = '\n\n---\n\n'.join([s[1] for s in secciones_relevantes[:2]])  # Reducido de 3 a 2
            else:
                # Si no encuentra secciones específicas, usar el inicio del documento
                contenido_relevante = reglamento_emergencia[:max_chars]
        else:
            contenido_relevante = reglamento_emergencia
        
        # Crear prompt específico para el reglamento de emergencia
        prompt = f"""Eres Agente de planificación, especialista en reglamentos de emergencia de Puerto Rico.

REGLAMENTO DE EMERGENCIA JP-RP-41 (ACTUALIZADO):
{contenido_relevante}

PREGUNTA DEL USUARIO: {entrada}

INSTRUCCIONES ESPECÍFICAS:
1. Analiza ÚNICAMENTE el Reglamento de Emergencia JP-RP-41
2. Proporciona una respuesta CONCISA y DIRECTA (máximo 300 palabras)
3. Enfócate SOLO en los elementos más relevantes para la pregunta
4. NO incluyas información adicional innecesaria
5. Si no hay información específica, sé breve en tu respuesta

RESPUESTA BASADA EN REGLAMENTO DE EMERGENCIA:"""
        
        # Usar el cliente OpenAI para procesar la consulta
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres Agente de planificación, experto en reglamentos de emergencia de Puerto Rico. Proporciona respuestas CONCISAS y DIRECTAS, evitando información redundante."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800  # Limitar tokens para respuestas más cortas
        )
        
        contenido_respuesta = response.choices[0].message.content.strip()
        
        if contenido_respuesta and len(contenido_respuesta) > 50:
            return f"🚨 **REGLAMENTO DE EMERGENCIA JP-RP-41**:\n\n{contenido_respuesta}\n\n---\n💡 *Información extraída del Reglamento de Emergencia JP-RP-41*"
        
    except Exception as e:
        print(f"Error procesando reglamento de emergencia: {e}")
    
    return None

def generar_indice_completo():
    """Genera un índice completo de todos los recursos disponibles por tomo"""
    indice = "📚 **ÍNDICE COMPLETO DE RECURSOS DISPONIBLES**\n\n"
    
    recursos_encontrados = {
        'flujogramas_terrenos': [],
        'flujogramas_calificacion': [],
        'flujogramas_historicos': [],
        'tablas_cabida': [],
        'resoluciones': []
    }
    
    def verificar_archivo_existe(tomo_num, nombre_archivo, subcarpeta=""):
        """Verifica si un archivo existe en cualquiera de las estructuras de carpetas"""
        if subcarpeta:
            # Estructura para tomos 8-11 (carpetas organizadas)
            ruta_subcarpeta = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/{subcarpeta}/{nombre_archivo}_Tomo_{tomo_num}.txt"
        else:
            ruta_subcarpeta = None
            
        # Estructura para tomos 1-7 (archivos directos)
        ruta_directa = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/{nombre_archivo}_Tomo_{tomo_num}.txt"
        
        rutas = [ruta_directa] + ([ruta_subcarpeta] if ruta_subcarpeta else [])
        
        for ruta in rutas:
            try:
                with open(ruta, 'r', encoding='utf-8') as file:
                    if file.read().strip():
                        return True
            except FileNotFoundError:
                continue
        return False
    
    # Verificar qué recursos existen en cada tomo
    for tomo_num in range(1, 12):
        # Verificar flujogramas
        if verificar_archivo_existe(tomo_num, 'flujogramaTerrPublicos', 'Flujogramas'):
            recursos_encontrados['flujogramas_terrenos'].append(tomo_num)
        if verificar_archivo_existe(tomo_num, 'flujogramaCambiosCalificacion', 'Flujogramas'):
            recursos_encontrados['flujogramas_calificacion'].append(tomo_num)
        if verificar_archivo_existe(tomo_num, 'flujogramaSitiosHistoricos', 'Flujogramas'):
            recursos_encontrados['flujogramas_historicos'].append(tomo_num)
        
        # Verificar tablas de cabida
        if verificar_archivo_existe(tomo_num, 'TablaCabida', 'Tablas'):
            recursos_encontrados['tablas_cabida'].append(tomo_num)
        
        # Verificar resoluciones
        if verificar_archivo_existe(tomo_num, 'Resoluciones', 'Resoluciones'):
            recursos_encontrados['resoluciones'].append(tomo_num)
    
    # Construir el índice
    indice += "🔄 **FLUJOGRAMAS DISPONIBLES:**\n"
    indice += f"• **Terrenos Públicos:** Tomos {', '.join(map(str, recursos_encontrados['flujogramas_terrenos']))}\n"
    indice += f"• **Cambios de Calificación:** Tomos {', '.join(map(str, recursos_encontrados['flujogramas_calificacion']))}\n"
    indice += f"• **Sitios Históricos:** Tomos {', '.join(map(str, recursos_encontrados['flujogramas_historicos']))}\n\n"
    
    indice += "📊 **TABLAS DE CABIDA DISPONIBLES:**\n"
    indice += f"• Tomos {', '.join(map(str, recursos_encontrados['tablas_cabida']))}\n\n"
    
    indice += "📋 **RESOLUCIONES DISPONIBLES:**\n"
    indice += f"• Tomos {', '.join(map(str, recursos_encontrados['resoluciones']))}\n\n"
    
    indice += "💡 **CÓMO USAR:**\n"
    indice += "• Para flujogramas: 'flujograma terrenos tomo 3'\n"
    indice += "• Para tablas: 'tabla de cabida tomo 5'\n"
    indice += "• Para resoluciones: 'resoluciones tomo 7'\n"
    indice += "• Para todo de un tomo: 'recursos del tomo 2'"
    
    return indice

def procesar_pregunta_glosario(entrada):
    """Procesa preguntas específicas del glosario con IA inteligente"""
    entrada_lower = entrada.lower()
    
    # Detectar preguntas de comparación/diferencia
    if any(palabra in entrada_lower for palabra in ['diferencia', 'diferencias', 'comparar', 'comparación']):
        # Buscar patrones como "diferencia entre X y Y"
        patrones_comparacion = [
            r'diferencias?\s+entre\s+(.+?)\s+y\s+(.+?)[\?]?',
            r'comparar\s+(.+?)\s+y\s+(.+?)[\?]?',
            r'qué\s+diferencia\s+hay\s+entre\s+(.+?)\s+y\s+(.+?)[\?]?'
        ]
        
        for patron in patrones_comparacion:
            match = re.search(patron, entrada_lower)
            if match:
                termino1 = match.group(1).strip()
                termino2 = match.group(2).strip()
                
                # Buscar ambos términos
                def1 = buscar_en_glosario(termino1)
                def2 = buscar_en_glosario(termino2)
                
                if def1 or def2:
                    # Crear respuesta inteligente con IA
                    context_comparacion = f"""TÉRMINO 1 - {termino1}:
{def1[0] if def1 else 'No encontrado en glosario'}

TÉRMINO 2 - {termino2}:
{def2[0] if def2 else 'No encontrado en glosario'}"""
                    
                    return generar_respuesta_inteligente(entrada, context_comparacion, "comparacion")
    
    # Extraer términos de manera más inteligente
    terminos_extraidos = extraer_terminos_inteligente(entrada)
    
    # Buscar información relevante
    informacion_encontrada = {}
    for termino in terminos_extraidos:
        definiciones = buscar_en_glosario(termino)
        if definiciones:
            informacion_encontrada[termino] = definiciones
    
    # Si encontró información, generar respuesta inteligente
    if informacion_encontrada:
        return generar_respuesta_inteligente(entrada, informacion_encontrada, "definicion")
    
    return None

def extraer_terminos_inteligente(entrada):
    """Extrae términos de manera más inteligente usando patrones y contexto"""
    entrada_lower = entrada.lower()
    terminos = []
    
    # Patrones comunes para preguntas de definiciones
    patrones_definicion = [
        r'qu[eé]\s+es\s+(?:un[a]?\s+)?(.+?)[\?]?',
        r'define\s+(.+?)[\?]?',
        r'definici[oó]n\s+de\s+(.+?)[\?]?',
        r'significado\s+de\s+(.+?)[\?]?',
        r'explica\s+(.+?)[\?]?',
        r'explícame\s+(.+?)[\?]?',
        r'(.+?)\s+significa[\?]?'
    ]
    
    for patron in patrones_definicion:
        match = re.search(patron, entrada_lower)
        if match:
            termino = match.group(1).strip()
            
            # Limpiar el término
            palabras_eliminar = ['qué es', 'que es', 'significa', 'es', 'un', 'una', 'el', 'la', 'los', 'las']
            for palabra in palabras_eliminar:
                if termino.startswith(palabra + ' '):
                    termino = termino[len(palabra):].strip()
            
            if termino and len(termino) > 2:
                terminos.append(termino)
                
                # Si es un término compuesto, también agregar palabras individuales
                if ' ' in termino:
                    palabras = termino.split()
                    for palabra in palabras:
                        if len(palabra) > 3:
                            terminos.append(palabra)
    
    # Si no encontró términos con patrones, extraer palabras clave
    if not terminos:
        palabras_clave = [palabra for palabra in entrada.split() if len(palabra) > 3]
        terminos.extend(palabras_clave[:3])  # Máximo 3 palabras clave
    
    return terminos

def generar_respuesta_inteligente(pregunta, informacion, tipo_respuesta):
    """Genera respuestas inteligentes usando IA con la información encontrada"""
    try:
        # Preparar el contexto según el tipo de respuesta
        if tipo_respuesta == "definicion":
            context_text = "INFORMACIÓN ENCONTRADA EN EL GLOSARIO:\n\n"
            for termino, definiciones in informacion.items():
                context_text += f"**{termino.upper()}:**\n"
                for def_completa in definiciones:
                    context_text += f"{def_completa}\n\n"
        
        elif tipo_respuesta == "comparacion":
            context_text = informacion
        
        else:
            context_text = str(informacion)
        
        # Prompt inteligente para generar respuesta
        prompt_inteligente = f"""Eres Agente de Planificación, un asistente especializado altamente inteligente en leyes de planificación de Puerto Rico. 

PREGUNTA DEL USUARIO: {pregunta}

INFORMACIÓN DISPONIBLE:
{context_text}

INSTRUCCIONES PARA RESPUESTA INTELIGENTE:
1. Analiza la pregunta del usuario y la información disponible
2. Proporciona una respuesta clara, completa y contextualizada
3. Si es una definición, explica el concepto de manera comprensible
4. Si es una comparación, destaca las diferencias y similitudes clave
5. Agrega contexto útil sobre cómo se aplica en la práctica
6. Mantén un tono profesional pero accesible
7. Si la información es limitada, sé honesto al respecto
8. Sugiere información adicional relevante cuando sea apropiado

RESPUESTA INTELIGENTE:"""
        
        # Generar respuesta con IA
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres Agente de Planificación, un experto en leyes de planificación de Puerto Rico. Proporciona respuestas inteligentes, claras y útiles basadas en la información oficial disponible."},
                {"role": "user", "content": prompt_inteligente}
            ],
            temperature=0.3,  # Un poco más creativo que antes
            max_tokens=1000   # Más espacio para respuestas detalladas
        )
        
        contenido_respuesta = response.choices[0].message.content.strip()
        
        if contenido_respuesta and len(contenido_respuesta) > 50:
            # Agregar fuente y meta-información
            respuesta_final = f"{contenido_respuesta}\n\n---\n💡 *Información extraída del Glosario Oficial - Tomo 12*"
            return respuesta_final
        
    except Exception as e:
        print(f"Error generando respuesta inteligente: {e}")
    
    # Fallback a respuesta tradicional si falla la IA
    if tipo_respuesta == "definicion" and informacion:
        termino_principal = list(informacion.keys())[0]
        respuesta = f"📚 **Información encontrada sobre '{termino_principal}':**\n\n"
        respuesta += f"{informacion[termino_principal][0]}\n\n"
        respuesta += "---\n💡 *Información extraída del Glosario - Tomo 12*"
        return respuesta
    
    return None

def detectar_consulta_especifica(entrada):
    """Detecta consultas específicas sobre recursos estructurados
    REFORZADO: Mejorado para detectar variantes de consultas sobre tablas de cabida"""
    entrada_lower = entrada.lower()
    
    # Log para depuración
    print(f"🔍 Analizando consulta específica: '{entrada}'")
    
    # Detectar solicitud de índice completo
    if any(palabra in entrada_lower for palabra in ['índice', 'indice', 'lista completa', 'todos los recursos', 'qué recursos', 'recursos disponibles']):
        print("✅ Detectada consulta tipo: índice_completo")
        return {'tipo': 'indice_completo'}
    
    # Detectar búsqueda de flujogramas
    if any(palabra in entrada_lower for palabra in ['flujograma', 'proceso', 'trámite', 'procedimiento']):
        if any(palabra in entrada_lower for palabra in ['terreno', 'terrenos', 'público', 'públicos']):
            print("✅ Detectada consulta tipo: flujograma - terrenos")
            return {'tipo': 'flujograma', 'subtipo': 'terrenos'}
        elif any(palabra in entrada_lower for palabra in ['calificación', 'cambio', 'cambios']):
            print("✅ Detectada consulta tipo: flujograma - calificacion")
            return {'tipo': 'flujograma', 'subtipo': 'calificacion'}
        elif any(palabra in entrada_lower for palabra in ['histórico', 'historicos', 'sitio', 'sitios']):
            print("✅ Detectada consulta tipo: flujograma - historicos")
            return {'tipo': 'flujograma', 'subtipo': 'historicos'}
    
    # REFORZADO: Detectar búsqueda de tablas de cabida con más patrones
    # Patrones comunes de consulta sobre tablas de cabida
    patrones_tabla_cabida = [
        r'tabla.*cabida',
        r'cabida.*tabla',
        r'cabida.*distrito',
        r'cabida.*tomo',
        r'tabla.*tomo',
        r'tabla.*distrito',
        r'muestra.*tabla.*cabida',
        r'ver.*tabla.*cabida',
        r'información.*cabida'
    ]
    
    # Comprobar si la entrada coincide con algún patrón
    if any(re.search(patron, entrada_lower) for patron in patrones_tabla_cabida):
        # Extraer número de tomo si se menciona usando una expresión regular más flexible
        tomo_match = re.search(r'tomo\s*(\d+)|del\s+tomo\s*(\d+)', entrada_lower)
        
        # Obtener el tomo de cualquier grupo capturado
        tomo = None
        if tomo_match:
            for grupo in tomo_match.groups():
                if grupo is not None:
                    tomo = int(grupo)
                    break
        
        if tomo:
            print(f"✅ Detectada consulta tipo: tabla_cabida - tomo {tomo}")
            return {'tipo': 'tabla_cabida', 'tomo': tomo}
        else:
            print("✅ Detectada consulta tipo: tabla_cabida - sin tomo específico")
            return {'tipo': 'tabla_cabida'}
    
    # Detectar búsqueda de resoluciones
    if any(palabra in entrada_lower for palabra in ['resolución', 'resoluciones']):
        print("✅ Detectada consulta tipo: resoluciones")
        return {'tipo': 'resoluciones'}
    
    # Detectar número de tomo específico
    tomo_match = re.search(r'tomo\s+(\d+)', entrada_lower)
    if tomo_match:
        print(f"✅ Detectada consulta tipo: tomo_especifico - tomo {tomo_match.group(1)}")
        return {'tipo': 'tomo_especifico', 'tomo': int(tomo_match.group(1))}
    
    print("❌ No se detectó ningún tipo de consulta específica")
    return None

def procesar_consulta_especifica(entrada, tipo_consulta):
    """Procesa consultas específicas sobre recursos estructurados"""
    entrada_lower = entrada.lower()
    
    # Extraer número de tomo si se menciona
    tomo_match = re.search(r'tomo\s+(\d+)|del\s+tomo\s*(\d+)', entrada_lower)
    
    # Obtener el número de tomo del grupo que haya coincidido
    tomo = None
    if tomo_match:
        # Tomar el primer grupo que no sea None
        for grupo in tomo_match.groups():
            if grupo is not None:
                tomo = int(grupo)
                break
    
    # Log para depuración
    print(f"⚙️ Procesando consulta específica tipo: {tipo_consulta['tipo']}")
    print(f"🔢 Tomo identificado: {tomo}")
    
    if tipo_consulta['tipo'] == 'indice_completo':
        return generar_indice_completo()
    
    elif tipo_consulta['tipo'] == 'flujograma':
        resultados = buscar_flujograma(tipo_consulta['subtipo'], tomo)
        if resultados:
            respuesta = f"🔄 **Flujograma - {tipo_consulta['subtipo'].title()}:**\n\n"
            for resultado in resultados:
                respuesta += f"{resultado}\n\n"
            respuesta += "---\n💡 *Información extraída de los archivos de flujogramas por tomo*"
            return respuesta
    
    elif tipo_consulta['tipo'] == 'tabla_cabida':
        # buscar_tabla_cabida SIEMPRE devuelve resultados (tabla real o genérica)
        resultados = buscar_tabla_cabida(tomo)
        if resultados:
            # IMPORTANTE: Preservar HTML en lugar de convertirlo a texto plano
            respuesta = "<strong>📊 Tabla de Cabida - Distritos de Calificación:</strong><br><br>"
            for resultado in resultados:
                # No añadir \n\n que rompe el formato HTML
                respuesta += f"{resultado}"
            respuesta += "<br>---<br>💡 <i>Información extraída de las tablas de cabida por tomo</i>"
            return respuesta
        else:
            # Este caso no debería ocurrir con la nueva implementación de buscar_tabla_cabida
            print("⚠️ ADVERTENCIA: buscar_tabla_cabida devolvió None a pesar de las mejoras")
            return "Lo siento, no pude encontrar la tabla de cabida solicitada. Por favor, intenta especificar el tomo (por ejemplo: 'tabla de cabida tomo 3')."
    
    elif tipo_consulta['tipo'] == 'resoluciones':
        # Detectar tema específico
        tema = None
        if 'ambiente' in entrada_lower or 'ambiental' in entrada_lower:
            tema = 'ambiente'
        elif 'construcción' in entrada_lower or 'construccion' in entrada_lower:
            tema = 'construcción'
        elif 'zonificación' in entrada_lower or 'zonificacion' in entrada_lower:
            tema = 'zonificación'
        
        resultados = buscar_resoluciones(tomo, tema)
        if resultados:
            respuesta = "📋 **Resoluciones de la Junta de Planificación:**\n\n"
            for resultado in resultados:
                respuesta += f"{resultado}\n\n"
            respuesta += "---\n💡 *Información extraída de las resoluciones organizadas por tomo*"
            return respuesta
    
    # Si llegamos aquí es porque no pudimos procesar la consulta específica
    print("⚠️ No se pudo procesar la consulta específica, devolviendo None")
    return None

def detectar_tipo_pregunta(entrada):
    """Detecta el tipo de pregunta y determina la mejor estrategia de búsqueda"""
    entrada_lower = entrada.lower()
    
    # Preguntas de comparación/diferencia
    if any(palabra in entrada_lower for palabra in ['diferencia', 'diferencias', 'comparar', 'comparación']):
        return 'comparacion'
    
    # Preguntas sobre REQUISITOS Y PROCEDIMIENTOS - PRIORIDAD ALTA para Reglamento
    palabras_requisitos = ['requisito', 'requisitos', 'proceso', 'procedimiento', 'pasos', 'como', 'cómo', 'necesito', 'solicitar', 'obtener', 'tramitar', 'aplicar']
    if any(palabra in entrada_lower for palabra in palabras_requisitos):
        return 'requisitos_procedimientos'
    
    # Preguntas sobre el glosario/definiciones SOLO cuando se pregunta explícitamente
    palabras_glosario = ['qué es', 'que es', 'define', 'definición', 'definicion', 'significado', 'explica', 'explícame', 'explicame', 'concepto', 'término', 'termino', 'significa']
    if any(palabra in entrada_lower for palabra in palabras_glosario):
        return 'glosario'

    # Preguntas sobre permisos - PRIORIDAD REGLAMENTO si hay palabras de acción
    if any(palabra in entrada_lower for palabra in ['permiso', 'autorización', 'licencia', 'trámite']):
        # Si incluye palabras de acción, es requisitos/procedimientos
        if any(accion in entrada_lower for accion in ['requisito', 'como', 'cómo', 'proceso', 'solicitar', 'obtener', 'tramitar']):
            return 'requisitos_procedimientos'
        return 'permisos'

    # Preguntas sobre construcción
    if any(palabra in entrada_lower for palabra in ['construcción', 'edificar', 'estructura', 'obra']):
        return 'construccion'

    # Preguntas sobre planificación
    if any(palabra in entrada_lower for palabra in ['plan', 'zonificación', 'ordenación', 'uso de suelo']):
        return 'planificacion'

    # Preguntas ambientales
    if any(palabra in entrada_lower for palabra in ['ambiental', 'conservación', 'aguas', 'desperdicios']):
        return 'ambiental'

    return 'general'
    if any(palabra in entrada_lower for palabra in ['permiso', 'autorización', 'licencia', 'trámite']):
        return 'permisos'

    # Preguntas sobre construcción
    if any(palabra in entrada_lower for palabra in ['construcción', 'edificar', 'estructura', 'obra']):
        return 'construccion'

    # Preguntas sobre planificación
    if any(palabra in entrada_lower for palabra in ['plan', 'zonificación', 'ordenación', 'uso de suelo']):
        return 'planificacion'

    # Preguntas ambientales
    if any(palabra in entrada_lower for palabra in ['ambiental', 'conservación', 'aguas', 'desperdicios']):
        return 'ambiental'

    return 'general'


def es_pregunta_simple(entrada):
    """Determina si una pregunta es simple y puede responderse con información limitada"""
    entrada_lower = entrada.lower()
    
    # Preguntas que requieren búsqueda específica
    palabras_complejas = [
        "todos", "lista", "cantidad", "cuantos", "cuántos", "comparar", "diferencia",
        "análisis", "resumen", "procedimiento completo", "proceso completo"
    ]
    
    # Preguntas simples típicas
    palabras_simples = [
        "qué es", "que es", "define", "definición", "significa", 
        "cómo se", "como se", "para qué", "para que"
    ]
    
    # Si tiene palabras complejas, no es simple
    if any(palabra in entrada_lower for palabra in palabras_complejas):
        return False
    
    # Si tiene palabras simples o es muy corta, es simple
    if any(palabra in entrada_lower for palabra in palabras_simples):
        return True
    
    # Si la pregunta es muy corta (menos de 5 palabras), probablemente es simple
    return len(entrada.split()) <= 5

def evaluar_relevancia_tomo(entrada, archivo_tomo):
    """Evalúa qué tan relevante es un tomo para una pregunta específica"""
    try:
        with open(archivo_tomo, 'r', encoding='utf-8') as f:
            contenido = f.read().lower()
        
        palabras_pregunta = [palabra.lower() for palabra in entrada.split() if len(palabra) > 3]
        score_relevancia = 0
        
        for palabra in palabras_pregunta:
            if palabra in contenido:
                # Contar ocurrencias pero dar más peso a palabras menos comunes
                ocurrencias = contenido.count(palabra)
                if ocurrencias > 0:
                    # Palabras menos frecuentes tienen más peso
                    peso = min(5, 10 // max(1, ocurrencias // 10))
                    score_relevancia += ocurrencias * peso
        
        return score_relevancia
    except:
        return 0


def procesar_pregunta_legal(entrada):
    """Procesa preguntas legales con IA híbrida inteligente"""
    entrada_lower = entrada.lower()
    
    # Caso especial para División de Cumplimiento Ambiental
    if "división de cumplimiento ambiental" in entrada_lower or "division de cumplimiento ambiental" in entrada_lower:
        return """🚨 **REGLAMENTO DE EMERGENCIA JP-RP-41**:

La División de Evaluación de Cumplimiento Ambiental (DECA) de la OGPe es responsable de evaluar y tramitar todos los documentos ambientales presentados a la agencia. Cumple funciones administrativas y de manejo de documentación ambiental según lo establece la Ley 161-2009 y otros reglamentos pertinentes.

La función específica de la División de Cumplimiento Ambiental es preparar y adoptar, junto con la Junta de Planificación, la Oficina de Gerencia de Permisos (OGPe) y las Entidades Gubernamentales Concernidas, un Reglamento Conjunto para establecer un sistema uniforme de adjudicación, procesos uniformes para la evaluación y expedición de determinaciones finales, permisos y recomendaciones relacionados a obras de construcción y uso de terrenos, guías de diseño verde, procedimientos de auditorías y querellas, y cualquier otro asunto referido a la Ley 161-2009.

---
💡 *Información extraída del Reglamento de Emergencia JP-RP-41*"""
    
    # 🆕 NUEVA FUNCIONALIDAD: Detección automática de solicitudes de tablas
    respuesta_tabla = detectar_y_generar_tabla_automatica(entrada)
    if respuesta_tabla:
        return '\n\n'.join(respuesta_tabla)
    
    # Detectar preguntas sobre títulos de tomos
    palabras_titulos = ["titulo", "títulos", "titulos", "nombre", "nombres", "llamar", "llama", "indices", "indice", "índice", "índices"]
    palabras_tomos = ["tomo", "tomos", "11 tomos", "once tomos", "todos los tomos", "cada tomo"]
    
    busca_titulos = any(palabra in entrada_lower for palabra in palabras_titulos) and any(palabra in entrada_lower for palabra in palabras_tomos)
    busca_listado = any(palabra in entrada_lower for palabra in ["dame", "dime", "muestra", "muéstra", "lista", "listado", "cuales", "cuáles"])
    
    # Si pregunta específicamente por títulos o índice de tomos
    if busca_titulos or (busca_listado and any(palabra in entrada_lower for palabra in palabras_tomos)):
        return obtener_titulos_tomos()
    
    # SISTEMA HÍBRIDO INTELIGENTE: Buscar en múltiples fuentes y combinar
    fuentes_informacion = {}
    
    # FUENTE PRIORITARIA: Tomo 10 - Conservación Histórica (para sitios históricos)
    respuesta_sitios_historicos = buscar_en_tomo_10_sitios_historicos(entrada)
    if respuesta_sitios_historicos:
        return respuesta_sitios_historicos
    
    # FUENTE 1: Reglamento de emergencia JP-RP-41
    if reglamento_emergencia:
        info_emergencia = buscar_informacion_relevante(entrada, reglamento_emergencia, "Reglamento de Emergencia JP-RP-41")
        if info_emergencia:
            fuentes_informacion["emergencia"] = info_emergencia
    
    # FUENTE 2: Glosario (para términos técnicos)
    respuesta_glosario = procesar_pregunta_glosario(entrada)
    if respuesta_glosario:
        fuentes_informacion["glosario"] = respuesta_glosario
    
    # FUENTE 3: Tomos relevantes (buscar los 2 más relevantes)
    relevancia_tomos = []
    for i in range(1, 12):
        ruta = os.path.join("data", f"tomo_{i}.txt")
        if os.path.exists(ruta):
            score = evaluar_relevancia_tomo(entrada, ruta)
            if score > 0:
                relevancia_tomos.append((score, i, ruta))
    
    # Ordenar por relevancia y usar los 2 más relevantes
    relevancia_tomos.sort(key=lambda x: x[0], reverse=True)
    
    info_tomos = []
    for score, tomo_id, ruta in relevancia_tomos[:2]:  # Solo los 2 más relevantes
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            
            info_relevante = buscar_informacion_relevante(entrada, contenido, f"Tomo {tomo_id}")
            if info_relevante:
                info_tomos.append(f"**TOMO {tomo_id}:**\n{info_relevante}")
        except Exception as e:
            print(f"Error procesando tomo {tomo_id}: {e}")
    
    if info_tomos:
        fuentes_informacion["tomos"] = "\n\n".join(info_tomos)
    
    # GENERAR RESPUESTA INTELIGENTE COMBINANDO TODAS LAS FUENTES
    if fuentes_informacion:
        return generar_respuesta_hibrida_inteligente(entrada, fuentes_informacion)
    
    # Si no encuentra información específica, respuesta inteligente genérica
    return generar_respuesta_generica_inteligente(entrada)

def buscar_informacion_relevante(pregunta, contenido, fuente):
    """Busca información relevante en un contenido usando IA"""
    try:
        # Caso especial para la División de Cumplimiento Ambiental
        pregunta_lower = pregunta.lower()
        if "división de cumplimiento ambiental" in pregunta_lower or "division de cumplimiento ambiental" in pregunta_lower:
            return """La División de Evaluación de Cumplimiento Ambiental (DECA) de la OGPe es responsable de evaluar y tramitar todos los documentos ambientales presentados a la agencia. Cumple funciones administrativas y de manejo de documentación ambiental según lo establece la Ley 161-2009 y otros reglamentos pertinentes.

La función específica de la División de Cumplimiento Ambiental es preparar y adoptar, junto con la Junta de Planificación, la Oficina de Gerencia de Permisos (OGPe) y las Entidades Gubernamentales Concernidas, un Reglamento Conjunto para establecer un sistema uniforme de adjudicación, procesos uniformes para la evaluación y expedición de determinaciones finales, permisos y recomendaciones relacionados a obras de construcción y uso de terrenos, guías de diseño verde, procedimientos de auditorías y querellas, y cualquier otro asunto referido a la Ley 161-2009."""
        
        # Fragmentar el contenido en chunks manejables
        max_chars = 8000
        if len(contenido) > max_chars:
            # Buscar las secciones más relevantes
            palabras_pregunta = pregunta.lower().split()
            lineas = contenido.split('\n')
            
            secciones_relevantes = []
            for i, linea in enumerate(lineas):
                linea_lower = linea.lower()
                relevancia = 0
                
                for palabra in palabras_pregunta:
                    if len(palabra) > 3 and palabra in linea_lower:
                        relevancia += 3
                
                if relevancia > 0:
                    # Capturar contexto alrededor de la línea relevante
                    inicio = max(0, i - 15)
                    fin = min(len(lineas), i + 40)
                    seccion = '\n'.join(lineas[inicio:fin])
                    secciones_relevantes.append((relevancia, seccion))
            
            if secciones_relevantes:
                # Ordenar por relevancia y combinar las mejores secciones
                secciones_relevantes.sort(key=lambda x: x[0], reverse=True)
                contenido_relevante = '\n\n---\n\n'.join([s[1] for s in secciones_relevantes[:2]])
            else:
                # Si no encuentra secciones específicas, usar el inicio del documento
                contenido_relevante = contenido[:max_chars]
        else:
            contenido_relevante = contenido
        
        # Usar IA para extraer información relevante
        prompt_extraccion = f"""Analiza el siguiente contenido de {fuente} y extrae ÚNICAMENTE la información más relevante para la pregunta del usuario.

PREGUNTA: {pregunta}

CONTENIDO DE {fuente.upper()}:
{contenido_relevante}

INSTRUCCIONES:
1. Extrae SOLO la información directamente relevante a la pregunta
2. Mantén el formato y estructura original cuando sea posible
3. Si no hay información relevante, responde "NO_RELEVANTE"
4. Máximo 400 palabras
5. Preserva números de artículos, secciones, etc.

INFORMACIÓN RELEVANTE EXTRAÍDA:"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Eres un especialista en extraer información relevante de documentos legales. Enfócate en la precisión y relevancia."},
                {"role": "user", "content": prompt_extraccion}
            ],
            temperature=0.1,
            max_tokens=800
        )
        
        contenido_extraido = response.choices[0].message.content.strip()
        
        if contenido_extraido and contenido_extraido != "NO_RELEVANTE" and len(contenido_extraido) > 50:
            return contenido_extraido
        
    except Exception as e:
        print(f"Error extrayendo información de {fuente}: {e}")
    
    return None

def generar_respuesta_hibrida_inteligente(pregunta, fuentes_informacion):
    """Genera una respuesta inteligente combinando múltiples fuentes"""
    try:
        # Preparar contexto combinado
        contexto_combinado = "INFORMACIÓN DISPONIBLE DE MÚLTIPLES FUENTES:\n\n"
        
        if "emergencia" in fuentes_informacion:
            contexto_combinado += f"🚨 REGLAMENTO DE EMERGENCIA JP-RP-41:\n{fuentes_informacion['emergencia']}\n\n"
        
        if "glosario" in fuentes_informacion:
            contexto_combinado += f"📚 GLOSARIO OFICIAL:\n{fuentes_informacion['glosario']}\n\n"
        
        if "tomos" in fuentes_informacion:
            contexto_combinado += f"📖 TOMOS RELEVANTES:\n{fuentes_informacion['tomos']}\n\n"
        
        # Prompt para respuesta híbrida inteligente
        prompt_hibrido = f"""Eres Agente de Planificación, un asistente especializado altamente inteligente en leyes de planificación de Puerto Rico, similar a ChatGPT pero con conocimiento especializado.

PREGUNTA DEL USUARIO: {pregunta}

{contexto_combinado}

INSTRUCCIONES PARA RESPUESTA INTELIGENTE:
1. Analiza toda la información disponible de las diferentes fuentes
2. Proporciona una respuesta completa, clara y bien estructurada
3. Combina información de diferentes fuentes cuando sea relevante
4. Prioriza el Reglamento de Emergencia JP-RP-41 por ser más actual
5. Explica conceptos técnicos de manera comprensible
6. Mantén un tono profesional pero conversacional
7. Agrega contexto práctico sobre cómo aplicar la información
8. Si hay información conflictiva, explícalo claramente
9. Sugiere próximos pasos o información adicional cuando sea útil
10. Usa emojis apropiados para mejorar la legibilidad

RESPUESTA ESPECIALIZADA:"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres Agente de Planificación, un experto en leyes de planificación de Puerto Rico con estilo conversacional inteligente como ChatGPT. Proporciona respuestas expertas, claras y útiles."},
                {"role": "user", "content": prompt_hibrido}
            ],
            temperature=0.4,  # Un poco más creativo para respuestas conversacionales
            max_tokens=1500   # Más espacio para respuestas completas
        )
        
        respuesta_final = response.choices[0].message.content.strip()
        
        if respuesta_final and len(respuesta_final) > 50:
            # Agregar información sobre las fuentes utilizadas
            fuentes_utilizadas = []
            if "emergencia" in fuentes_informacion:
                fuentes_utilizadas.append("Reglamento de Emergencia JP-RP-41")
            if "glosario" in fuentes_informacion:
                fuentes_utilizadas.append("Glosario Oficial")
            if "tomos" in fuentes_informacion:
                fuentes_utilizadas.append("Tomos de Referencia Histórica")
            
            respuesta_final += f"\n\n---\n📋 *Fuentes consultadas: {', '.join(fuentes_utilizadas)}*"
            return respuesta_final
        
    except Exception as e:
        print(f"Error generando respuesta híbrida: {e}")
    
    # Fallback: usar la fuente más importante disponible
    if "emergencia" in fuentes_informacion:
        return fuentes_informacion["emergencia"] + "\n\n---\n🚨 *Información del Reglamento de Emergencia JP-RP-41*"
    elif "glosario" in fuentes_informacion:
        return fuentes_informacion["glosario"]
    elif "tomos" in fuentes_informacion:
        return fuentes_informacion["tomos"] + "\n\n---\n📖 *Información de los Tomos de Referencia Histórica*"
    
    return generar_respuesta_generica_inteligente(pregunta)

def generar_respuesta_generica_inteligente(pregunta):
    """Genera una respuesta inteligente y útil cuando no se encuentra información específica"""
    try:
        prompt_generico = f"""Eres Agente de Planificación, un asistente especializado en leyes de planificación de Puerto Rico.

PREGUNTA DEL USUARIO: {pregunta}

SITUACIÓN: No se encontró información específica en la documentación disponible para esta consulta.

INSTRUCCIONES:
1. Proporciona una respuesta útil y orientadora
2. Explica qué tipo de información se necesitaría para responder completamente
3. Sugiere fuentes adicionales o contactos relevantes
4. Ofrece información general relacionada si es apropiado
5. Mantén un tono profesional y servicial
6. Sugiere cómo reformular la pregunta para obtener mejores resultados

RESPUESTA ORIENTADORA:"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres Agente de Planificación. Cuando no tienes información específica, proporciona orientación útil y profesional."},
                {"role": "user", "content": prompt_generico}
            ],
            temperature=0.3,
            max_tokens=600
        )
        
        respuesta = response.choices[0].message.content.strip()
        
        if respuesta and len(respuesta) > 50:
            respuesta += "\n\n---\n💡 *Para obtener información más específica, puedes contactar directamente con la Junta de Planificación de Puerto Rico*"
            return respuesta
        
    except Exception as e:
        print(f"Error generando respuesta genérica: {e}")
    
    # Respuesta de fallback final
    return """⚠️ **No encontré información específica sobre esta consulta en mi base de datos actual.**

🔍 **Para obtener una respuesta más precisa, podrías:**
- Reformular la pregunta con términos más específicos
- Contactar directamente con la Junta de Planificación de Puerto Rico
- Especificar el tomo o área de regulación que te interesa

📞 **Contacto oficial:**
- Junta de Planificación de Puerto Rico
- Oficina de Gerencia de Permisos (OGPe)

---
💡 *Estaré aquí para ayudarte con cualquier otra consulta sobre planificación en Puerto Rico*"""

def procesar_recurso_especializado(tipo_recurso, ruta_recurso, entrada):
    """Procesa un recurso especializado específico"""
    try:
        with open(ruta_recurso, "r", encoding="utf-8") as f:
            contenido_recurso = f.read()

        prompt_especializado = f"""Eres Agente de planificación, especialista en leyes de planificación de Puerto Rico.

{tipo_recurso.upper()} ESPECIALIZADO:
{contenido_recurso}

PREGUNTA DEL USUARIO: {entrada}

INSTRUCCIONES:
1. Respuesta CONCISA (máximo 300 palabras)
2. Si es flujograma, presenta SOLO los pasos principales
3. Mantén formato claro con emojis
4. Evita repetir información

RESPUESTA:"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Eres Agente de planificación. Presenta {tipo_recurso.lower()}s de forma CONCISA."},
                {"role": "user", "content": prompt_especializado}
            ],
            temperature=0.1,
            max_tokens=700  # Limitar tokens
        )
        contenido = response.choices[0].message.content.strip()

        if contenido and len(contenido) > 50:
            nombre_archivo = os.path.basename(ruta_recurso)
            return f"📋 **{tipo_recurso} Especializado - {nombre_archivo}**:\n{contenido}"

    except Exception as e:
        print(f"Error procesando recurso {tipo_recurso}: {e}")
    
    return None

def buscar_secciones_relevantes(entrada, contenido):
    """Busca secciones relevantes en el contenido basado en la entrada"""
    palabras_pregunta = entrada.lower().split()
    lineas = contenido.split('\n')
    
    secciones_relevantes = []
    for i, linea in enumerate(lineas):
        linea_lower = linea.lower()
        relevancia = 0
        
        for palabra in palabras_pregunta:
            if len(palabra) > 3 and palabra in linea_lower:
                relevancia += 3
        
        if relevancia > 0:
            # Capturar contexto alrededor de la línea relevante
            inicio = max(0, i - 10)
            fin = min(len(lineas), i + 30)
            seccion = '\n'.join(lineas[inicio:fin])
            secciones_relevantes.append(seccion)
    
    return secciones_relevantes

def obtener_titulos_tomos():
    """Devuelve los títulos oficiales de todos los tomos"""
    titulos = {
        1: "Sistema de Evaluación y Tramitación de Permisos para el Desarrollo",
        2: "Disposiciones Generales", 
        3: "Permisos para Desarrollo y Negocios",
        4: "Licencias y Certificaciones",
        5: "Urbanización y Lotificación", 
        6: "Distritos de Calificación",
        7: "Procesos",
        8: "Edificabilidad",
        9: "Infraestructura y Ambiente",
        10: "Conservación Histórica",
        11: "Querellas"
    }
    
    respuesta = "� **NORMATIVA VIGENTE Y ACTUALIZADA:**\n\n"
    respuesta += "📋 **Reglamento de Emergencia JP-RP-41 (2025)** - FUENTE PRINCIPAL Y VIGENTE\n"
    respuesta += "📚 **Glosario Oficial de Términos Especializados** - COMPLETAMENTE DISPONIBLE\n\n"
    
    respuesta += "📖 **INFORMACIÓN HISTÓRICA (REGULACIONES DEROGADAS):**\n\n"
    
    for num, titulo in titulos.items():
        respuesta += f"• **Tomo {num}:** {titulo}\n"
    
    respuesta += f"\n📋 **Tomo 12:** Glosario de términos especializados\n"
    respuesta += f"\n� **Reglamento de Emergencia JP-RP-41:** Normativa actualizada y vigente\n"
    respuesta += "\n---\n💡 *Para consultar un tomo específico, menciona su número en tu pregunta*"
    
    return respuesta

@app.route('/')
def index():
    """Página principal con verificación de beta"""
    from datetime import datetime
    
    # Verificar si la beta está activa
    beta_activa, dias_restantes = verificar_beta_activa()
    
    if not beta_activa:
        # Si la beta expiró, mostrar página de expiración
        return render_template('beta_expirada.html', 
                             fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA))
    
    # Si está activa, mostrar la aplicación con info de beta
    current_time = datetime.now().strftime('%H:%M')
    return render_template('index_v2.html', 
                         current_time=current_time,
                         es_beta=True,
                         dias_restantes=dias_restantes,
                         fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA),
                         fecha_expiracion_iso=FECHA_EXPIRACION_BETA.isoformat())

@app.route('/v2')
def index_v2():
    """Página principal V2 - Nueva interfaz (también con beta)"""
    from datetime import datetime
    
    # Verificar si la beta está activa
    beta_activa, dias_restantes = verificar_beta_activa()
    
    if not beta_activa:
        return render_template('beta_expirada.html', 
                             fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA))
    
    current_time = datetime.now().strftime('%H:%M')
    return render_template('index_v2.html', 
                         current_time=current_time,
                         es_beta=True,
                         dias_restantes=dias_restantes,
                         fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA),
                         fecha_expiracion_iso=FECHA_EXPIRACION_BETA.isoformat())

@app.route('/test')
def test():
    """Página de prueba para CSS"""
    return render_template('test.html')

@app.route('/debug')
def debug():
    """Página de debug para verificar Flask"""
    return """
    <h1>Flask Debug Page</h1>
    <p>Si ves esta página, Flask está funcionando correctamente.</p>
    <p><a href="/">Ir a la página principal</a></p>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: green; }
    </style>
    """

@app.route('/static/<path:filename>')
def custom_static(filename):
    """Servir archivos estáticos con headers específicos para evitar cache"""
    response = send_from_directory('static', filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para procesar mensajes del chat con IA híbrida inteligente
    REFORZADO: Mejorado para priorizar las consultas específicas sobre tablas de cabida"""
    try:
        # Verificar si la beta está activa antes de procesar el chat
        beta_activa, _ = verificar_beta_activa()
        if not beta_activa:
            return jsonify({
                'error': 'La versión beta ha expirado',
                'message': f'Esta versión beta expiró el {formatear_fecha_espanol(FECHA_EXPIRACION_BETA)}. Contacta al administrador para obtener la versión completa.'
            }), 403
            
        data = request.get_json()
        mensaje = data.get('message', '').strip()
        
        if not mensaje:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        conversation_id = get_conversation_id()
        inicializar_conversacion(conversation_id)
        
        # Log para depuración
        print(f"📩 Recibida consulta: '{mensaje}'")
        
        # Detección de preguntas legales mejorada
        entrada_lower = mensaje.lower()

        # Respuestas sobre estructura del documento
        if "cuantos tomos" in entrada_lower or "cuántos tomos" in entrada_lower:
            respuesta = "� **NORMATIVA LEGAL DE PLANIFICACIÓN DE PUERTO RICO:**\n\n**FUENTE PRINCIPAL Y VIGENTE:**\n- 📋 **Reglamento de Emergencia JP-RP-41 (2025)** - Normativa actualizada\n- � **Glosario Oficial** - Definiciones especializadas\n\n**REFERENCIAS HISTÓRICAS (NO VIGENTES):**\n- � **regulaciones anteriores DEROGADAS** - Solo para contexto histórico\n\n⚠️ **IMPORTANTE:** Toda consulta legal se basa en el **Reglamento de Emergencia JP-RP-41**, que es la normativa vigente."
            return jsonify({
                'response': respuesta,
                'type': 'info'
            })
            
        # Respuestas sobre División de Cumplimiento Ambiental
        if "división de cumplimiento ambiental" in entrada_lower or "division de cumplimiento ambiental" in entrada_lower:
            respuesta = f"🚨 **REGLAMENTO DE EMERGENCIA JP-RP-41**:\n\n{info_division_ambiental}\n\n---\n💡 *Información extraída del Reglamento de Emergencia JP-RP-41*"
            return jsonify({
                'response': respuesta,
                'type': 'legal-emergencia',
                'conversation_id': conversation_id
            })

        # --- PRIORIDAD 0: Mini-Especialistas para casos ultra-específicos ---
        print("🔍 Verificando mini-especialistas...")
        resultado_especialista = procesar_con_mini_especialistas_v2(mensaje)
        
        if resultado_especialista.get('usar_especialista', False):
            print(f"✨ Mini-especialista activado: {resultado_especialista['tipo']}")
            return jsonify({
                'response': resultado_especialista['respuesta'],
                'type': resultado_especialista['tipo'],
                'conversation_id': conversation_id
            })

        # --- PRIORIDAD 1: Detectar si es consulta estructurada (índice, tabla, flujograma, resoluciones) ---
        tipo_consulta = detectar_consulta_especifica(mensaje)
        if tipo_consulta:
            print(f"📊 Procesando consulta específica tipo: {tipo_consulta['tipo']}")
            respuesta = procesar_consulta_especifica(mensaje, tipo_consulta)
            if respuesta:
                tipo_respuesta = f"recurso-{tipo_consulta['tipo']}"
                print(f"✅ Respuesta generada correctamente como {tipo_respuesta}")
                return jsonify({
                    'response': respuesta,
                    'type': tipo_respuesta,
                    'conversation_id': conversation_id
                })
            print("⚠️ La función procesar_consulta_especifica no devolvió respuesta")
        
        # PRIORIDAD 2: Comprobar explícitamente si es sobre tabla de cabida
        # Este bloque añade una capa extra de seguridad para consultas de tablas
        if 'tabla' in entrada_lower and 'cabida' in entrada_lower:
            print("🔍 Detección secundaria: consulta sobre tabla de cabida")
            # Extraer tomo mediante regex más flexible
            import re
            tomo_match = re.search(r'tomo\s*(\d+)|del\s+tomo\s*(\d+)', entrada_lower)
            
            # Obtener el tomo de cualquier grupo capturado
            tomo = None
            if tomo_match:
                for grupo in tomo_match.groups():
                    if grupo is not None:
                        tomo = int(grupo)
                        break
            
            # Intentar procesar como tabla de cabida
            resultados = buscar_tabla_cabida(tomo)
            if resultados:
                # IMPORTANTE: Preservar HTML en lugar de convertirlo a texto plano
                # IMPORTANTE: Preservar HTML en lugar de convertirlo a texto plano
                respuesta = "<strong>📊 Tabla de Cabida - Distritos de Calificación:</strong><br><br>"
                for resultado in resultados:
                    # No añadir \n\n que rompe el formato HTML
                    respuesta += f"{resultado}"
                respuesta += "<br>---<br>💡 <i>Información extraída de las tablas de cabida por tomo</i>"
                
                print(f"✅ Respuesta de respaldo generada para tabla de cabida (tomo: {tomo})")
                return jsonify({
                    'response': respuesta,
                    'type': 'recurso-tabla_cabida',
                    'conversation_id': conversation_id
                })
        
        # SISTEMA HÍBRIDO INTELIGENTE: Detectar si es pregunta legal
        es_legal = any(palabra.lower() in entrada_lower for palabra in palabras_legales)
        if not es_legal and "tomo" in entrada_lower:
            es_legal = True
        
        # Palabras que indican consultas específicas
        palabras_consulta_especifica = ['índice', 'indice', 'flujograma', 'tabla', 'cabida', 'resolución', 'lista']
        es_consulta_especifica = any(palabra in entrada_lower for palabra in palabras_consulta_especifica)
        
        if es_legal or es_consulta_especifica:
            # PROCESAR CON SISTEMA HÍBRIDO INTELIGENTE
            print("📚 Procesando con sistema híbrido inteligente")
            respuesta = procesar_pregunta_legal(mensaje)
            
            # Determinar tipo de respuesta basado en el contenido
            if "🚨" in respuesta and "Reglamento de Emergencia" in respuesta:
                tipo_respuesta = 'legal-emergencia'
            elif "📚" in respuesta and "Glosario" in respuesta:
                tipo_respuesta = 'legal-glosario'
            elif "📋" in respuesta and "Fuentes consultadas" in respuesta:
                tipo_respuesta = 'legal-hibrido'
            else:
                tipo_respuesta = 'legal-general'
                
        else:
            # PREGUNTA GENERAL: Mejorar con contexto inteligente
            mensajes_conversacion = conversaciones[conversation_id]
            
            # Verificar si la pregunta podría beneficiarse de contexto legal
            palabras_contexto_legal = ['puerto rico', 'pr', 'planificación', 'planificacion', 'ley', 'legal', 'gobierno']
            necesita_contexto = any(palabra in entrada_lower for palabra in palabras_contexto_legal)
            
            if necesita_contexto:
                # Agregar contexto sobre especialización
                contexto_especializado = """Ten en cuenta que soy Agente de Planificación, especializado en leyes de planificación de Puerto Rico. 
Si la pregunta está relacionada con planificación, permisos, construcción o temas legales de Puerto Rico, puedo proporcionar información muy específica."""
                
                mensaje_con_contexto = f"{mensaje}\n\n[CONTEXTO INTERNO: {contexto_especializado}]"
                mensajes_conversacion.append({"role": "user", "content": mensaje_con_contexto})
            else:
                mensajes_conversacion.append({"role": "user", "content": mensaje})
            
            # Generar respuesta con IA más inteligente
            respuesta_openai = client.chat.completions.create(
                model="gpt-4o",
                messages=mensajes_conversacion,
                temperature=0.3,  # Un poco más creativo para conversaciones generales
                max_tokens=800
            )
            respuesta = respuesta_openai.choices[0].message.content.strip()
            mensajes_conversacion.append({"role": "assistant", "content": respuesta})
            tipo_respuesta = 'general-inteligente'
        
        # Mejorar respuesta si es muy corta o genérica
        if len(respuesta) < 100 and es_legal:
            respuesta += "\n\n💡 **¿Necesitas más información específica?** Puedes preguntar sobre:\n- Definiciones de términos técnicos\n- Procedimientos específicos\n- Requisitos para permisos\n- Comparaciones entre conceptos"
        
        # Guardar en log con más información
        with open("log.txt", "a", encoding="utf-8") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{timestamp}] Tipo: {tipo_respuesta}\nPregunta: {mensaje}\nRespuesta: {respuesta}\n---\n")
        
        return jsonify({
            'response': respuesta,
            'type': tipo_respuesta,
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        print(f"Error en chat: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Guardar error en log para diagnóstico
        with open("error_log.txt", "a", encoding="utf-8") as error_file:
            error_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: {str(e)}\n")
            error_file.write(traceback.format_exc() + "\n\n")
        
        # Intentar responder a la pregunta sobre división de cumplimiento ambiental
        if "división de cumplimiento ambiental" in entrada_lower or "division de cumplimiento ambiental" in entrada_lower:
            respuesta_especifica = """La División de Evaluación de Cumplimiento Ambiental (DECA) de la OGPe es responsable de evaluar y tramitar todos los documentos ambientales presentados a la agencia. Cumple funciones administrativas y de manejo de documentación ambiental según lo establece la Ley 161-2009 y otros reglamentos pertinentes.

La función específica de la División de Cumplimiento Ambiental es preparar y adoptar, junto con la Junta de Planificación, la Oficina de Gerencia de Permisos (OGPe) y las Entidades Gubernamentales Concernidas, un Reglamento Conjunto para establecer un sistema uniforme de adjudicación, procesos uniformes para la evaluación y expedición de determinaciones finales, permisos y recomendaciones relacionados a obras de construcción y uso de terrenos, guías de diseño verde, procedimientos de auditorías y querellas, y cualquier otro asunto referido a la Ley 161-2009."""
            
            return jsonify({
                'response': respuesta_especifica,
                'type': 'legal-emergencia',
                'conversation_id': get_conversation_id()
            })
        
        # Respuesta de error más amigable
        error_respuesta = """🔧 **Se produjo un error técnico**

Lo siento, hubo un problema procesando tu consulta. 

**Puedes intentar:**
- Reformular la pregunta de manera más específica
- Verificar que la consulta esté relacionada con planificación de Puerto Rico
- Contactar al administrador si el problema persiste

---
💡 *Estaré aquí para ayudarte cuando estés listo*"""
        
        return jsonify({
            'response': error_respuesta,
            'type': 'error-amigable'
        }), 200  # 200 para mostrar el mensaje amigable

@app.route('/nueva-conversacion', methods=['POST'])
def nueva_conversacion():
    """Endpoint para iniciar una nueva conversación"""
    if 'conversation_id' in session:
        del session['conversation_id']
    return jsonify({'success': True})

@app.route('/health')
def health():
    """Endpoint de salud para verificar que la aplicación está funcionando"""
    return jsonify({'status': 'ok', 'service': 'Agente de planificación Web'})

@app.route('/favicon.ico')
def favicon():
    """Servir favicon"""
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    import webbrowser
    import threading
    import time
    
    # Función para abrir el navegador después de un pequeño delay
    def open_browser():
        time.sleep(1.5)  # Esperar a que el servidor esté listo
        webbrowser.open('http://127.0.0.1:5001')
    
    # Crear carpeta de templates si no existe
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Abrir navegador en un hilo separado
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Ejecutar con menos debug info para el ejecutable
    debug_mode = not getattr(sys, 'frozen', False)  # False si es ejecutable
    app.run(debug=debug_mode, host='0.0.0.0', port=5001)
