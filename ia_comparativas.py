# =========================
# IA_COMPARATIVAS.PY - INTÉRPRETE COMPARATIVAS (CANÓNICO)
# =========================
# CAMBIOS (mínimos):
# 1) Agregué TABLA_CANONICA_COMPARATIVAS (solo filas comparativas)
# 2) Agregué fallback proveedor_libre igual que IA_COMPRAS (para que "tresul" funcione)
# 3) No toqué la lógica de comparación: mes vs mes / año vs año

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
| 17 | comparar | proveedor | anio+anio | no | comparar_proveedor_anios | proveedor, anios |
| 18 | comparar compras | proveedor | mes+mes | no | comparar_proveedor_meses | proveedor, mes1, mes2, label1, label2 |
| 19 | comparar compras | proveedor | anio+anio | no | comparar_proveedor_anios | proveedor, anios |
| 30 | comparar compras | proveedor | mes(YYYY-MM)+mes(YYYY-MM) | no | comparar_proveedor_meses | proveedor, mes1, mes2, label1, label2 |
| 31 | comparar compras | proveedor | anio+anio | no | comparar_proveedor_anios | proveedor, anios |
| 34 | comparar compras | proveedor | "junio julio 2025" | no | comparar_proveedor_meses | proveedor, 2025-06, 2025-07, label1, label2 |
| 35 | comparar compras | proveedor | "noviembre diciembre 2025" | no | comparar_proveedor_meses | proveedor, 2025-11, 2025-12, label1, label2 |
| 36 | comparar compras | proveedor | "2024 2025" | no | comparar_proveedor_anios | proveedor, [2024,2025] |
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

    # 1) PRIORIDAD ABSOLUTA: MATCH EXACTO
    toks_set = set(toks)
    for orig, norm in index:
        if norm in toks_set:
            return [orig]

    # 2) FALLBACK: substring + score
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
# EXTRAER PROVEEDOR LIBRE (IGUAL A COMPRAS, ADAPTADO A COMPARATIVAS)
# =====================================================================
def _extraer_proveedor_libre_comparativas(texto_lower: str) -> Optional[str]:
    tmp = texto_lower

    # sacar palabras de acción
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
# INTÉRPRETE COMPARATIVAS
# =====================================================================
def interpretar_comparativas(pregunta: str) -> Dict:
    texto = (pregunta or "").strip()
    texto_lower = texto.lower().strip()

    es_comparar = ("comparar" in texto_lower) or ("comparame" in texto_lower) or ("compara" in texto_lower)
    es_compras = ("compra" in texto_lower) or ("compras" in texto_lower)

    if not (es_comparar and es_compras):
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "Probá: comparar compras roche junio julio 2025 | comparar compras tresul 2023 2024",
            "debug": "comparar: no match",
        }

    idx_prov = _get_indices()
    provs = _match_best(texto_lower, idx_prov, max_items=MAX_PROVEEDORES)

    anios = _extraer_anios(texto_lower)
    meses_nombre = _extraer_meses_nombre(texto_lower)
    meses_yyyymm = _extraer_meses_yyyymm(texto_lower)

    # ==========================================================
    # PROVEEDOR (CLAVE): igual que COMPRAS
    # - si no lo reconoce por lista, usa proveedor_libre (tresul/biodiagnostico/etc)
    # ==========================================================
    proveedor_libre = None
    if not provs:
        proveedor_libre = _extraer_proveedor_libre_comparativas(texto_lower)

    proveedor_final = provs[0] if provs else proveedor_libre

    if not proveedor_final:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "No reconocí el proveedor. Probá: comparar compras tresul 2023 2024 | comparar compras biodiagnostico 2024 2025",
            "debug": "comparar: proveedor no reconocido",
        }

    # ==========================================================
    # FUNCIÓN 1: COMPARAR PROVEEDOR MESES (YYYY-MM)
    # ==========================================================
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

    # ==========================================================
    # FUNCIÓN 2: COMPARAR PROVEEDOR MESES (nombre + año)
    # ==========================================================
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

    # Si dio 2 meses sin año
    if len(meses_nombre) >= 2 and len(anios) == 0:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": f"Para comparar meses necesito el año. Probá: comparar compras {proveedor_final} {meses_nombre[0]} {meses_nombre[1]} 2025",
            "debug": "comparar: meses sin año",
        }

    # ==========================================================
    # FUNCIÓN 3: COMPARAR PROVEEDOR AÑOS
    # ==========================================================
    if len(anios) >= 2:
        return {
            "tipo": "comparar_proveedor_anios",
            "parametros": {
                "proveedor": proveedor_final,
                "anios": [anios[0], anios[1]],
                "label1": str(anios[0]),
                "label2": str(anios[1]),
            },
            "debug": "comparar proveedor años",
        }

    # Si hay 1 solo año (tu regla: no se puede comparar con 1)
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
        "sugerencia": f"Probá: comparar compras {proveedor_final} junio julio 2025 | comparar compras {proveedor_final} 2023 2024",
        "debug": "comparar: faltan meses/año",
    }
