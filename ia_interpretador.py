# =========================
# IA_INTERPRETADOR.PY
# =========================

import os
import re
import json
from typing import Dict, Optional
from datetime import datetime

import streamlit as st
from openai import OpenAI
from config import OPENAI_MODEL

# =====================================================================
# CONFIGURACIÓN OPENAI
# =====================================================================

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =====================================================================
# MAPA DE MESES (FORMATO CANÓNICO YYYY-MM)
# =====================================================================

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
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}

ANIOS_VALIDOS = ["2023", "2024", "2025", "2026"]

# =====================================================================
# CATÁLOGOS DESDE SUPABASE (CACHEADOS)
# =====================================================================

@st.cache_data(ttl=3600)
def get_lista_proveedores() -> list[str]:
    """
    Devuelve proveedores desde Supabase (columna: nombre)
    """
    from sql_queries import get_proveedores  # SQL EXISTENTE
    df = get_proveedores()
    return [p.lower() for p in df["nombre"].dropna().unique()]


@st.cache_data(ttl=3600)
def get_lista_articulos() -> list[str]:
    """
    Devuelve artículos desde Supabase (columna: descripcion)
    """
    from sql_queries import get_articulos  # SQL EXISTENTE
    df = get_articulos()
    return [a.lower() for a in df["descripcion"].dropna().unique()]


def detectar_proveedor(texto: str, proveedores: list[str]) -> Optional[str]:
    for p in proveedores:
        if p in texto:
            return p
    return None


def detectar_articulo(texto: str, articulos: list[str]) -> Optional[str]:
    for a in articulos:
        if a in texto:
            return a
    return None


def detectar_mes_y_anio(texto: str) -> Optional[str]:
    meses_en_texto = [m for m in MESES if m in texto]
    anio_match = re.search(r"(2023|2024|2025|2026)", texto)

    if len(meses_en_texto) == 1 and anio_match:
        mes = MESES[meses_en_texto[0]]
        anio = anio_match.group(1)
        return f"{anio}-{mes}"

    return None

# =====================================================================
# FUNCIÓN PRINCIPAL
# =====================================================================

def interpretar_pregunta(pregunta: str) -> Dict:
    if not pregunta or not pregunta.strip():
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "Escribí una consulta válida.",
            "debug": "pregunta vacía",
        }

    texto = pregunta.lower().strip()

    # ==========================================================
    # SALUDOS
    # ==========================================================
    if texto in ["hola", "buenos dias", "buenas", "gracias", "chau"]:
        return {
            "tipo": "conversacion",
            "parametros": {},
            "debug": "saludo simple",
        }

    # ==========================================================
    # CARGA DE CATÁLOGOS
    # ==========================================================
    proveedores = get_lista_proveedores()
    articulos = get_lista_articulos()

    proveedor = detectar_proveedor(texto, proveedores)
    articulo = detectar_articulo(texto, articulos)
    mes = detectar_mes_y_anio(texto)

    # ==========================================================
    # REGLA DIRECTA: COMPRAS PROVEEDOR + MES
    # Ej: "compras roche noviembre 2025"
    # ==========================================================
    if proveedor and mes and "compra" in texto:
        return {
            "tipo": "compras_proveedor_mes",
            "parametros": {
                "proveedor": proveedor,
                "mes": mes,
            },
            "debug": "regla directa proveedor + mes (supabase)",
        }

    # ==========================================================
    # REGLA DIRECTA: COMPRAS PROVEEDOR + AÑO
    # ==========================================================
    if proveedor and "compra" in texto:
        anio_match = re.search(r"(2023|2024|2025|2026)", texto)
        if anio_match:
            return {
                "tipo": "compras_proveedor_anio",
                "parametros": {
                    "proveedor": proveedor,
                    "anio": int(anio_match.group(1)),
                },
                "debug": "regla directa proveedor + año",
            }

    # ==========================================================
    # REGLA DIRECTA: COMPARAR PROVEEDOR MESES
    # Ej: "comparar compras roche junio julio 2025"
    # ==========================================================
    if proveedor and "comparar" in texto:
        meses_en_texto = [m for m in MESES if m in texto]
        anio_match = re.search(r"(2023|2024|2025|2026)", texto)

        if len(meses_en_texto) == 2 and anio_match:
            anio = anio_match.group(1)
            mes1 = f"{anio}-{MESES[meses_en_texto[0]]}"
            mes2 = f"{anio}-{MESES[meses_en_texto[1]]}"

            return {
                "tipo": "comparar_proveedor_meses",
                "parametros": {
                    "proveedor": proveedor,
                    "mes1": mes1,
                    "mes2": mes2,
                    "label1": f"{meses_en_texto[0]} {anio}",
                    "label2": f"{meses_en_texto[1]} {anio}",
                },
                "debug": "comparar proveedor meses (regla directa)",
            }

    # ==========================================================
    # STOCK ARTÍCULO
    # ==========================================================
    if articulo and "stock" in texto:
        return {
            "tipo": "stock_articulo",
            "parametros": {"articulo": articulo},
            "debug": "stock articulo directo",
        }

    # ==========================================================
    # FALLBACK A OPENAI (SOLO SI NO HUBO MATCH)
    # ==========================================================
    if not client:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "Probá con: compras roche noviembre 2025",
            "debug": "sin openai",
        }

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Devolvé SOLO JSON válido."},
                {"role": "user", "content": pregunta},
            ],
            temperature=0.1,
            max_tokens=300,
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"```json|```", "", content).strip()
        return json.loads(content)

    except Exception as e:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "No pude interpretar la consulta.",
            "debug": f"openai error: {str(e)[:80]}",
        }

# =====================================================================
# MAPEO TIPO → SQL
# =====================================================================

MAPEO_FUNCIONES = {
    "compras_proveedor_mes": {
        "funcion": "get_detalle_compras_proveedor_mes",
        "params": ["proveedor", "mes"],
    },
    "compras_proveedor_anio": {
        "funcion": "get_detalle_compras_proveedor_anio",
        "params": ["proveedor", "anio"],
    },
    "comparar_proveedor_meses": {
        "funcion": "get_comparacion_proveedor_meses",
        "params": ["proveedor", "mes1", "mes2", "label1", "label2"],
    },
    "stock_articulo": {
        "funcion": "get_stock_articulo",
        "params": ["articulo"],
    },
}

def obtener_info_tipo(tipo: str) -> Optional[Dict]:
    return MAPEO_FUNCIONES.get(tipo)

def es_tipo_valido(tipo: str) -> bool:
    return tipo in MAPEO_FUNCIONES or tipo in ["conversacion", "no_entendido"]
