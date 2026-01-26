# interpretador_stock.py
"""
Módulo dedicado exclusivamente a interpretar preguntas de stock
Versión mejorada con detección robusta de familias
"""
import re
import streamlit as st
from typing import Dict, Optional, List

# =====================================================================
# CARGA DINÁMICA DE FAMILIAS DESDE BD
# =====================================================================
@st.cache_data(ttl=60 * 60)
def _cargar_familias_stock() -> List[str]:
    """Carga las familias desde la tabla stock"""
    try:
        from sql_core import ejecutar_consulta
        
        query = """
        SELECT DISTINCT TRIM("FAMILIA") AS familia
        FROM public.stock
        WHERE "FAMILIA" IS NOT NULL
          AND TRIM("FAMILIA") <> ''
          AND UPPER(TRIM("FAMILIA")) <> 'SIN FAMILIA'
        ORDER BY familia
        """
        
        df = ejecutar_consulta(query, ())
        
        if df is not None and not df.empty and 'familia' in df.columns:
            familias = df['familia'].tolist()
            print(f"✅ Familias cargadas desde BD: {familias}")
            return familias
        
        print("⚠️ No se pudieron cargar familias de BD, usando fallback")
        return ["AF", "BE", "CM", "FB", "G", "HT", "ID", "MY", "TEST", "TR", "XX"]
    
    except Exception as e:
        print(f"❌ Error cargando familias: {e}")
        return ["AF", "BE", "CM", "FB", "G", "HT", "ID", "MY", "TEST", "TR", "XX"]


# =====================================================================
# FUNCIÓN PRINCIPAL
# =====================================================================
def interpretar_pregunta_stock(pregunta: str) -> Dict:
    """
    Interpreta preguntas relacionadas con stock.
    Retorna un diccionario con tipo y parámetros.
    """
    if not pregunta:
        return {"tipo": "no_entendido", "parametros": {}}
    
    pregunta_lower = pregunta.lower().strip()
    
    print(f"\n🔍 INTERPRETADOR STOCK")
    print(f"  Pregunta original: {pregunta}")
    print(f"  Pregunta lower: {pregunta_lower}")
    
    # 1. Detectar si es pregunta de stock
    palabras_clave = [
        "stock", "artículo", "articulo", "lote", "familia", 
        "depósito", "deposito", "vence", "vencimiento", "bajo", "crítico"
    ]
    es_pregunta_stock = any(palabra in pregunta_lower for palabra in palabras_clave)
    
    if not es_pregunta_stock:
        print("  ❌ No es pregunta de stock")
        return {"tipo": "no_stock", "parametros": {}}
    
    print("  ✅ Es pregunta de stock")
    
    # 2. Extraer parámetros
    params = extraer_parametros_stock(pregunta_lower)
    print(f"  Parámetros extraídos: {params}")
    
    # 3. Determinar tipo de consulta
    tipo = determinar_tipo_consulta(pregunta_lower, params)
    print(f"  Tipo determinado: {tipo}")
    
    return {
        "tipo": tipo,
        "parametros": params
    }


# =====================================================================
# EXTRACCIÓN DE PARÁMETROS
# =====================================================================
def extraer_parametros_stock(pregunta: str) -> Dict:
    """
    Extrae parámetros de la pregunta usando regex y búsqueda en BD
    """
    params = {}
    
    # ===== EXTRAER FAMILIA =====
    # Cargar familias desde BD
    familias = _cargar_familias_stock()
    
    # Normalizar pregunta
    pregunta_norm = pregunta.lower().strip()
    
    # Buscar cada familia en la pregunta
    for familia in familias:
        familia_lower = familia.lower()
        
        # Buscar como palabra completa
        patron = rf'\b{re.escape(familia_lower)}\b'
        if re.search(patron, pregunta_norm):
            params['familia'] = familia  # Guardar en mayúsculas original
            print(f"    ✅ Familia detectada: {familia}")
            break
    
    # ===== EXTRAER LOTE =====
    lote_match = re.search(r'lote\s+(\w+)', pregunta)
    if lote_match:
        params['lote'] = lote_match.group(1)
    
    # ===== EXTRAER DÍAS =====
    dias_match = re.search(r'(\d+)\s*(dias|día|dia)', pregunta)
    if dias_match:
        params['dias'] = int(dias_match.group(1))
    
    # ===== EXTRAER ARTÍCULO (FALLBACK) =====
    # Solo si no hay familia ni lote
    if not params.get('familia') and not params.get('lote'):
        palabras_excluir = {
            'stock', 'cuanto', 'cuánto', 'hay', 'de', 'del', 'tenemos', 
            'disponible', 'el', 'la', 'los', 'las', 'que', 'es', 'un', 
            'una', 'cual', 'cuál', 'familia', 'lote', 'por'
        }
        palabras = [p for p in pregunta.split() if p not in palabras_excluir and len(p) > 2]
        if palabras:
            params['articulo'] = ' '.join(palabras)
    
    return params


# =====================================================================
# DETERMINACIÓN DE TIPO
# =====================================================================
def determinar_tipo_consulta(pregunta: str, params: Dict) -> str:
    """
    Determina el tipo de consulta basado en la pregunta y parámetros
    """
    # 1. FAMILIA ESPECÍFICA (tiene prioridad)
    if params.get('familia'):
        return 'stock_familia'
    
    # 2. POR FAMILIA (RESUMEN)
    if 'por familia' in pregunta or 'por familias' in pregunta:
        return 'stock_por_familia_resumen'
    
    # 3. POR DEPÓSITO (RESUMEN)
    if 'por depósito' in pregunta or 'por deposito' in pregunta:
        return 'stock_por_deposito_resumen'
    
    # 4. LOTE ESPECÍFICO
    if params.get('lote'):
        return 'stock_lote'
    
    # 5. VENCIMIENTOS
    if 'vence' in pregunta or 'vencimiento' in pregunta:
        if 'ya venc' in pregunta or 'vencido' in pregunta:
            return 'vencidos'
        return 'vencimientos'
    
    # 6. STOCK BAJO
    if 'bajo' in pregunta or 'crítico' in pregunta or 'pedir' in pregunta:
        return 'stock_bajo'
    
    # 7. TOTAL
    if 'total' in pregunta and 'stock' in pregunta:
        return 'stock_total'
    
    # 8. ARTÍCULO
    if params.get('articulo'):
        return 'stock_articulo'
    
    # 9. FALLBACK
    return 'no_entendido'

