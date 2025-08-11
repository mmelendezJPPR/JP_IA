"""
Módulo para cargar los tomos mejorados como fuente de información principal
"""

import os
import re
import sys

def cargar_tomo_mejorado(numero_tomo):
    """
    Carga el tomo mejorado según su número
    
    Args:
        numero_tomo (int): Número del tomo a cargar (1-12)
    
    Returns:
        str: Contenido del tomo mejorado o None si no se encuentra
    """
    # Directorio donde están los tomos mejorados
    directorio_datos = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    
    # Buscar primero el tomo mejorado
    patron_mejorado = f"TOMO{numero_tomo}_COMPLETO_MEJORADO_*.txt"
    
    # Caso especial para tomo 12 (glosario)
    if numero_tomo == 12:
        patron_mejorado = "TOMO12_GLOSARIO_COMPLETO_MEJORADO_*.txt"
    
    # Listar archivos en el directorio para encontrar coincidencias
    archivos = os.listdir(directorio_datos)
    archivo_mejorado = None
    
    # Buscar el archivo que coincida con el patrón
    for archivo in archivos:
        if re.match(f"TOMO{numero_tomo}_COMPLETO_MEJORADO_\\d+_\\d+.txt", archivo):
            archivo_mejorado = archivo
            break
        # Caso especial para el tomo 12 (glosario)
        elif numero_tomo == 12 and re.match("TOMO12_GLOSARIO_COMPLETO_MEJORADO_\\d+_\\d+.txt", archivo):
            archivo_mejorado = archivo
            break
    
    # Si encontramos el archivo mejorado, cargarlo
    if archivo_mejorado:
        ruta_archivo = os.path.join(directorio_datos, archivo_mejorado)
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
                print(f"✅ Tomo {numero_tomo} mejorado cargado: {len(contenido)} caracteres")
                return contenido
        except Exception as e:
            print(f"❌ Error cargando tomo {numero_tomo} mejorado: {e}")
    
    # Caso especial para el tomo 1 (que aún no tiene versión mejorada)
    if numero_tomo == 1:
        ruta_original = os.path.join(directorio_datos, f"tomo_{numero_tomo}.txt")
        try:
            if os.path.exists(ruta_original):
                with open(ruta_original, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    print(f"⚠️ Usando tomo 1 original como fallback: {len(contenido)} caracteres")
                    return contenido
        except Exception as e:
            print(f"❌ Error cargando tomo 1 original: {e}")
    
    # Para los demás tomos, no intentamos cargar el original
    print(f"❌ No se encontró el tomo {numero_tomo} mejorado")
    return None

def cargar_todos_los_tomos():
    """
    Carga todos los tomos mejorados disponibles (1-12, incluyendo glosario)
    VERSIÓN OPTIMIZADA: Solo utiliza tomos mejorados (versiones definitivas)
    
    Returns:
        dict: Diccionario con el contenido de cada tomo {numero: contenido}
    """
    tomos = {}
    
    # Mapeo de números de tomo a sus descripciones
    descripciones_tomos = {
        1: "Sistema de Evaluación y Tramitación de Permisos",
        2: "Disposiciones Generales",
        3: "Permisos para Desarrollo y Negocios",
        4: "Licencias y Certificaciones",
        5: "Urbanización y Lotificación",
        6: "Distritos de Calificación",
        7: "Procesos",
        8: "Edificabilidad",
        9: "Infraestructura y Ambiente",
        10: "Conservación Histórica",
        11: "Querellas",
        12: "Glosario de términos especializados"
    }
    
    # Cargar tomos 1-11
    for i in range(1, 12):
        contenido = cargar_tomo_mejorado(i)
        if contenido:
            tomos[i] = contenido
            print(f"✅ Tomo {i} cargado: {descripciones_tomos[i]} ({len(contenido)} caracteres)")
        else:
            print(f"❌ Tomo {i} no disponible: {descripciones_tomos[i]}")
    
    # Cargar tomo 12 (glosario)
    contenido_glosario = cargar_tomo_mejorado(12)
    if contenido_glosario:
        tomos[12] = contenido_glosario
        print(f"✅ Glosario (Tomo 12) cargado: {len(contenido_glosario)} caracteres")
    else:
        print("❌ Glosario (Tomo 12) no disponible")
    
    print(f"✅ Cargados {len(tomos)} tomos mejorados en total")
    return tomos
