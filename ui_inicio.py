# =========================
# UI_INICIO.PY - PANTALLA DE INICIO CON ACCESOS RÁPIDOS (CORPORATIVO)
# TARJETAS HERMOSAS CON BOTONES STREAMLIT CONFIABLES
# =========================

import streamlit as st
from datetime import datetime
import random


def mostrar_inicio():
    """Pantalla de inicio con accesos rápidos a los módulos (look corporativo)"""

    # =========================
    # Datos usuario / saludo
    # =========================
    user = st.session_state.get("user", {})
    nombre = user.get("nombre", "Usuario")

    hora = datetime.now().hour
    if hora < 12:
        saludo = "¡Buenos días"
    elif hora < 19:
        saludo = "¡Buenas tardes"
    else:
        saludo = "¡Buenas noches"

    # =========================
    # Header (saludo)
    # =========================
    st.markdown(
        f"""
        <div style="max-width:1100px;margin:0 auto;text-align:center;padding:10px 0 18px 0;">
            <h2 style="margin:0;color:#0f172a;font-size:34px;font-weight:800;letter-spacing:-0.02em;">
                {saludo}, {nombre.split()[0]}! 👋
            </h2>
            <p style="margin:8px 0 0 0;color:#64748b;font-size:16px;">
                ¿Qué querés hacer hoy?
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================
    # CSS PARA TARJETAS HERMOSAS
    # =========================
    st.markdown("""
    <style>
      .fc-section-title{
        color:#64748b;font-size:12px;font-weight:800;text-transform:uppercase;
        letter-spacing:1px;margin:18px 0 10px 6px;display:flex;align-items:center;gap:8px;
      }
      
      /* Ocultar labels y resetear botones */
      div[data-testid="column"] button[kind="secondary"] {
        border: 1px solid rgba(15,23,42,0.10) !important;
        background: rgba(255,255,255,0.72) !important;
        border-radius: 18px !important;
        padding: 0 !important;
        box-shadow: 0 10px 26px rgba(2,6,23,0.06) !important;
        cursor: pointer !important;
        transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease !important;
        user-select: none !important;
        width: 100% !important;
        height: 90px !important;
        text-align: left !important;
        color: #0f172a !important;
      }
      
      div[data-testid="column"] button[kind="secondary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 14px 34px rgba(2,6,23,0.09) !important;
        border-color: rgba(37,99,235,0.20) !important;
      }
      
      div[data-testid="column"] button[kind="secondary"]:active {
        transform: translateY(0) !important;
        box-shadow: 0 10px 26px rgba(2,6,23,0.06) !important;
      }

      div[data-testid="column"] button[kind="secondary"] p {
        margin: 0 !important;
        padding: 16px !important;
        font-size: 14px !important;
        line-height: 1.4 !important;
        text-align: left !important;
      }

      @media (max-width: 768px) {
        div[data-testid="column"] button[kind="secondary"] {
          height: 85px !important;
        }
        div[data-testid="column"] button[kind="secondary"] p {
          padding: 14px !important;
          font-size: 13px !important;
        }
      }
    </style>
    """, unsafe_allow_html=True)

    # =========================
    # MÓDULOS PRINCIPALES
    # =========================
    st.markdown('<div class="fc-section-title">📌 Módulos principales</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🛒 **Compras IA**\n\nConsultas inteligentes", key="card_compras", type="secondary", use_container_width=True):
            st.session_state["radio_menu"] = "🛒 Compras IA"
            st.rerun()
    
    with col2:
        if st.button("🔎 **Buscador IA**\n\nBuscar facturas / lotes", key="card_buscador", type="secondary", use_container_width=True):
            st.session_state["radio_menu"] = "🔎 Buscador IA"
            st.rerun()
    
    with col3:
        if st.button("📦 **Stock IA**\n\nConsultar inventario", key="card_stock", type="secondary", use_container_width=True):
            st.session_state["radio_menu"] = "📦 Stock IA"
            st.rerun()
    
    with col4:
        if st.button("📊 **Dashboard**\n\nVer estadísticas", key="card_dashboard", type="secondary", use_container_width=True):
            st.session_state["radio_menu"] = "📊 Dashboard"
            st.rerun()

    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)

    # =========================
    # GESTIÓN
    # =========================
    st.markdown('<div class="fc-section-title">📋 Gestión</div>', unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        if st.button("📄 **Pedidos internos**\n\nGestionar pedidos", key="card_pedidos", type="secondary", use_container_width=True):
            st.session_state["radio_menu"] = "📄 Pedidos internos"
            st.rerun()
    
    with col6:
        if st.button("🧾 **Baja de stock**\n\nRegistrar bajas", key="card_baja", type="secondary", use_container_width=True):
            st.session_state["radio_menu"] = "🧾 Baja de stock"
            st.rerun()
    
    with col7:
        if st.button("📦 **Órdenes de compra**\n\nCrear órdenes", key="card_ordenes", type="secondary", use_container_width=True):
            st.session_state["radio_menu"] = "📦 Órdenes de compra"
            st.rerun()
    
    with col8:
        if st.button("📈 **Indicadores**\n\nPower BI", key="card_indicadores", type="secondary", use_container_width=True):
            st.session_state["radio_menu"] = "📈 Indicadores (Power BI)"
            st.rerun()

    # =========================
    # TIP DEL DÍA
    # =========================
    tips = [
        "💡 Escribí 'compras roche 2025' para ver todas las compras a Roche este año",
        "💡 Usá 'lotes por vencer' en Stock IA para ver vencimientos próximos",
        "💡 Probá 'comparar roche 2024 2025' para ver la evolución de compras",
        "💡 En el Buscador podés filtrar por proveedor, artículo y fechas",
        "💡 Usá 'top 10 proveedores 2025' para ver el ranking de compras",
    ]
    tip = random.choice(tips)

    st.markdown(
        f"""
        <div style="max-width:1100px;margin:16px auto 0 auto;">
            <div style="
                background: rgba(255,255,255,0.70);
                border: 1px solid rgba(15,23,42,0.10);
                border-left: 4px solid rgba(37,99,235,0.55);
                border-radius: 16px;
                padding: 14px 16px;
                box-shadow: 0 10px 26px rgba(2,6,23,0.06);
            ">
                <p style="margin:0;color:#0b3b60;font-size:14px;font-weight:600;">
                    {tip}
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
