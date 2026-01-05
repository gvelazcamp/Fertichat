# =========================
# IA_COMPARATIVAS.PY - INTÉRPRETE COMPARATIVAS (CANÓNICO)
# =========================
# IDEA CLAVE (TU REGLA):
# - Lo importante es detectar la FUNCIÓN (ACCIÓN | OBJETO | TIEMPO | MULTI | TIPO | PARAMS).
# - Todo lo demás que el usuario escriba antes/después (hola, insultos, texto extra) NO importa.
# - Si el usuario dice "comparar" pero no da 2 años / 2 meses -> NO se ejecuta. Se sugiere la función correcta.
#
# Ejemplo:
# "hola gonzalo como estas compara las compras tresul 2025"
# -> Falta 2º año -> sugerir "comparar compras tresul 2024 2025"

import re
import unicodedata
from typing import Dict, List, Tuple, Optional

import streamlit as st

MESES = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "setiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}

MAX_PROVEEDORES = 5
MAX_MESES = 6
MAX_ANIOS = 4

# =====================================================================
# TABLA CANÓNICA (SOLO COMPARATIVAS)
# =====================================================================
TABLA_CANONICA_COMPARATIVAS = r"""
| # | ACCIÓN | OBJETO | TIEMPO | MULTI | TIPO (output) | PARAMS |
|---|--------|--------|--------|-------|---------------|--------|
| 16 | comparar | proveedor | mes+mes (mismo anio) | no | comparar_proveedor_meses | proveedor, mes1, mes2, label1, label2 |
| 17 | comparar | proveedor | anio+anio | no | comparar_proveedor_anios | proveedor, anios, label1, label2 |
| 18 | comparar compras | proveedor | mes+mes | no | comparar_proveedor_meses | proveedor, mes1, mes2, label1, label2 |
| 19 | comparar compras | proveedor | anio+anio | no | comparar_proveedor_anios | proveedor, anios, label1, label2 |
| 22 | comparar | proveedor | meses (lista) | si (<=6) | comparar_proveedor_meses | proveedor, mes1, mes2, label1, label2 |
| 23 | comparar | proveedor | anios (lista) | si (<=4) | comparar_proveedor_anios | proveedor, anios, label1, label2 |
| 30 | comparar compras | proveedor | mes(YYYY-MM)+mes(YYYY-MM) | no | comparar_proveedor_meses | proveedor, mes1, mes2, label1, label2 |
| 31 | comparar compras | proveedor | anio+anio | no | comparar_proveedor_anios | proveedor, anios, label1, label2 |
| 34 | comparar compras | proveedor | "junio julio 2025" | no | comparar_proveedor_meses | proveedor, 2025-06, 2025-07, label1, label2 |
| 35 | comparar compras | proveedor | "noviembre diciembre 2025" | no | comparar_proveedor_meses | proveedor, 2025-11, 2025-12, label1, label2 |
| 36 | comparar compras | proveedor | "2024 2025" | no | comparar_proveedor_anios | proveedor, [2024,2025], label1, label2 |
| 41 | comparar compras | proveedor | "enero febrero" (sin año) | no | no_entendido | sugerir: "comparar compras proveedor enero febrero 2025" |
| 46 | comparar | proveedor | mes vs mes | no | comparar_proveedor_meses | proveedor, mes1, mes2, label1, label2 |
| 47 | comparar | proveedor | anio vs anio | no | comparar_proveedor_anios | proveedor, anios, label1, label2 |
"""

# =====================================================================
# HELPERS NORMALIZACIÓN
# =====================================================================
def _strip_accents(s: str) -> str:
    if not s:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

def _key(s: str) -> str:
    s = _strip_accents((s or "").lower().strip())
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def _tokens(texto: str) -> List[str]:
    raw = re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9]+", (texto or "").lower())
    out: List[str] = []
    for t in raw:
        k = _key(t)
        if len(k) >= 3:
            out.append(k)
    return out

# =====================================================================
# CARGA LISTAS DESDE SUPABASE (cache)
# =====================================================================
@st.cache_data(ttl=60 * 60)
def _cargar_listas_supabase() -> Dict[str, List[str]]:
    proveedores: List[str] = []

    try:
        from supabase_client import supabase  # type: ignore
        if supabase is None:
            return {"proveedores": []}

        # Proveedores: tabla proveedores, columna nombre (variantes)
        for col in ["nombre", "Nombre", "NOMBRE"]:
            try:
                res = supabase.table("proveedores").select(col).execute()
                data = res.data or []
                proveedores = [str(r.get(col)).strip() for r in data if r.get(col)]
                if proveedores:
                    break
            except Exception:
                continue

    except Exception:
        return {"proveedores": []}

    proveedores = sorted(list(set([p for p in proveedores if p])))
    return {"proveedores": proveedores}

def _get_indices() -> List[Tuple[str, str]]:
    listas = _cargar_listas_supabase()
    prov = [(p, _key(p)) for p in (listas.get("proveedores") or []) if p]
    return prov

def _match_best(texto: str, index: List[Tuple[str, str]], max_items: int = 1) -> List[str]:
    toks = _tokens(texto)
    if not toks or not index:
        return []

    # 1) EXACT token match (cuando el proveedor es 1 palabra exacta en la lista)
    toks_set = set(toks)
    for orig, norm in index:
        if norm in toks_set:
            return [orig]

    # 2) substring + score (cuando el usuario escribe "tresul" y en la lista está "LABORATORIO TRESUL ...")
    candidatos: List[Tuple[int, str]] = []
    for orig, norm in index:
        for tk in toks:
            if tk and tk in norm:
                score = (len(tk) * 1000) - len(norm)
                candidatos.append((score, orig))

    if not candidatos:
        return []

    candidatos.sort(key=lambda x: (-x[0], x[1]))
    out: List[str] = []
    seen = set()
    for _, orig in candidatos:
        if orig not in seen:
            seen.add(orig)
            out.append(orig)
        if len(out) >= max_items:
            break

    return out

# =====================================================================
# RESOLVER ALIASES DE PROVEEDOR (TRESUL / BIODIAGNOSTICO / ROCHE)
# - Devuelve SIEMPRE un proveedor REAL de Supabase (orig), no "tresul"
# =====================================================================
ALIASES_PROVEEDOR: Dict[str, List[str]] = {
    # usuario -> posibles fragmentos en el nombre real (normalizados por _key)
    "tresul": ["tresul", "laboratoriotresul"],
    "biodiagnostico": ["biodiagnostico", "cabinsur", "cabinsursrl", "cabinsuruy", "cabinsururuguay"],
    "roche": ["roche", "rochediagnostics", "rocheinternational"],
}

def _buscar_proveedor_en_lista_por_fragmentos(
    idx_prov: List[Tuple[str, str]],
    fragmentos_norm: List[str],
) -> Optional[str]:
    """
    Devuelve el 'orig' de Supabase que mejor matchee cualquiera de los fragmentos.
    Priorizamos nombres más específicos y/o con 'laboratorio' cuando corresponde.
    """
    if not idx_prov or not fragmentos_norm:
        return None

    best_orig: Optional[str] = None
    best_score: Optional[int] = None

    for orig, norm in idx_prov:
        hit_any = False
        score = 0

        for frag in fragmentos_norm:
            if frag and frag in norm:
                hit_any = True
                score += 1000 + (len(frag) * 10)

        if not hit_any:
            continue

        # preferir "laboratorio" cuando existe (tresul suele venir así)
        if "laboratorio" in norm:
            score += 250

        # preferir nombres más específicos (leve)
        score -= int(len(norm) / 10)

        if best_score is None or score > best_score:
            best_score = score
            best_orig = orig

    return best_orig

def _resolver_proveedor_canonico(texto_lower: str, idx_prov: List[Tuple[str, str]]) -> Optional[str]:
    """
    1) Si detecta alias conocido (tresul/biodiagnostico/cabinsur/roche) -> devuelve el proveedor real.
    2) Si no, usa match_best (lista).
    3) Si no, intenta mapear el "proveedor libre" a un proveedor real (fragmento).
    """
    tlk = _key(texto_lower)

    # 1) alias directo por presencia en texto
    for alias, frags in ALIASES_PROVEEDOR.items():
        if alias in tlk:
            cand = _buscar_proveedor_en_lista_por_fragmentos(idx_prov, frags)
            if cand:
                return cand

    # 2) match por lista (general)
    provs = _match_best(texto_lower, idx_prov, max_items=1)
    if provs:
        return provs[0]

    # 3) proveedor libre -> intentar mapear a un proveedor real por fragmento
    proveedor_libre = _extraer_proveedor_libre(texto_lower)
    if proveedor_libre:
        frag = _key(proveedor_libre)
        if frag and len(frag) >= 3:
            cand = _buscar_proveedor_en_lista_por_fragmentos(idx_prov, [frag])
            if cand:
                return cand

    return None

def _extraer_proveedor_libre(texto_lower: str) -> Optional[str]:
    """
    Saca palabras funcionales y deja "lo que parece proveedor".
    Esto NO se usa como proveedor final; se usa para mapear a un proveedor real.
    """
    tmp = texto_lower

    # sacar triggers
    tmp = re.sub(r"\b(comparar|comparame|compara)\b", " ", tmp)
    tmp = re.sub(r"\b(compras?|compra)\b", " ", tmp)

    # sacar meses
    tmp = re.sub(
        r"\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b",
        " ",
        tmp,
    )

    # sacar años
    tmp = re.sub(r"\b(2023|2024|2025|2026)\b", " ", tmp)

    # normalizar espacios
    tmp = re.sub(r"\s+", " ", tmp).strip()

    if tmp and len(tmp) >= 3:
        return tmp
    return None

# =====================================================================
# PARSEO TIEMPO
# =====================================================================
def _extraer_anios(texto: str) -> List[int]:
    anios = re.findall(r"(2023|2024|2025|2026)", texto or "")
    out: List[int] = []
    for a in anios:
        try:
            out.append(int(a))
        except Exception:
            pass

    seen = set()
    out2: List[int] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            out2.append(x)
    return out2[:MAX_ANIOS]

def _extraer_meses_nombre(texto: str) -> List[str]:
    tl = (texto or "").lower()
    ms = [m for m in MESES.keys() if m in tl]
    seen = set()
    out: List[str] = []
    for m in ms:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out[:MAX_MESES]

def _extraer_meses_yyyymm(texto: str) -> List[str]:
    ms = re.findall(r"(2023|2024|2025|2026)[-/](0[1-9]|1[0-2])", texto or "")
    out = [f"{a}-{m}" for a, m in ms]
    seen = set()
    out2: List[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            out2.append(x)
    return out2[:MAX_MESES]

def _to_yyyymm(anio: int, mes_nombre: str) -> str:
    return f"{anio}-{MESES[mes_nombre]}"

# =====================================================================
# INTÉRPRETE COMPARATIVAS
# =====================================================================
def interpretar_comparativas(pregunta: str) -> Dict:
    texto = (pregunta or "").strip()
    texto_lower = texto.lower().strip()

    # gatillos
    es_comparar = ("comparar" in texto_lower) or ("comparame" in texto_lower) or ("compara" in texto_lower)
    es_compras = ("compra" in texto_lower) or ("compras" in texto_lower)

    if not (es_comparar and es_compras):
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "Probá: comparar compras roche junio julio 2025 | comparar compras tresul 2024 2025",
            "debug": "comparar: no match (faltan gatillos comparar+compras)",
        }

    idx_prov = _get_indices()

    anios = _extraer_anios(texto_lower)
    meses_nombre = _extraer_meses_nombre(texto_lower)
    meses_yyyymm = _extraer_meses_yyyymm(texto_lower)

    # =========================
    # PROVEEDOR (CANÓNICO)
    # - SIEMPRE intentar devolver el proveedor real de Supabase
    # =========================
    proveedor_final = _resolver_proveedor_canonico(texto_lower, idx_prov)

    if not proveedor_final:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "No reconocí el proveedor. Probá: comparar compras tresul 2024 2025 | comparar compras biodiagnostico 2024 2025",
            "debug": "comparar: proveedor no reconocido",
        }

    # =========================
    # FUNCIÓN 1: comparar proveedor meses (YYYY-MM)
    # =========================
    if len(meses_yyyymm) >= 2:
        mes1, mes2 = meses_yyyymm[0], meses_yyyymm[1]
        return {
            "tipo": "comparar_proveedor_meses",
            "parametros": {
                "proveedor": proveedor_final,
                "mes1": mes1,
                "mes2": mes2,
                "label1": mes1,
                "label2": mes2,
            },
            "debug": "comparar proveedor meses (YYYY-MM)",
        }

    # =========================
    # FUNCIÓN 2: comparar proveedor meses (nombre + año)
    # =========================
    if len(meses_nombre) >= 2 and len(anios) >= 1:
        anio = anios[0]
        mes1 = _to_yyyymm(anio, meses_nombre[0])
        mes2 = _to_yyyymm(anio, meses_nombre[1])
        return {
            "tipo": "comparar_proveedor_meses",
            "parametros": {
                "proveedor": proveedor_final,
                "mes1": mes1,
                "mes2": mes2,
                "label1": f"{meses_nombre[0]} {anio}",
                "label2": f"{meses_nombre[1]} {anio}",
            },
            "debug": "comparar proveedor meses (nombre+anio)",
        }

    # Si dio 1 mes o 2 meses sin año -> sugerir
    if len(meses_nombre) >= 2 and len(anios) == 0:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": f"Para comparar meses necesito el año. Probá: comparar compras {proveedor_final} {meses_nombre[0]} {meses_nombre[1]} 2025",
            "debug": "comparar: meses sin año",
        }

    # =========================
    # FUNCIÓN 3: comparar proveedor años (año vs año)
    # =========================
    if len(anios) >= 2:
        y1, y2 = anios[0], anios[1]
        return {
            "tipo": "comparar_proveedor_anios",
            "parametros": {
                "proveedor": proveedor_final,
                "anios": [y1, y2],
                "label1": str(y1),
                "label2": str(y2),
            },
            "debug": "comparar proveedor años",
        }

    # Si hay 1 solo año -> sugerir explícitamente (tu regla)
    if len(anios) == 1:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": f"Para comparar años necesito 2 años. Probá: comparar compras {proveedor_final} {anios[0]-1} {anios[0]}",
            "debug": "comparar: solo 1 año",
        }

    return {
        "tipo": "no_entendido",
        "parametros": {},
        "sugerencia": f"Probá: comparar compras {proveedor_final} junio julio 2025 | comparar compras {proveedor_final} 2024 2025",
        "debug": "comparar: faltan meses/año",
    }
