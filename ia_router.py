# =========================
# IA_ROUTER.PY - ROUTER (COMPRAS / COMPARATIVAS / STOCK)
# =========================

import os
import re
from typing import Dict, Optional

import streamlit as st
from openai import OpenAI
from config import OPENAI_MODEL

# Import CANÓNICO (alias para evitar recursión por nombre)
from ia_interpretador import (
    interpretar_pregunta as interpretar_canonico,
    obtener_info_tipo as obtener_info_tipo_canonico,
    es_tipo_valido as es_tipo_valido_canonico,
)

from ia_comparativas import interpretar_comparativas

# =====================================================================
# CONFIGURACIÓN OPENAI (opcional)
# =====================================================================
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

USAR_OPENAI_PARA_DATOS = False

# =====================================================================
# (Opcional) info tipo desde comparativas si existe
# =====================================================================
try:
    from ia_comparativas import obtener_info_tipo as obtener_info_tipo_comparativas  # type: ignore
except Exception:
    obtener_info_tipo_comparativas = None  # type: ignore

try:
    from ia_comparativas import es_tipo_valido as es_tipo_valido_comparativas  # type: ignore
except Exception:
    es_tipo_valido_comparativas = None  # type: ignore


# =====================================================================
# ROUTER PRINCIPAL
# =====================================================================
def interpretar_pregunta(pregunta: str) -> Dict:
    """
    Router principal:
    - Comparativas -> ia_comparativas.interpretar_comparativas
    - Todo lo demás (compras, facturas, stock, etc.) -> ia_interpretador.interpretar_pregunta (CANÓNICO)
    """
    if not pregunta or not str(pregunta).strip():
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "Escribe una consulta.",
            "debug": "Pregunta vacía.",
        }

    texto = str(pregunta).strip()
    texto_lower = texto.lower().strip()

    # Comparativas (prioridad)
    if re.search(r"\b(comparar|comparame|compara)\b", texto_lower):
        return interpretar_comparativas(texto)

    # Default: CANÓNICO
    return interpretar_canonico(texto)


# =====================================================================
# MAPEO TIPO → FUNCIÓN SQL (delegado a canónico / comparativas)
# =====================================================================
def obtener_info_tipo(tipo: str) -> Optional[Dict]:
    info = None
    try:
        info = obtener_info_tipo_canonico(tipo)
    except Exception:
        info = None

    if info is not None:
        return info

    if callable(obtener_info_tipo_comparativas):
        try:
            return obtener_info_tipo_comparativas(tipo)
        except Exception:
            return None

    return None


def es_tipo_valido(tipo: str) -> bool:
    try:
        if es_tipo_valido_canonico(tipo):
            return True
    except Exception:
        pass

    if callable(es_tipo_valido_comparativas):
        try:
            return bool(es_tipo_valido_comparativas(tipo))
        except Exception:
            return False

    return False
