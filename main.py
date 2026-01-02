# =========================
# MAIN.PY - VERSIÓN MÓVIL CON SELECTBOX FLOTANTE
# =========================

import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="FertiChat",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="collapsed"  # CERRADO al inicio
)

# =========================
# IMPORTS
# =========================
from config import MENU_OPTIONS, DEBUG_MODE
from auth import init_db
from login_page import require_auth, get_current_user, logout
from pedidos import mostrar_pedidos_internos, contar_notificaciones_no_leidas
from bajastock import mostrar_baja_stock
from ordenes_compra import mostrar_ordenes_compra
from ui_compras import Compras_IA
from ui_buscador import mostrar_buscador_ia
from ui_stock import mostrar_stock_ia, mostrar_resumen_stock_rotativo
from ui_dashboard import mostrar_dashboard, mostrar_indicadores_ia, mostrar_resumen_compras_rotativo
from ingreso_comprobantes import mostrar_ingreso_comprobantes
from ui_inicio import mostrar_inicio
from ficha_stock import mostrar_ficha_stock
from articulos import mostrar_articulos
from depositos import mostrar_depositos
from familias import mostrar_familias


# =========================
# CSS MEJORADO
# =========================
def inject_css():
    st.markdown(
        """
        <style>
        /* Ocultar elementos de Streamlit */
        div.stAppToolbar,
        div[data-testid="stToolbar"],
        div[data-testid="stToolbarActions"],
        div[data-testid="stDecoration"],
        #MainMenu,
        footer{
          display: none !important;
        }

        header[data-testid="stHeader"]{
          height: 0 !important;
          min-height: 0 !important;
          background: transparent !important;
        }

        /* Theme */
        :root{
            --fc-bg-1: #f6f4ef;
            --fc-bg-2: #f3f6fb;
            --fc-primary: #0b3b60;
            --fc-accent: #f59e0b;
        }

        html, body{
            font-family: Inter, system-ui, sans-serif;
            color: #0f172a;
        }

        [data-testid="stAppViewContainer"]{
            background: linear-gradient(135deg, var(--fc-bg-1), var(--fc-bg-2));
        }

        .block-container{
            max-width: 1240px;
            padding-top: 1.25rem;
            padding-bottom: 2.25rem;
        }

        /* Sidebar PC */
        section[data-testid="stSidebar"]{
            border-right: 1px solid rgba(15, 23, 42, 0.08);
        }
        section[data-testid="stSidebar"] > div{
            background: rgba(255,255,255,0.70);
            backdrop-filter: blur(8px);
        }

        div[data-testid="stSidebar"] div[role="radiogroup"] label{
            border-radius: 12px;
            padding: 8px 10px;
            margin: 3px 0;
            border: 1px solid transparent;
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
            background: rgba(37,99,235,0.06);
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
            background: rgba(245,158,11,0.10);
            border: 1px solid rgba(245,158,11,0.18);
        }

        /* ========================================
           RESPONSIVE MÓVIL - SIDEBAR PERFECTO
        ======================================== */
        @media (max-width: 768px){
            
            /* ✅ SIDEBAR - Ajustado correctamente */
            section[data-testid="stSidebar"]{
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                height: 100vh !important;
                width: 280px !important;
                max-width: 280px !important;
                z-index: 999998 !important;
                transform: translateX(-100%) !important;
                transition: transform 0.3s ease !important;
                display: block !important;
                visibility: visible !important;
                background: rgba(255,255,255,0.98) !important;
                backdrop-filter: blur(12px) !important;
                box-shadow: 8px 0 24px rgba(0,0,0,0.2) !important;
                overflow-y: auto !important;
                overflow-x: hidden !important;
            }

            /* Sidebar ABIERTO */
            section[data-testid="stSidebar"][aria-expanded="true"]{
                transform: translateX(0) !important;
            }

            /* Contenedor interno */
            section[data-testid="stSidebar"] > div{
                background: transparent !important;
                width: 100% !important;
                padding: 1rem !important;
            }

            /* TODO visible y negro */
            section[data-testid="stSidebar"] *{
                visibility: visible !important;
                opacity: 1 !important;
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }

            /* Logo/título del sidebar */
            section[data-testid="stSidebar"] h1,
            section[data-testid="stSidebar"] h2,
            section[data-testid="stSidebar"] h3{
                color: #0f172a !important;
                word-wrap: break-word !important;
            }

            /* Inputs y campos de texto */
            section[data-testid="stSidebar"] input,
            section[data-testid="stSidebar"] textarea{
                background: rgba(248,250,252,0.9) !important;
                border: 1px solid rgba(15,23,42,0.12) !important;
                color: #0f172a !important;
                width: 100% !important;
            }

            /* Botones del sidebar */
            section[data-testid="stSidebar"] button{
                width: 100% !important;
                background: rgba(248,250,252,0.9) !important;
                color: #0f172a !important;
                border: 1px solid rgba(15,23,42,0.12) !important;
            }

            /* ✅ MENÚ RADIO - Sin puntos, bien visible */
            section[data-testid="stSidebar"] div[role="radiogroup"]{
                display: flex !important;
                flex-direction: column !important;
                gap: 4px !important;
            }

            section[data-testid="stSidebar"] div[role="radiogroup"] label{
                display: flex !important;
                align-items: center !important;
                background: rgba(248,250,252,0.9) !important;
                border: 1px solid rgba(15,23,42,0.12) !important;
                border-radius: 10px !important;
                padding: 10px 12px !important;
                margin: 0 !important;
                cursor: pointer !important;
                width: 100% !important;
            }

            /* Ocultar círculo del radio */
            section[data-testid="stSidebar"] div[role="radiogroup"] div[data-baseweb="radio"]{
                display: none !important;
            }

            /* Texto del menú */
            section[data-testid="stSidebar"] div[role="radiogroup"] label > div{
                color: #0f172a !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                width: 100% !important;
                text-align: left !important;
            }

            /* Item seleccionado */
            section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
                background: rgba(245,158,11,0.18) !important;
                border-color: rgba(245,158,11,0.35) !important;
            }

            section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) > div{
                color: #0b3b60 !important;
                font-weight: 700 !important;
            }

            /* ✅ OVERLAY oscuro cuando sidebar está abierto */
            section[data-testid="stSidebar"][aria-expanded="true"]::before{
                content: "";
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: -1;
                pointer-events: auto;
            }

            /* ✅ BOTÓN HAMBURGUESA */
            button[data-testid="stExpandSidebarButton"],
            button[data-testid="stSidebarCollapsedControl"],
            button[data-testid="stSidebarCollapseButton"],
            button[data-testid="baseButton-header"],
            button[kind="header"],
            button[kind="headerNoPadding"],
            header button{
                display: flex !important;
                position: fixed !important;
                top: 10px !important;
                left: 10px !important;
                z-index: 999999 !important;
                width: 52px !important;
                height: 52px !important;
                min-width: 52px !important;
                min-height: 52px !important;
                background: #ffffff !important;
                border: 3px solid #0b3b60 !important;
                border-radius: 14px !important;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
                visibility: visible !important;
                opacity: 1 !important;
                align-items: center !important;
                justify-content: center !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            /* SVG del botón */
            button[data-testid="stExpandSidebarButton"] svg,
            button[data-testid="stSidebarCollapsedControl"] svg,
            button[data-testid="stSidebarCollapseButton"] svg,
            button[data-testid="baseButton-header"] svg,
            button[kind="header"] svg,
            header button svg{
                display: block !important;
                color: #0b3b60 !important;
                fill: #0b3b60 !important;
                width: 28px !important;
                height: 28px !important;
            }

            /* ✅ CONTENIDO PRINCIPAL - Sin padding extra */
            .block-container{
                padding-top: 1.5rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# =========================
# INICIALIZACIÓN
# =========================
inject_css()
init_db()
require_auth()

user = get_current_user() or {}

# =========================
# TÍTULO Y CAMPANITA
# =========================
usuario_actual = user.get("usuario", user.get("email", ""))
cant_pendientes = 0
if usuario_actual:
    cant_pendientes = contar_notificaciones_no_leidas(usuario_actual)

col_logo, col_spacer, col_notif = st.columns([7, 2, 1])

with col_logo:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px;">
            <div>
                <h1 style="margin: 0; font-size: 38px; font-weight: 900; color: #0f172a;">
                    FertiChat
                </h1>
                <p style="margin: 4px 0 0 0; font-size: 15px; color: #64748b;">
                    Sistema de Gestión de Compras
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_notif:
    if cant_pendientes > 0:
        if st.button(f"🔔 {cant_pendientes}", key="campanita_global"):
            st.session_state["radio_menu"] = "📄 Pedidos internos"
            st.rerun()
    else:
        st.markdown("<div style='text-align:right; font-size:26px;'>🔔</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# =========================
# SIDEBAR (PC Y MÓVIL)
# =========================
with st.sidebar:
    st.markdown(f"""
        <div style='
            background: rgba(255,255,255,0.85);
            padding: 16px;
            border-radius: 18px;
            margin-bottom: 14px;
            border: 1px solid rgba(15, 23, 42, 0.10);
            box-shadow: 0 10px 26px rgba(2, 6, 23, 0.06);
        '>
            <div style='display:flex; align-items:center; gap:10px; justify-content:center;'>
                <div style='font-size: 26px;'>🦋</div>
                <div style='font-size: 20px; font-weight: 800; color:#0f172a;'>FertiChat</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.text_input("Buscar...", key="sidebar_search", label_visibility="collapsed", placeholder="Buscar...")

    st.markdown(f"👤 **{user.get('nombre', 'Usuario')}**")
    if user.get('empresa'):
        st.markdown(f"🏢 {user.get('empresa')}")
    st.markdown(f"📧 _{user.get('Usuario', '')}_")

    st.markdown("---")

    if st.button("🚪 Cerrar sesión", key="btn_logout_sidebar", use_container_width=True):
        logout()
        st.rerun()

    st.markdown("---")
    st.markdown("## 📌 Menú")

    # Inicializar si no existe
    if "radio_menu" not in st.session_state:
        st.session_state["radio_menu"] = "🏠 Inicio"

    menu = st.radio("Ir a:", MENU_OPTIONS, key="radio_menu")


# =========================
# ROUTER
# =========================
menu_actual = st.session_state["radio_menu"]

if menu_actual == "🏠 Inicio":
    mostrar_inicio()
elif menu_actual == "🛒 Compras IA":
    mostrar_resumen_compras_rotativo()
    Compras_IA()
elif menu_actual == "📦 Stock IA":
    mostrar_resumen_stock_rotativo()
    mostrar_stock_ia()
elif menu_actual == "🔎 Buscador IA":
    mostrar_buscador_ia()
elif menu_actual == "📥 Ingreso de comprobantes":
    mostrar_ingreso_comprobantes()
elif menu_actual == "📊 Dashboard":
    mostrar_dashboard()
elif menu_actual == "📄 Pedidos internos":
    mostrar_pedidos_internos()
elif menu_actual == "🧾 Baja de stock":
    mostrar_baja_stock()
elif menu_actual == "📈 Indicadores (Power BI)":
    mostrar_indicadores_ia()
elif menu_actual == "📦 Órdenes de compra":
    mostrar_ordenes_compra()
elif menu_actual == "📒 Ficha de stock":
    mostrar_ficha_stock()
elif menu_actual == "📚 Artículos":
    mostrar_articulos()
elif menu_actual == "🏬 Depósitos":
    mostrar_depositos()
elif menu_actual == "🧩 Familias":
    mostrar_familias()
