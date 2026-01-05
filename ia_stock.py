# =========================
# IA_STOCK.PY - INTÉRPRETE STOCK (CANÓNICO)
# =========================

import os
import re
import unicodedata
from typing import Dict, List, Tuple

import streamlit as st

MAX_ARTICULOS = 5

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
    articulos: List[str] = []

    try:
        from supabase_client import supabase  # type: ignore
        if supabase is None:
            return {"articulos": []}

        for col in ["Descripción", "Descripcion", "descripcion", "DESCRIPCION", "DESCRIPCIÓN"]:
            try:
                res = supabase.table("articulos").select(col).execute()
                data = res.data or []
                articulos = [str(r.get(col)).strip() for r in data if r.get(col)]
                if articulos:
                    break
            except Exception:
                continue

    except Exception:
        return {"articulos": []}

    articulos = sorted(list(set([a for a in articulos if a])))
    return {"articulos": articulos}

def _get_art_index() -> List[Tuple[str, str]]:
    listas = _cargar_listas_supabase()
    return [(a, _key(a)) for a in (listas.get("articulos") or []) if a]

def _match_best(texto: str, index: List[Tuple[str, str]], max_items: int = 1) -> List[str]:
    toks = _tokens(texto)
    if not toks or not index:
        return []

    toks_set = set(toks)
    for orig, norm in index:
        if norm in toks_set:
            return [orig]

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
# INTÉRPRETE STOCK
# =====================================================================
def interpretar_stock(pregunta: str) -> Dict:
    texto = (pregunta or "").strip()
    texto_lower = texto.lower().strip()

    art_index = _get_art_index()
    arts = _match_best(texto_lower, art_index, max_items=MAX_ARTICULOS)

    if "stock" in texto_lower:
        if arts:
            return {
                "tipo": "stock_articulo",
                "parametros": {"articulo": arts[0]},
                "debug": "stock articulo",
            }
        return {"tipo": "stock_total", "parametros": {}, "debug": "stock total"}

    return {
        "tipo": "no_entendido",
        "parametros": {},
        "sugerencia": "Probá: stock total | stock vitek",
        "debug": "stock: no match",
    }
