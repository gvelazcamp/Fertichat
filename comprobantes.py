# =====================================================================
# 📑 MÓDULO COMPROBANTES - FERTI CHAT
# Archivo: comprobantes.py
# =====================================================================

import streamlit as st

# =====================================================================
# ALTA DE STOCK
# =====================================================================

def mostrar_comprobante_alta_stock():
    st.subheader("⬆️ Alta de stock")

    deposito_destino = st.selectbox(
        "Depósito destino",
        ["Casa Central", "ANDA", "Platinum"]
    )

    st.markdown("### Artículos")
    st.info("Acá luego se cargan artículos, lote, vencimiento y cantidad")


# =====================================================================
# BAJA DE STOCK
# =====================================================================

def mostrar_comprobante_baja_stock():
    st.subheader("⬇️ Baja de stock")

    deposito_origen = st.selectbox(
        "Depósito origen",
        ["Casa Central", "ANDA", "Platinum"]
    )

    motivo = st.selectbox(
        "Motivo de baja",
        ["Salida no declarada", "Rotura", "Pérdida", "Recuento", "Otro"]
    )

    st.markdown("### Artículos")
    st.info("Se bajará siempre el lote más próximo a vencer (FIFO)")


# =====================================================================
# MOVIMIENTO ENTRE DEPÓSITOS
# =====================================================================

def mostrar_comprobante_movimiento():
    st.subheader("🔁 Movimiento entre depósitos")

    col1, col2 = st.columns(2)

    with col1:
        deposito_origen = st.selectbox(
            "Depósito origen",
            ["Casa Central", "ANDA", "Platinum"]
        )

    with col2:
        deposito_destino = st.selectbox(
            "Depósito destino",
            ["Casa Central", "ANDA", "Platinum"]
        )

    st.markdown("### Artículos")
    st.info("Movimiento de mercadería entre depósitos con control de lote")


# =====================================================================
# BAJA POR VENCIMIENTO
# =====================================================================

def mostrar_comprobante_baja_vencimiento():
    st.subheader("⏰ Baja por vencimiento")

    deposito_origen = st.selectbox(
        "Depósito",
        ["Casa Central", "ANDA", "Platinum"]
    )

    st.warning("Solo se permiten artículos vencidos")


# =====================================================================
# AJUSTE POR RECUENTO (ALTA / BAJA)
# =====================================================================

def mostrar_comprobante_ajuste_recuento():
    st.subheader("⚖️ Ajuste por recuento")

    deposito = st.selectbox(
        "Depósito",
        ["Casa Central", "ANDA", "Platinum"]
    )

    tipo_ajuste = st.radio(
        "Tipo de ajuste",
        ["Alta", "Baja"],
        horizontal=True
    )

    st.markdown("### Artículos")
    st.info("Permite ajustar stock real contra sistema")


# =====================================================================
# MENÚ PRINCIPAL COMPROBANTES
# =====================================================================

def mostrar_menu_comprobantes():

    st.title("📑 Comprobantes")

    opcion = st.radio(
        "Tipo de comprobante",
        [
            "⬆️ Alta de stock",
            "⬇️ Baja de stock",
            "🔁 Movimiento entre depósitos",
            "⏰ Baja por vencimiento",
            "⚖️ Ajuste por recuento"
        ]
    )

    if opcion == "⬆️ Alta de stock":
        mostrar_comprobante_alta_stock()

    elif opcion == "⬇️ Baja de stock":
        mostrar_comprobante_baja_stock()

    elif opcion == "🔁 Movimiento entre depósitos":
        mostrar_comprobante_movimiento()

    elif opcion == "⏰ Baja por vencimiento":
        mostrar_comprobante_baja_vencimiento()

    elif opcion == "⚖️ Ajuste por recuento":
        mostrar_comprobante_ajuste_recuento()
