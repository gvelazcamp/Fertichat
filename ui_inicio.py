# =========================
# UI_INICIO.PY - PANTALLA DE INICIO CON ACCESOS RÁPIDOS
# SOLUCIÓN DEFINITIVA CON BOTONES FUNCIONALES
# =========================

import streamlit as st
from datetime import datetime
import random


def mostrar_inicio():
    """Pantalla de inicio con accesos rápidos a los módulos"""

    # =========================
    # SISTEMA DE NAVEGACIÓN CON CLICKS
    # =========================
    if "nav_click" not in st.session_state:
        st.session_state["nav_click"] = None

    # Si hay un click pendiente, navegar AHORA
    if st.session_state["nav_click"]:
        destino = st.session_state["nav_click"]
        st.session_state["nav_click"] = None
        st.session_state["radio_menu"] = destino
        st.rerun()

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
    # CSS PARA TARJETAS CON BOTONES INVISIBLES
    # =========================
    st.markdown("""
    <style>
        .card-container {
            position: relative;
            border: 1px solid rgba(15,23,42,0.10);
            background: rgba(255,255,255,0.72);
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 10px 26px rgba(2,6,23,0.06);
            transition: all 140ms ease;
            height: 90px;
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 8px;
        }
        
        .card-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 34px rgba(2,6,23,0.09);
            border-color: rgba(37,99,235,0.20);
        }
        
        /* Ocultar botón pero mantener área clickeable */
        [data-testid="column"] .element-container button {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            z-index: 100 !important;
            background: transparent !important;
            border: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # =========================
    # MÓDULOS PRINCIPALES
    # =========================
    st.markdown('<p style="color:#64748b;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1px;margin:18px 0 10px 6px;">📌 MÓDULOS PRINCIPALES</p>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="card-container">
            <div style="width:54px;height:54px;border-radius:16px;display:flex;align-items:center;justify-content:center;
                        background:rgba(16,185,129,0.10);border:1px solid rgba(16,185,129,0.18);">
                <div style="font-size:26px;">🛒</div>
            </div>
            <div>
                <h3 style="margin:0;color:#0f172a;font-size:16px;font-weight:800;">Compras IA</h3>
                <p style="margin:3px 0 0 0;color:#64748b;font-size:13px;">Consultas inteligentes</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="nav_compras"):
            st.session_state["nav_click"] = "🛒 Compras IA"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="card-container">
            <div style="width:54px;height:54px;border-radius:16px;display:flex;align-items:center;justify-content:center;
                        background:rgba(59,130,246,0.10);border:1px solid rgba(59,130,246,0.18);">
                <div style="font-size:26px;">🔎</div>
            </div>
            <div>
                <h3 style="margin:0;color:#0f172a;font-size:16px;font-weight:800;">Buscador IA</h3>
                <p style="margin:3px 0 0 0;color:#64748b;font-size:13px;">Buscar facturas / lotes</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="nav_buscador"):
            st.session_state["nav_click"] = "🔎 Buscador IA"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="card-container">
            <div style="width:54px;height:54px;border-radius:16px;display:flex;align-items:center;justify-content:center;
                        background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.22);">
                <div style="font-size:26px;">📦</div>
            </div>
            <div>
                <h3 style="margin:0;color:#0f172a;font-size:16px;font-weight:800;">Stock IA</h3>
                <p style="margin:3px 0 0 0;color:#64748b;font-size:13px;">Consultar inventario</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="nav_stock"):
            st.session_state["nav_click"] = "📦 Stock IA"
            st.rerun()

    with col4:
        st.markdown("""
        <div class="card-container">
            <div style="width:54px;height:54px;border-radius:16px;display:flex;align-items:center;justify-content:center;
                        background:rgba(139,92,246,0.10);border:1px solid rgba(139,92,246,0.18);">
                <div style="font-size:26px;">📊</div>
            </div>
            <div>
                <h3 style="margin:0;color:#0f172a;font-size:16px;font-weight:800;">Dashboard</h3>
                <p style="margin:3px 0 0 0;color:#64748b;font-size:13px;">Ver estadísticas</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="nav_dashboard"):
            st.session_state["nav_click"] = "📊 Dashboard"
            st.rerun()

    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)

    # =========================
    # GESTIÓN
    # =========================
    st.markdown('<p style="color:#64748b;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1px;margin:18px 0 10px 6px;">📋 GESTIÓN</p>', unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.markdown("""
        <div class="card-container">
            <div style="width:54px;height:54px;border-radius:16px;display:flex;align-items:center;justify-content:center;
                        background:rgba(2,132,199,0.10);border:1px solid rgba(2,132,199,0.18);">
                <div style="font-size:26px;">📄</div>
            </div>
            <div>
                <h3 style="margin:0;color:#0f172a;font-size:16px;font-weight:800;">Pedidos internos</h3>
                <p style="margin:3px 0 0 0;color:#64748b;font-size:13px;">Gestionar pedidos</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="nav_pedidos"):
            st.session_state["nav_click"] = "📄 Pedidos internos"
            st.rerun()

    with col6:
        st.markdown("""
        <div class="card-container">
            <div style="width:54px;height:54px;border-radius:16px;display:flex;align-items:center;justify-content:center;
                        background:rgba(244,63,94,0.10);border:1px solid rgba(244,63,94,0.18);">
                <div style="font-size:26px;">🧾</div>
            </div>
            <div>
                <h3 style="margin:0;color:#0f172a;font-size:16px;font-weight:800;">Baja de stock</h3>
                <p style="margin:3px 0 0 0;color:#64748b;font-size:13px;">Registrar bajas</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="nav_baja"):
            st.session_state["nav_click"] = "🧾 Baja de stock"
            st.rerun()

    with col7:
        st.markdown("""
        <div class="card-container">
            <div style="width:54px;height:54px;border-radius:16px;display:flex;align-items:center;justify-content:center;
                        background:rgba(100,116,139,0.10);border:1px solid rgba(100,116,139,0.18);">
                <div style="font-size:26px;">📦</div>
            </div>
            <div>
                <h3 style="margin:0;color:#0f172a;font-size:16px;font-weight:800;">Órdenes de compra</h3>
                <p style="margin:3px 0 0 0;color:#64748b;font-size:13px;">Crear órdenes</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="nav_ordenes"):
            st.session_state["nav_click"] = "📦 Órdenes de compra"
            st.rerun()

    with col8:
        st.markdown("""
        <div class="card-container">
            <div style="width:54px;height:54px;border-radius:16px;display:flex;align-items:center;justify-content:center;
                        background:rgba(34,197,94,0.10);border:1px solid rgba(34,197,94,0.18);">
                <div style="font-size:26px;">📈</div>
            </div>
            <div>
                <h3 style="margin:0;color:#0f172a;font-size:16px;font-weight:800;">Indicadores</h3>
                <p style="margin:3px 0 0 0;color:#64748b;font-size:13px;">Power BI</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("", key="nav_indicadores"):
            st.session_state["nav_click"] = "📈 Indicadores (Power BI)"
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
