# =========================
# IA_INTERPRETADOR.PY
# =========================

import re
from typing import Dict, Optional, List

import streamlit as st

# =====================================================================
# MAPA DE MESES
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
# CATÁLOGOS DESDE TU SQL (YA EXISTENTE)
# =====================================================================

@st.cache_data(ttl=3600)
def get_lista_proveedores() -> List[str]:
    """
    Devuelve lista de proveedores desde Supabase
    """
    from sql_queries import get_proveedores  # FUNCIÓN REAL TUYA
    df = get_proveedores()
    return [p.lower() for p in df["proveedor"].dropna().unique()]


@st.cache_data(ttl=3600)
def get_lista_articulos() -> List[str]:
    """
    Devuelve lista de artículos desde Supabase
    """
    from sql_queries import get_articulos  # FUNCIÓN REAL TUYA
    df = get_articulos()
    return [a.lower() for a in df["articulo"].dropna().unique()]


# =====================================================================
# DETECTORES
# =====================================================================

def detectar_proveedor(texto: str, proveedores: List[str]) -> Optional[str]:
    for p in proveedores:
        if p in texto:
            return p
    return None


def detectar_articulo(texto: str, articulos: List[str]) -> Optional[str]:
    for a in articulos:
        if a in texto:
            return a
    return None


def detectar_mes(texto: str) -> Optional[str]:
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
            "debug": "pregunta vacía"
        }

    texto = pregunta.lower().strip()

    # -------------------------
    # SALUDOS
    # -------------------------
    if texto in ["hola", "buenos dias", "buenas", "gracias", "chau"]:
        return {
            "tipo": "conversacion",
            "parametros": {},
            "debug": "saludo"
        }

    proveedores = get_lista_proveedores()
    articulos = get_lista_articulos()

    proveedor = detectar_proveedor(texto, proveedores)
    articulo = detectar_articulo(texto, articulos)
    mes = detectar_mes(texto)

    # ==========================================================
    # COMPRAS PROVEEDOR + MES
    # Ej: "compras roche noviembre 2025"
    # ==========================================================
    if "compra" in texto and proveedor and mes:
        return {
            "tipo": "compras_proveedor_mes",
            "parametros": {
                "proveedor": proveedor,
                "mes": mes
            },
            "debug": "proveedor + mes (directo)"
        }

    # ==========================================================
    # COMPRAS PROVEEDOR + AÑO
    # ==========================================================
    if "compra" in texto and proveedor:
        anio_match = re.search(r"(2023|2024|2025|2026)", texto)
        if anio_match:
            return {
                "tipo": "compras_proveedor_anio",
                "parametros": {
                    "proveedor": proveedor,
                    "anio": int(anio_match.group(1))
                },
                "debug": "proveedor + año"
            }

    # ==========================================================
    # COMPARAR PROVEEDOR MESES
    # ==========================================================
    if "comparar" in texto and proveedor:
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
                    "mes2": mes2
                },
                "debug": "comparar proveedor meses"
            }

    # ==========================================================
    # STOCK ARTÍCULO
    # ==========================================================
    if "stock" in texto and articulo:
        return {
            "tipo": "stock_articulo",
            "parametros": {
                "articulo": articulo
            },
            "debug": "stock articulo"
        }

    # ==========================================================
    # FALLBACK
    # ==========================================================
    return {
        "tipo": "no_entendido",
        "parametros": {},
        "sugerencia": "Probá: compras roche noviembre 2025",
        "debug": "sin match"
    }
