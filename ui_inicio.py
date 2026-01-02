# =========================
# UI_INICIO.PY - CON TARJETAS QUE SÍ FUNCIONAN
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
    # TARJETAS CON BOTONES DE STREAMLIT (SÍ FUNCIONAN)
    # =========================
    
    st.markdown('<div style="max-width:1100px;margin:0 auto;">', unsafe_allow_html=True)
    
    # MÓDULOS PRINCIPALES
    st.markdown('<div style="color:#64748b;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1px;margin:18px 0 10px 6px;">📌 MÓDULOS PRINCIPALES</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🛒 Compras IA\nConsultas inteligentes", use_container_width=True, key="btn_compras"):
            st.session_state["radio_menu"] = "🛒 Compras IA"
            st.rerun()
    
    with col2:
        if st.button("🔎 Buscador IA\nBuscar facturas / lotes", use_container_width=True, key="btn_buscador"):
            st.session_state["radio_menu"] = "🔎 Buscador IA"
            st.rerun()
    
    with col3:
        if st.button("📦 Stock IA\nConsultar inventario", use_container_width=True, key="btn_stock"):
            st.session_state["radio_menu"] = "📦 Stock IA"
            st.rerun()
    
    with col4:
        if st.button("📊 Dashboard\nVer estadísticas", use_container_width=True, key="btn_dashboard"):
            st.session_state["radio_menu"] = "📊 Dashboard"
            st.rerun()

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # GESTIÓN
    st.markdown('<div style="color:#64748b;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1px;margin:18px 0 10px 6px;">📋 GESTIÓN</div>', unsafe_allow_html=True)
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        if st.button("📄 Pedidos internos\nGestionar pedidos", use_container_width=True, key="btn_pedidos"):
            st.session_state["radio_menu"] = "📄 Pedidos internos"
            st.rerun()
    
    with col6:
        if st.button("🧾 Baja de stock\nRegistrar bajas", use_container_width=True, key="btn_baja"):
            st.session_state["radio_menu"] = "🧾 Baja de stock"
            st.rerun()
    
    with col7:
        if st.button("📦 Órdenes de compra\nCrear órdenes", use_container_width=True, key="btn_ordenes"):
            st.session_state["radio_menu"] = "📦 Órdenes de compra"
            st.rerun()
    
    with col8:
        if st.button("📈 Indicadores\nPower BI", use_container_width=True, key="btn_indicadores"):
            st.session_state["radio_menu"] = "📈 Indicadores (Power BI)"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # CSS PARA LOS BOTONES
    # =========================
    st.markdown("""
        <style>
        /* Botones de inicio con estilo de tarjetas */
        div[data-testid="column"] > div > div > button {
            height: 90px !important;
            padding: 14px !important;
            background: rgba(255,255,255,0.75) !important;
            border: 1px solid rgba(15,23,42,0.10) !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 20px rgba(2,6,23,0.06) !important;
            color: #0f172a !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            line-height: 1.3 !important;
            text-align: left !important;
            white-space: pre-line !important;
            transition: all 0.15s ease !important;
        }
        
        div[data-testid="column"] > div > div > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 12px 28px rgba(2,6,23,0.10) !important;
            border-color: rgba(37,99,235,0.25) !important;
            background: rgba(255,255,255,0.90) !important;
        }
        
        div[data-testid="column"] > div > div > button:active {
            transform: translateY(0) !important;
        }

        /* Responsive - móvil en 2 columnas */
        @media (max-width: 768px) {
            div[data-testid="column"] {
                min-width: 48% !important;
                flex: 0 0 48% !important;
            }
            
            div[data-testid="column"] > div > div > button {
                height: 85px !important;
                font-size: 14px !important;
                padding: 12px !important;
            }
        }

        /* Móvil muy pequeño - 1 columna */
        @media (max-width: 500px) {
            div[data-testid="column"] {
                min-width: 100% !important;
                flex: 0 0 100% !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

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
        <div style="max-width:1100px;margin:20px auto 0 auto;">
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
