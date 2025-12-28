# =========================
# DIAGNÓSTICO GENERAL - FERTICHAT
# =========================

import streamlit as st
from diagnostico_queries import (
    mostrar_debug_real,
    mostrar_proveedores_similares,
    mostrar_meses_disponibles,
    mostrar_cruce_proveedor_mes
)

st.set_page_config(page_title="Diagnóstico Fertichat", layout="wide")

st.title("🔬 Diagnóstico de Consultas - Fertichat")
st.write(
    "Este módulo muestra **exactamente qué entendió la app**, "
    "qué SQL ejecutó y por qué una consulta puede no devolver resultados."
)

st.divider()

# =====================================================
# BLOQUE PRINCIPAL
# =====================================================
if "debug" not in st.session_state:
    st.warning("⚠️ No hay información de debug. Ejecutá primero una consulta en la app.")
else:
    debug = st.session_state.debug

    # -------------------------
    # DEBUG REAL
    # -------------------------
    mostrar_debug_real(debug)

    st.divider()

    # -------------------------
    # PROVEEDORES SIMILARES
    # -------------------------
    proveedor = debug.get("proveedor")
    if proveedor:
        mostrar_proveedores_similares(proveedor)

    st.divider()

    # -------------------------
    # MESES DISPONIBLES
    # -------------------------
    mostrar_meses_disponibles()

    st.divider()

    # -------------------------
    # CRUCE PROVEEDOR / MES
    # -------------------------
    if proveedor:
        mostrar_cruce_proveedor_mes(proveedor)

    st.success(
        "✅ Diagnóstico completo.\n\n"
        "Acá podés ver si el problema es:\n"
        "- detección del proveedor\n"
        "- formato de mes/año\n"
        "- SQL demasiado restrictivo\n"
        "- o ausencia real de datos"
    )
