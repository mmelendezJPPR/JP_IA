"""
Script para verificar el estado de los tomos y hacer una limpieza si es necesario
"""

import os
import re
import sys
import shutil
from datetime import datetime

# Directorio base donde están los tomos
directorio_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def analizar_tomos():
    """
    Analiza los tomos existentes y muestra un informe detallado
    """
    print("\n====================================")
    print("ANÁLISIS DE TOMOS - INFORME DETALLADO")
    print("====================================")
    
    # Obtener listado de archivos
    archivos = os.listdir(directorio_base)
    
    # Clasificar archivos
    tomos_mejorados = []
    tomos_originales = []
    otros_archivos = []
    
    for archivo in archivos:
        if re.match(r"TOMO\d+_COMPLETO_MEJORADO_\d+_\d+\.txt", archivo):
            tomos_mejorados.append(archivo)
        elif re.match(r"tomo_\d+\.txt", archivo) or archivo == "glosario.txt" or archivo == "Tomo_10_Conservacion_Historica.txt":
            tomos_originales.append(archivo)
        elif os.path.isfile(os.path.join(directorio_base, archivo)) and archivo.endswith(".txt"):
            otros_archivos.append(archivo)
    
    # Ordenar las listas
    tomos_mejorados.sort()
    tomos_originales.sort()
    
    # Mostrar resultados
    print(f"\n1. TOMOS MEJORADOS ENCONTRADOS ({len(tomos_mejorados)}):")
    for i, tomo in enumerate(tomos_mejorados):
        tamano = os.path.getsize(os.path.join(directorio_base, tomo)) / 1024
        print(f"   {i+1}. {tomo} ({tamano:.1f} KB)")
    
    print(f"\n2. TOMOS ORIGINALES ENCONTRADOS ({len(tomos_originales)}):")
    for i, tomo in enumerate(tomos_originales):
        tamano = os.path.getsize(os.path.join(directorio_base, tomo)) / 1024
        print(f"   {i+1}. {tomo} ({tamano:.1f} KB)")
    
    if otros_archivos:
        print(f"\n3. OTROS ARCHIVOS TXT ({len(otros_archivos)}):")
        for i, archivo in enumerate(otros_archivos):
            tamano = os.path.getsize(os.path.join(directorio_base, archivo)) / 1024
            print(f"   {i+1}. {archivo} ({tamano:.1f} KB)")
    
    # Análisis de cobertura
    print("\n4. ANÁLISIS DE COBERTURA:")
    
    # Extraer números de tomos mejorados
    numeros_tomos_mejorados = []
    for tomo in tomos_mejorados:
        match = re.match(r"TOMO(\d+)_", tomo)
        if match:
            numeros_tomos_mejorados.append(int(match.group(1)))
    
    # Extraer números de tomos originales
    numeros_tomos_originales = []
    for tomo in tomos_originales:
        match = re.match(r"tomo_(\d+)\.txt", tomo)
        if match:
            numeros_tomos_originales.append(int(match.group(1)))
    
    # Tomos que tienen ambas versiones
    tomos_duplicados = sorted(list(set(numeros_tomos_mejorados) & set(numeros_tomos_originales)))
    
    # Tomos que solo tienen versión mejorada
    tomos_solo_mejorados = sorted(list(set(numeros_tomos_mejorados) - set(numeros_tomos_originales)))
    
    # Tomos que solo tienen versión original
    tomos_solo_originales = sorted(list(set(numeros_tomos_originales) - set(numeros_tomos_mejorados)))
    
    print(f"   - Tomos con ambas versiones: {tomos_duplicados}")
    print(f"   - Tomos solo con versión mejorada: {tomos_solo_mejorados}")
    print(f"   - Tomos solo con versión original: {tomos_solo_originales}")
    
    # Verificar si hay tomo 12 (glosario)
    tiene_glosario_mejorado = any("TOMO12_GLOSARIO" in tomo for tomo in tomos_mejorados)
    tiene_glosario_original = "glosario.txt" in tomos_originales
    
    print(f"   - Glosario mejorado: {'✅ Disponible' if tiene_glosario_mejorado else '❌ No disponible'}")
    print(f"   - Glosario original: {'✅ Disponible' if tiene_glosario_original else '❌ No disponible'}")
    
    # Recomendaciones
    print("\n5. RECOMENDACIONES:")
    
    if tomos_duplicados:
        print(f"   ⚠️ Se recomienda usar únicamente los tomos mejorados para los tomos: {tomos_duplicados}")
        
    if tomos_solo_originales:
        print(f"   ⚠️ Crear versiones mejoradas para los tomos: {tomos_solo_originales}")
    
    if tiene_glosario_mejorado and tiene_glosario_original:
        print("   ⚠️ Se recomienda usar únicamente el glosario mejorado")
    
    print("\nLa aplicación está configurada para usar primordialmente los tomos mejorados.")
    print("Los tomos originales solo se usarán si no existe una versión mejorada del mismo.")
    
    # Resumen final
    print("\n====================================")
    print("RESUMEN FINAL")
    print("====================================")
    print(f"✅ Tomos mejorados: {len(tomos_mejorados)}")
    print(f"ℹ️ Tomos originales: {len(tomos_originales)}")
    if otros_archivos:
        print(f"ℹ️ Otros archivos: {len(otros_archivos)}")
    print(f"📊 Cobertura: {len(numeros_tomos_mejorados)} de 12 tomos tienen versión mejorada")
    
    return tomos_mejorados, tomos_originales, otros_archivos

def crear_carpeta_backup():
    """
    Crea una carpeta de backup para los archivos originales
    """
    fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta_backup = os.path.join(directorio_base, f"tomos_originales_backup_{fecha_actual}")
    
    if not os.path.exists(carpeta_backup):
        os.makedirs(carpeta_backup)
        print(f"\nCarpeta de backup creada: {carpeta_backup}")
    
    return carpeta_backup

def mover_tomos_originales(tomos_originales, carpeta_backup):
    """
    Mueve los tomos originales a la carpeta de backup
    """
    print("\nMoviendo tomos originales a la carpeta de backup...")
    
    for tomo in tomos_originales:
        ruta_origen = os.path.join(directorio_base, tomo)
        ruta_destino = os.path.join(carpeta_backup, tomo)
        
        try:
            shutil.move(ruta_origen, ruta_destino)
            print(f"   ✅ Movido: {tomo}")
        except Exception as e:
            print(f"   ❌ Error moviendo {tomo}: {e}")
    
    print("\nOperación completada.")

if __name__ == "__main__":
    print("============================================")
    print("ANÁLISIS Y LIMPIEZA DE TOMOS")
    print("============================================")
    print("Este script analiza los tomos existentes y permite realizar una limpieza")
    
    tomos_mejorados, tomos_originales, otros_archivos = analizar_tomos()
    
    if tomos_originales:
        respuesta = input("\n¿Desea mover los tomos originales a una carpeta de backup? (s/n): ")
        
        if respuesta.lower() == 's':
            carpeta_backup = crear_carpeta_backup()
            mover_tomos_originales(tomos_originales, carpeta_backup)
            print(f"\n✅ Tomos originales movidos a: {carpeta_backup}")
            print("La aplicación ahora usará exclusivamente los tomos mejorados disponibles.")
        else:
            print("\nOperación cancelada. Los tomos originales permanecen en su ubicación.")
    else:
        print("\nNo hay tomos originales para mover.")
