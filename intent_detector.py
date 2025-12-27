# =========================
# INTENT DETECTOR - DETECCIÓN DE INTENCIONES (CORREGIDO)
# =========================
# CAMBIOS:
# 1. Agregado "comparame", "compara", "comparar" a todas las detecciones
# 2. Agregado "comparame" a las palabras a excluir del proveedor
# 3. Nueva lógica para detectar "comparar mes X año1 año2"
# 4. Mejor orden de prioridades

import re
import unicodedata
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


# =====================================================================
# NORMALIZACIÓN TEXTO
# =====================================================================

def normalizar_texto(texto: str) -> str:
    """Normaliza texto: minúsculas, sin acentos, sin espacios extras"""
    if texto is None:
        return ""
    s = str(texto)
    s = s.lower().strip()
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    s = ' '.join(s.split())
    return s

# =====================================================================
# DETECCIÓN ARTÍCULO vs PROVEEDOR (ARTÍCULO TIENE PRIORIDAD)
# =====================================================================

def detectar_articulo_o_proveedor(patron: str, lista_articulos: list, lista_proveedores: list) -> str | None:
    """
    Regla:
    - Si aparece en ARTICULOS → ARTICULO
    - Si NO aparece en ARTICULOS pero sí en PROVEEDORES → PROVEEDOR
    """

    if not patron:
        return None

    p = normalizar_texto(patron)

    # 1️⃣ ARTÍCULO (PRIORIDAD)
    for a in lista_articulos:
        if p in normalizar_texto(a):
            return "ARTICULO"

    # 2️⃣ PROVEEDOR
    for prov in lista_proveedores:
        if p in normalizar_texto(prov):
            return "PROVEEDOR"

    return None

# =====================================================================
# HELPERS DE EXTRACCIÓN
# =====================================================================

def es_conocimiento_general(pregunta: str) -> bool:
    txt = pregunta.lower().strip()
    patrones = [
        "que es", "qué es", "para que sirve", "para qué sirve",
        "qué significa", "que significa", "explica", "explicame",
    ]
    for p in patrones:
        if txt.startswith(p):
            return True
    return False


def extraer_meses(texto: str):
    """Detecta meses en texto y devuelve lista de mes_key 'YYYY-MM'"""
    if not texto:
        return []

    texto = texto.lower()

    meses = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
    }

    anio_match = re.search(r"(20\d{2})", texto)
    anio = anio_match.group(1) if anio_match else str(datetime.now().year)

    encontrados = []
    for nombre, num in meses.items():
        if nombre in texto:
            encontrados.append(f"{anio}-{num}")

    return encontrados


def _es_token_mes_o_periodo(tok: str) -> bool:
    """Detecta si un token es un mes o período temporal"""
    t = normalizar_texto(tok or "")

    meses = {
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
        'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    }
    if t in meses:
        return True

    if t in {'este', 'esta', 'mes', 'pasado', 'pasada', 'hoy', 'ayer', 'semana'}:
        return True

    if re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])', t):
        return True

    if re.fullmatch(r'20\d{2}', t):
        return True

    return False


def extraer_valores_multiples(texto: str, tipo: str) -> List[str]:
    """Extrae valores múltiples (proveedor/articulo/familia) del texto"""
    texto_norm = normalizar_texto(texto)

    patron = rf'{tipo}(?:es|s)?\s+([a-z0-9,\s\.\-]+?)(?:\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|este|mes|pasado|del|de|en|20\d{{2}}|comparar|gastos|compras|detalle|factura|vs)|$)'
    match = re.search(patron, texto_norm)
    if match:
        valores_str = match.group(1).strip()
        valores = re.split(r'\s*,\s*|\s+y\s+', valores_str)
        valores = [v.strip() for v in valores if v.strip() and len(v.strip()) > 1]
        valores = [v for v in valores if not _es_token_mes_o_periodo(v)]
        return valores

    return []


# =====================================================================
# PALABRAS A EXCLUIR (CENTRALIZADO)
# =====================================================================

PALABRAS_EXCLUIR_PROVEEDOR = [
    # Verbos de comparación
    'comparar', 'comparame', 'compara', 'comparacion', 'comparaciones',
    # Verbos de compras
    'compras', 'compra', 'compre', 'compramos', 'comprado',
    # Verbos de acción
    'traer', 'mostrar', 'ver', 'dame', 'pasame', 'mostrame',
    'necesito', 'quiero', 'buscar', 'busco', 'listar',
    # Artículos y preposiciones
    'de', 'del', 'la', 'el', 'los', 'las', 'en', 'por', 'para',
    'un', 'una', 'unos', 'unas', 'al', 'a', 'con', 'sin',
    # Temporal
    'mes', 'año', 'ano', 'meses', 'años', 'anos',
    # Meses (correctos + typos + abreviaturas)
    'enero', 'ene', 'ener', 'enro',
    'febrero', 'feb', 'febr', 'febrer', 'febreo',
    'marzo', 'mar', 'marz', 'marso',
    'abril', 'abr', 'abri', 'abrl',
    'mayo', 'may', 'mallo',
    'junio', 'jun', 'juni', 'juno',
    'julio', 'jul', 'juli', 'julo',
    'agosto', 'ago', 'agost', 'agoto', 'agsoto',
    'septiembre', 'sep', 'sept', 'set', 'setiembre', 'septirmbre', 'septiembr', 'setiembr',
    'octubre', 'oct', 'octu', 'octub', 'octubr', 'octbre', 'ocutbre',
    'noviembre', 'nov', 'noviem', 'noviemb', 'novimbre', 'novimbr', 'novienbre', 'novmbre',
    'diciembre', 'dic', 'diciem', 'diciemb', 'dicimbre', 'dicimbr', 'dicienbre', 'dicmbre',
    # Años
    '2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027', '2028', '2029', '2030',
    # Otros
    'vs', 'versus', 'contra', 'detalle', 'total', 'gastos', 'gasto',
    'proveedor', 'proveedores', 'articulo', 'articulos', 'familia', 'familias',
    # Saludos
    'hola', 'buenos', 'buenas', 'dias', 'tardes', 'noches', 'buen', 'dia',
    'gracias', 'porfa', 'por', 'favor',
    # Nombres comunes a ignorar
    'che', 'me', 'podrias', 'podes', 'puedes',
]

# Palabras que disparan comparación
PALABRAS_COMPARACION = ['comparar', 'comparame', 'compara', 'comparacion', 'comparaciones', 'vs', 'versus']


def _extraer_patron_libre(texto: str, excluir_palabras: List[str] = None) -> str:
    """Extrae patrón libre eliminando palabras clave"""
    if excluir_palabras is None:
        excluir_palabras = PALABRAS_EXCLUIR_PROVEEDOR
    
    txt = normalizar_texto(texto)
    txt = txt.replace("última", "ultima")
    
    # Limpiar signos de puntuación
    txt = re.sub(r'[,;:.!?¿¡]', ' ', txt)

    tokens = [t for t in re.split(r'\s+', txt)
              if t and t not in excluir_palabras and not _es_token_mes_o_periodo(t)]
    return " ".join(tokens).strip()


def _extraer_nro_factura(texto: str) -> Optional[str]:
    """Extrae número de factura (5+ dígitos)"""
    m = re.search(r'\b\d{5,}\b', str(texto).strip())
    if not m:
        return None
    return m.group(0)


# =====================================================================
# EXTRACCIÓN DE FECHAS Y PERÍODOS
# =====================================================================

def _month_range(year: int, month: int) -> Tuple[datetime, datetime]:
    """Retorna inicio y fin de un mes"""
    inicio = datetime(year, month, 1, 0, 0, 0)
    if month == 12:
        fin = datetime(year, 12, 31, 23, 59, 59)
    else:
        fin = (datetime(year, month + 1, 1) - timedelta(days=1)).replace(hour=23, minute=59, second=59)
    return inicio, fin


def extraer_meses_para_comparacion(texto: str) -> List[Tuple[datetime, datetime, str]]:
    """Extrae meses para comparación (soporte: nombres, YYYY-MM, typos, abreviaturas)"""
    texto_norm = normalizar_texto(texto)
    hoy = datetime.now()

    # Diccionario COMPLETO: typos + abreviaturas → número de mes
    meses_typos = {
        # Enero
        'enero': 1, 'ene': 1, 'ener': 1, 'enro': 1,
        # Febrero  
        'febrero': 2, 'feb': 2, 'febr': 2, 'febrer': 2, 'febreo': 2,
        # Marzo
        'marzo': 3, 'mar': 3, 'marz': 3, 'marso': 3,
        # Abril
        'abril': 4, 'abr': 4, 'abri': 4, 'abrl': 4,
        # Mayo
        'mayo': 5, 'may': 5, 'mallo': 5,
        # Junio
        'junio': 6, 'jun': 6, 'juni': 6, 'juno': 6,
        # Julio
        'julio': 7, 'jul': 7, 'juli': 7, 'julo': 7,
        # Agosto
        'agosto': 8, 'ago': 8, 'agost': 8, 'agoto': 8, 'agsoto': 8,
        # Septiembre
        'septiembre': 9, 'sep': 9, 'sept': 9, 'set': 9,
        'setiembre': 9, 'septirmbre': 9, 'septiembr': 9, 'setiembr': 9,
        # Octubre
        'octubre': 10, 'oct': 10, 'octu': 10, 'octub': 10, 'octubr': 10, 
        'octbre': 10, 'ocutbre': 10,
        # Noviembre
        'noviembre': 11, 'nov': 11, 'noviem': 11, 'noviemb': 11,
        'novimbre': 11, 'novimbr': 11, 'novienbre': 11, 'novmbre': 11,
        # Diciembre
        'diciembre': 12, 'dic': 12, 'diciem': 12, 'diciemb': 12,
        'dicimbre': 12, 'dicimbr': 12, 'dicienbre': 12, 'dicmbre': 12,
    }
    
    # Nombres bonitos para mostrar
    nombres_bonitos = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    encontrados = []

    # 1) YYYY-MM
    for m in re.finditer(r'\b(20\d{2})-(0[1-9]|1[0-2])\b', texto_norm):
        y = int(m.group(1))
        mo = int(m.group(2))
        ini, fin = _month_range(y, mo)
        encontrados.append((m.start(), ini, fin, f"{y}-{mo:02d}"))

    # 2) Buscar años en el texto
    anios_encontrados = sorted([int(x) for x in re.findall(r'\b(20\d{2})\b', texto_norm)])
    
    # 3) Buscar meses (ordenar por longitud DESC para evitar que "nov" matchee antes que "noviembre")
    meses_ordenados = sorted(meses_typos.keys(), key=len, reverse=True)
    meses_ya_encontrados = set()  # Evitar duplicados
    
    for variante in meses_ordenados:
        # Buscar con word boundary
        pattern = rf'\b{re.escape(variante)}\b'
        match = re.search(pattern, texto_norm)
        
        if match:
            num_mes = meses_typos[variante]
            
            # Si ya encontramos este mes, saltar
            if num_mes in meses_ya_encontrados:
                continue
            meses_ya_encontrados.add(num_mes)
            
            nombre = nombres_bonitos[num_mes]
            pos = match.start()
            
            # Si hay múltiples años, crear entrada para cada año
            if len(anios_encontrados) >= 2:
                for anio in anios_encontrados:
                    ini, fin = _month_range(anio, num_mes)
                    encontrados.append((pos, ini, fin, f"{nombre} {anio}"))
            elif len(anios_encontrados) == 1:
                ini, fin = _month_range(anios_encontrados[0], num_mes)
                encontrados.append((pos, ini, fin, f"{nombre} {anios_encontrados[0]}"))
            else:
                # Sin año → usar año actual
                ini, fin = _month_range(hoy.year, num_mes)
                encontrados.append((pos, ini, fin, nombre))

    # 4) "este mes" y "mes pasado"
    for m in re.finditer(r'\beste mes\b', texto_norm):
        ini, fin = _month_range(hoy.year, hoy.month)
        encontrados.append((m.start(), ini, fin, "Este mes"))

    for m in re.finditer(r'\bmes pasado\b', texto_norm):
        if hoy.month == 1:
            ini, fin = _month_range(hoy.year - 1, 12)
        else:
            ini, fin = _month_range(hoy.year, hoy.month - 1)
        encontrados.append((m.start(), ini, fin, "Mes pasado"))

    # Ordenar por posición y eliminar duplicados
    encontrados.sort(key=lambda x: x[0])

    salida = []
    vistos = set()
    for _, ini, fin, label in encontrados:
        key = (ini.date(), fin.date())
        if key in vistos:
            continue
        vistos.add(key)
        salida.append((ini, fin, label))

    return salida


def extraer_anios(texto: str) -> List[int]:
    """Extrae años (20xx) del texto"""
    txt = normalizar_texto(texto or "")
    anios = sorted({int(x) for x in re.findall(r"\b(20\d{2})\b", txt)})

    if not anios:
        hoy = datetime.now()
        anios = [hoy.year - 2, hoy.year - 1, hoy.year]
    return anios


def _extraer_mes_key(texto: str) -> Optional[str]:
    """Extrae mes en formato YYYY-MM"""
    txt = normalizar_texto(texto)

    # 1) YYYY-MM directo
    m = re.search(r'\b(20\d{2})-(0[1-9]|1[0-2])\b', txt)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    # 2) Nombre de mes + año opcional
    meses_map = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }

    for mn, num in meses_map.items():
        if mn in txt:
            y = datetime.now().year
            my = re.search(r'\b(20\d{2})\b', txt)
            if my:
                y = int(my.group(1))
            return f"{y}-{num:02d}"

    return None


def _extraer_mes_keys_multiples(texto: str) -> List[str]:
    """Extrae múltiples períodos YYYY-MM"""
    txt = normalizar_texto(texto)
    hoy = datetime.now()

    meses_map = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }

    encontrados = []

    # 1) YYYY-MM
    for m in re.finditer(r'\b(20\d{2})-(0[1-9]|1[0-2])\b', txt):
        encontrados.append(f"{m.group(1)}-{m.group(2)}")

    # 2) Nombres de meses
    patron = r'\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b(?:\s*(20\d{2}))?'
    for m in re.finditer(patron, txt):
        mes_nombre = m.group(1)
        anio_txt = m.group(2)
        y = int(anio_txt) if anio_txt else hoy.year
        mo = meses_map[mes_nombre]
        encontrados.append(f"{y}-{mo:02d}")

    seen = set()
    out = []
    for k in encontrados:
        if k not in seen:
            seen.add(k)
            out.append(k)

    return out


def _extraer_lista_familias(texto: str) -> List[str]:
    """Extrae lista de familias (1-6 chars, ej: G, FB, ID)"""
    raw = str(texto).strip()
    txt = normalizar_texto(raw)

    m = re.search(r'(secciones|seccion|familias|familia)\s+(.+)$', txt)
    if not m:
        return []

    tail = m.group(2)
    tail = re.split(r'\b(20\d{2}-(0[1-9]|1[0-2]))\b', tail)[0]
    meses_nombres = "(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"
    tail = re.split(meses_nombres, tail)[0]

    tokens = re.split(r'[\s,]+', tail)
    out = []
    for t in tokens:
        t = t.strip()
        if not t or _es_token_mes_o_periodo(t):
            continue
        if t in {"gastos", "gasto", "comparar", "compras"}:
            continue
        if 1 <= len(t) <= 6:
            out.append(t.upper())

    seen = set()
    res = []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res


# =====================================================================
# HELPER: DETECTAR SI ES COMPARACIÓN
# =====================================================================

def _es_comparacion(texto_norm: str) -> bool:
    """Detecta si el texto pide una comparación"""
    return any(p in texto_norm for p in PALABRAS_COMPARACION)


def _extraer_proveedor_limpio(texto: str) -> str:
    """Extrae el proveedor limpiando todas las palabras innecesarias"""
    return _extraer_patron_libre(texto, PALABRAS_EXCLUIR_PROVEEDOR)


# =====================================================================
# DETECTOR DE INTENCIÓN PRINCIPAL CON ORDEN DE PRIORIDAD (CORREGIDO)
# =====================================================================

def detectar_intencion(texto: str) -> Dict:
    """
    Detecta intención con ORDEN DE PRIORIDAD claro
    Retorna: {'tipo': 'xxx', 'parametros': {...}, 'debug': 'info'}
    
    CAMBIOS:
    - Comparaciones tienen MAYOR prioridad
    - "comparame", "compara" ahora se detectan
    - Mejor limpieza del proveedor
    """
    
    texto_norm = normalizar_texto(texto).replace("última", "ultima")
    intencion = {'tipo': 'consulta_general', 'parametros': {}, 'debug': ''}

    # =====================================================================
    # 🏆 PRIORIDAD X: TOP PROVEEDORES (COMPRAS IA) - DETECCIÓN FLEXIBLE
    # =====================================================================
    # Detecta variantes como:
    # - "top 10 proveedores"
    # - "top proveedores noviembre 2025"
    # - "ranking proveedores 2025"
    # - "mayores proveedores noviembre"
    # - "principales proveedores 2025"
    # - "proveedores con mayor gasto noviembre 2025"
    
    palabras_top = ['top', 'ranking', 'mayores', 'principales', 'mayor gasto', 'mas compramos', 'mas gastamos']
    tiene_top = any(p in texto_norm for p in palabras_top)
    tiene_proveedores = 'proveedor' in texto_norm or 'proveedores' in texto_norm
    
    if tiene_top and tiene_proveedores:
        anios = extraer_anios(texto)
        mes_key = _extraer_mes_key(texto)
        
        # Detectar moneda
        moneda = None
        if any(m in texto_norm for m in ['dolares', 'dolar', 'usd', 'u$s']):
            moneda = 'U$S'
        elif any(m in texto_norm for m in ['pesos', '$']):
            moneda = '$'

        params = {}
        
        if moneda:
            params["moneda"] = moneda
        if mes_key:
            params["mes"] = mes_key
        elif anios:
            params["anio"] = anios[0]

        return {
            "tipo": "top_10_proveedores",
            "parametros": params,
            "debug": f"Match: top proveedores (mes={mes_key}, anio={anios[0] if anios else None}, moneda={moneda})"
        }

    # =====================================================================
    # PRIORIDAD 1: LISTAR VALORES (muy específico)
    # =====================================================================
    if 'listar' in texto_norm and any(x in texto_norm for x in ['proveedores', 'familias', 'articulos', 'proveedor', 'familia', 'articulo']):
        intencion['tipo'] = 'listar_valores'
        intencion['debug'] = 'Match: listar valores'
        return intencion

    # =====================================================================
    # PRIORIDAD 2: FACTURA POR NÚMERO (más específico que "última factura")
    # =====================================================================
    nro = _extraer_nro_factura(texto)
    if nro and ('factura' in texto_norm) and any(x in texto_norm for x in ['detalle', 'ver', 'mostrar', 'numero', 'nro']):
        intencion['tipo'] = 'detalle_factura_numero'
        intencion['parametros']['nro_factura'] = nro
        intencion['debug'] = f'Match: factura número {nro}'
        return intencion

    # =====================================================================
    # PRIORIDAD 3: FACTURA COMPLETA DE ARTÍCULO
    # =====================================================================
    if ('factura completa' in texto_norm) or (('ultima' in texto_norm) and ('factura' in texto_norm) and ('completa' in texto_norm or 'toda' in texto_norm)):
        intencion['tipo'] = 'factura_completa_articulo'
        intencion['debug'] = 'Match: factura completa artículo'
        return intencion

    # =====================================================================
    # PRIORIDAD 4: ÚLTIMA FACTURA
    # =====================================================================
    tiene_ultimo = any(x in texto_norm for x in ['ultima', 'ultimo', 'ultim'])
    tiene_factura = 'factura' in texto_norm
    tiene_cuando_vino = any(x in texto_norm for x in ['cuando vino', 'cuando llego', 'cuando entro'])
    
    if (tiene_ultimo and tiene_factura) or (tiene_cuando_vino and tiene_ultimo) or (tiene_ultimo and not tiene_factura and len(texto_norm.split()) >= 2):
        if not any(x in texto_norm for x in ['completa', 'toda', 'todas', 'entera']):
            # NO si es comparación
            if not _es_comparacion(texto_norm):
                intencion['tipo'] = 'ultima_factura_articulo'
                intencion['debug'] = 'Match: última factura (flexible - ignora ruido)'
                return intencion

    # =====================================================================
    # PRIORIDAD 5: TODAS LAS FACTURAS DE ARTÍCULO
    # =====================================================================
    if any(x in texto_norm for x in ['facturas', 'en que factura', 'cuando vino', 'listar facturas', 'factura vino']):
        if 'ultima' not in texto_norm and not _es_comparacion(texto_norm):
            intencion['tipo'] = 'facturas_articulo'
            intencion['debug'] = 'Match: todas las facturas de artículo'
            return intencion

    # =====================================================================
    # PRIORIDAD 6: GASTOS SECCIONES / FAMILIAS (solo si NO es comparación)
    # =====================================================================
    tiene_gastos = any(k in texto_norm for k in ['gastos', 'gasto', 'gastado', 'gastamos', 'importes', 'importe', 'cuanto gasto', 'cuánto gasto', 'cuanto fue', 'cuánto fue'])
    tiene_familia = any(k in texto_norm for k in ['familia', 'familias', 'seccion', 'secciones'])
    
    # ⚠️ NO matchear si es comparación (eso va a PRIORIDAD 7)
    if tiene_gastos and tiene_familia and not _es_comparacion(texto_norm):
        intencion['tipo'] = 'gastos_secciones'
        intencion['debug'] = 'Match: gastos por familias/secciones'
        return intencion


    # =====================================================================
    # 🌟 PRIORIDAD 7: COMPARACIONES (ANTES DE COMPRAS)
    # =====================================================================
    if _es_comparacion(texto_norm):
        anios = extraer_anios(texto)
        meses = extraer_meses_para_comparacion(texto)
        
        # Extraer proveedor LIMPIO
        prov_limpio = _extraer_proveedor_limpio(texto)
        proveedores = [prov_limpio] if prov_limpio else []
        
        # Detectar si es comparación de FAMILIAS/GASTOS
        es_familia = any(x in texto_norm for x in ['familia', 'familias', 'seccion', 'secciones'])
        tiene_gastos = any(x in texto_norm for x in ['gastos', 'gasto', 'gastado'])
        
        # Detectar moneda
        moneda = None
        if any(m in texto_norm for m in ['dolares', 'dolar', 'usd', 'u$s']):
            moneda = 'U$S'
        elif any(m in texto_norm for m in ['pesos']):
            moneda = '$'
        
        # =====================================================================
        # CASO A: COMPARAR FAMILIAS/GASTOS POR AÑOS
        # Ej: "comparar gastos familias 2023 2024", "comparar familias 2023 2024 pesos"
        # =====================================================================
        if (es_familia or tiene_gastos) and len(set(anios)) >= 2 and not proveedores:
            intencion['tipo'] = 'comparar_familia_anios_monedas'
            intencion['parametros']['anios'] = sorted(list(set(anios)))
            if moneda:
                intencion['parametros']['moneda'] = moneda
            intencion['debug'] = f'Match: comparar familias años {sorted(anios)} moneda={moneda}'
            return intencion
        
        # =====================================================================
        # CASO B: COMPARAR FAMILIAS/GASTOS POR MESES
        # Ej: "comparar gastos familias junio julio", "comparar familias junio julio pesos"
        # =====================================================================
        if (es_familia or tiene_gastos) and len(meses) >= 2 and not proveedores:
            intencion['tipo'] = 'comparar_familia_meses'
            intencion['parametros']['meses'] = meses
            if moneda:
                intencion['parametros']['moneda'] = moneda
            intencion['debug'] = f'Match: comparar familias meses {[m[2] for m in meses]} moneda={moneda}'
            return intencion
        
        # =====================================================================
        # CASO C: Comparar PROVEEDOR - mismo mes en diferentes años
        # Ej: "comparame compras roche noviembre 2023 2024"
        # =====================================================================
        if len(anios) >= 2 and len(meses) >= 2:
            intencion['tipo'] = 'comparar_proveedor_meses'
            intencion['parametros']['meses'] = meses
            intencion['parametros']['proveedores'] = proveedores
            if moneda:
                intencion['parametros']['moneda'] = moneda
            intencion['debug'] = f'Match: comparar {proveedores} meses {[m[2] for m in meses]}'
            return intencion
        
        # =====================================================================
        # CASO D: Comparar PROVEEDOR por años completos
        # Ej: "comparar roche 2023 2024"
        # =====================================================================
        if len(set(anios)) >= 2:
            intencion['tipo'] = 'comparar_proveedor_anios_monedas'
            intencion['parametros']['anios'] = sorted(list(set(anios)))
            intencion['parametros']['proveedores'] = proveedores
            if moneda:
                intencion['parametros']['moneda'] = moneda
            intencion['debug'] = f'Match: comparar proveedor {proveedores} años {sorted(anios)}'
            return intencion
        
        # =====================================================================
        # CASO E: Comparar meses diferentes del mismo año
        # Ej: "comparar junio julio 2025"
        # =====================================================================
        if len(meses) >= 2:
            # Comparar artículo
            if 'articulo' in texto_norm:
                intencion['tipo'] = 'comparar_articulo_meses'
                intencion['debug'] = f'Match: comparar artículo meses {[m[2] for m in meses]}'
                return intencion
            
            # Comparar proveedor (si hay proveedor detectado)
            if 'proveedor' in texto_norm or proveedores:
                intencion['tipo'] = 'comparar_proveedor_meses'
                intencion['parametros']['proveedores'] = proveedores
                intencion['debug'] = f'Match: comparar proveedor meses {[m[2] for m in meses]}'
                return intencion
            
            # Comparar familia (si tiene palabras de familia/gastos)
            if es_familia or tiene_gastos:
                intencion['tipo'] = 'comparar_familia_meses'
                intencion['debug'] = f'Match: comparar familia meses {[m[2] for m in meses]}'
                return intencion
            
            # Default: proveedor
            intencion['tipo'] = 'comparar_proveedor_meses'
            intencion['parametros']['proveedores'] = proveedores
            intencion['debug'] = f'Match: comparar (default) meses {[m[2] for m in meses]}'
            return intencion
        
        # =====================================================================
        # FALLBACK: Es comparación pero no pude extraer parámetros
        # → Pasar a IA para que interprete (typos, lenguaje natural, etc.)
        # =====================================================================
        # Si llegó acá es porque detectó "comparar/comparame/etc" pero no pudo
        # extraer meses ni años suficientes (posible typo como "novimbr")
        intencion['tipo'] = 'consulta_general'  # Forzar que vaya a IA
        intencion['debug'] = 'Comparación detectada pero sin parámetros suficientes → IA'
        return intencion

    # =====================================================================
    # PRIORIDAD 8: COMPRAS POR MES (formato Excel)
    # =====================================================================
    if (
        ('compras' in texto_norm or 'compra' in texto_norm)
        and ('por mes' in texto_norm or 'del mes' in texto_norm)
        and any(x in texto_norm for x in ['listar', 'detalle', 'ver', 'mostrar', 'excel'])
    ):
        intencion['tipo'] = 'compras_por_mes'
        intencion['debug'] = 'Match: compras por mes'
        return intencion

    # =====================================================================
    # PRIORIDAD 9: DETALLE COMPRAS PROVEEDOR / ARTÍCULO + MES O AÑO
    # =====================================================================
    if ('compra' in texto_norm or 'compras' in texto_norm or 'compre' in texto_norm):

        # NO si ya es comparación
        if not _es_comparacion(texto_norm):

            mes_key = _extraer_mes_key(texto)
            prov = _extraer_proveedor_limpio(texto)
            articulos = extraer_valores_multiples(texto, 'articulo')

            # -------------------------------------------------
            # 🔥 DESAMBIGUACIÓN: términos que son ARTÍCULO (no proveedor)
            # -------------------------------------------------
            if (not articulos) and prov:
                prov_norm = (prov or "").strip().lower()
                if prov_norm in {"vitek"}:
                    articulos = [prov]
                    prov = None

            # -------------------------------------------------
            # 🔹 ARTÍCULO + MES
            # -------------------------------------------------
            if mes_key and articulos:
                intencion['tipo'] = 'detalle_compras_articulo_mes'
                intencion['parametros']['mes_key'] = mes_key
                intencion['parametros']['articulo_like'] = articulos[0]
                intencion['debug'] = f"Match: detalle compras artículo {articulos[0]} en {mes_key}"
                return intencion

            # -------------------------------------------------
            # 🔹 PROVEEDOR + MES
            # -------------------------------------------------
            if mes_key and prov:
                intencion['tipo'] = 'detalle_compras_proveedor_mes'
                intencion['parametros']['mes_key'] = mes_key
                intencion['parametros']['proveedor_like'] = prov
                intencion['debug'] = f"Match: detalle compras {prov} en {mes_key}"
                return intencion

            # -------------------------------------------------
            # 🔹 AÑO EXPLÍCITO (solo si el usuario lo escribió)
            # -------------------------------------------------
            anios = sorted({int(y) for y in re.findall(r"\b(20\d{2})\b", texto_norm)})

            # -------------------------------------------------
            # 🔹 ARTÍCULO + 2+ AÑOS → COMPARACIÓN
            # -------------------------------------------------
            if len(anios) >= 2 and articulos:
                intencion['tipo'] = 'comparar_articulo_anios'
                intencion['parametros']['anios'] = anios
                intencion['parametros']['articulo_like'] = articulos[0]
                intencion['debug'] = f"Match: comparar artículo {articulos[0]} en años {anios}"
                return intencion

            # -------------------------------------------------
            # 🔹 ARTÍCULO + 1 AÑO
            # -------------------------------------------------
            if anios and articulos:
                intencion['tipo'] = 'detalle_compras_articulo_anio'
                intencion['parametros']['anio'] = anios[0]
                intencion['parametros']['articulo_like'] = articulos[0]
                intencion['debug'] = f"Match: detalle compras artículo {articulos[0]} en año {anios[0]}"
                return intencion

            # -------------------------------------------------
            # 🔹 PROVEEDOR + AÑO
            # -------------------------------------------------
            if anios and prov:
                intencion['tipo'] = 'detalle_compras_proveedor_anio'
                intencion['parametros']['anio'] = anios[0]
                intencion['parametros']['proveedor_like'] = prov
                intencion['debug'] = f"Match: detalle compras {prov} en año {anios[0]}"
                return intencion

    # =====================================================================
    # PRIORIDAD 10: TOTAL COMPRAS PROVEEDOR + MONEDA + 2+ PERÍODOS
    # =====================================================================
    if any(k in texto_norm for k in ["proveedor", "proveedores", "por proveedor"]) and any(k in texto_norm for k in ["total", "ranking", "mayor", "gasto", "gastado", "se gasto", "cuanto"]):
        periodos = _extraer_mes_keys_multiples(texto)
        if len(periodos) >= 2:
            intencion['tipo'] = 'total_proveedor_moneda_periodos'
            intencion['parametros']['periodos'] = periodos
            intencion['debug'] = f'Match: total proveedor múltiples períodos {periodos}'
            return intencion

    # =====================================================================
    # PRIORIDAD 11: DETALLE GENERAL
    # =====================================================================
    if 'detalle' in texto_norm or 'que vino' in texto_norm or 'listado' in texto_norm:
        intencion['tipo'] = 'detalle'
        intencion['debug'] = 'Match: detalle general'
        return intencion

    # =====================================================================
    # PRIORIDAD 12: COMPRAS GENERAL
    # =====================================================================
    if 'compras' in texto_norm or 'compra' in texto_norm:
        intencion['tipo'] = 'consulta_general'
        intencion['debug'] = 'Match: compras general'
        return intencion

    # =====================================================================
    # FALLBACK: CONSULTA GENERAL
    # =====================================================================
    intencion['debug'] = 'No match específico, consulta general'
    return intencion


# =====================================================================
# CONSTRUCCIÓN DE WHERE CLAUSE
# =====================================================================

def construir_where_clause(texto: str) -> Tuple[str, tuple]:
    """Construye cláusula WHERE basada en el texto"""
    condiciones = []
    params = []
    texto_norm = normalizar_texto(texto)

    condiciones.append("(tipo_comprobante = 'Compra Contado' OR tipo_comprobante LIKE 'Compra%%')")

    if 'proveedor' in texto_norm:
        proveedores = extraer_valores_multiples(texto, 'proveedor')
        if proveedores:
            parts = []
            for prov in proveedores:
                parts.append("LOWER(Proveedor) LIKE %s")
                params.append(f"%{prov.lower()}%")
            condiciones.append(f"({' OR '.join(parts)})")

    if 'articulo' in texto_norm:
        articulos = extraer_valores_multiples(texto, 'articulo')

        if articulos:
            parts = []

            for art in articulos:
                parts.append("LOWER(Articulo) LIKE %s")
                params.append(f"%{art.lower()}%")

            condiciones.append(f"({' OR '.join(parts)})")

    if 'familia' in texto_norm:
        familias = extraer_valores_multiples(texto, 'familia')
        if familias:
            parts = []
            for fam in familias:
                parts.append("LOWER(Familia) LIKE %s")
                params.append(f"%{fam.lower()}%")
            condiciones.append(f"({' OR '.join(parts)})")

    where_clause = " AND ".join(condiciones) if condiciones else "1=1"
    return where_clause, tuple(params)