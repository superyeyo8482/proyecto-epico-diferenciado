import re
import json
import os
from datetime import datetime

# ====================================================
# CONFIGURACIÓN
# ====================================================

DOCUMENTO_PATH = "C:/Users/roble/OneDrive/Documentos/proyecto epico diferenciado/AnalizadorNoticias/texto_completo_ocr.txt"
RESULTADOS_DIR = "C:/Users/roble/OneDrive/Documentos/proyecto epico diferenciado/AnalizadorNoticias"

# ====================================================
# FUNCIONES
# ====================================================

def cargar_documento():
    with open(DOCUMENTO_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def extraer_titulares(texto):
    titulares = []
    lineas = texto.split('\n')
    
    for linea in lineas:
        linea = linea.strip()
        if len(linea) > 15 and len(linea) < 200:
            if not re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+$', linea):
                if not linea.startswith('--- Página'):
                    if not linea.startswith('E') or len(linea) > 5:
                        titulares.append(linea)
    
    return titulares

def identificar_periodicos(texto):
    periodicos = []
    patrones = [
        r'EL UNIVERSAL',
        r'MILENIO',
        r'La Jornada',
        r'EL ECONOMISTA',
        r'El Sol de México',
        r'CRÓNICA',
        r'EL HERALDO DE MÉXICO',
        r'ContraRéplica'
    ]
    
    for patron in patrones:
        if re.search(patron, texto, re.IGNORECASE):
            periodicos.append(patron)
    
    return periodicos

def analizar_calidad_ocr(texto):
    caracteres_extraños = re.findall(r'[^a-zA-ZáéíóúñÁÉÍÓÚÑüÜ0-9\s\.\,\;\"\'\¿\?\!\¡\(\)\-\:\/\n]', texto)
    total_caracteres = len(texto)
    porcentaje_error = (len(caracteres_extraños) / total_caracteres) * 100 if total_caracteres > 0 else 0
    
    if porcentaje_error < 2:
        calidad = "Excelente"
    elif porcentaje_error < 5:
        calidad = "Buena"
    elif porcentaje_error < 10:
        calidad = "Regular"
    else:
        calidad = "Mala"
    
    return {
        "calidad": calidad,
        "porcentaje_error": round(porcentaje_error, 2),
        "caracteres_extraños": caracteres_extraños[:50]
    }

def main():
    print("🔍 Verificando documento extraído...")
    texto = cargar_documento()
    
    paginas = re.findall(r'--- Página \d+ ---', texto)
    titulares = extraer_titulares(texto)
    periodicos = identificar_periodicos(texto)
    calidad = analizar_calidad_ocr(texto)
    
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   - Páginas: {len(paginas)}")
    print(f"   - Titulares detectados: {len(titulares)}")
    print(f"   - Periódicos identificados: {len(periodicos)}")
    print(f"   - Calidad OCR: {calidad['calidad']} ({calidad['porcentaje_error']}% de error)")
    
    print(f"\n📰 PERIÓDICOS IDENTIFICADOS:")
    for p in periodicos:
        print(f"   ✅ {p}")
    
    print(f"\n📋 TITULARES PRINCIPALES (primeros 15):")
    for i, t in enumerate(titulares[:15], 1):
        print(f"   {i}. {t}")
    
    resultados = {
        "fecha": datetime.now().isoformat(),
        "paginas": len(paginas),
        "titulares": len(titulares),
        "periodicos": periodicos,
        "calidad_ocr": calidad,
        "titulares_lista": titulares[:30]
    }
    
    resultados_path = os.path.join(RESULTADOS_DIR, "verificacion_documento.json")
    with open(resultados_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Resultados guardados en: {resultados_path}")

if __name__ == "__main__":
    main()
