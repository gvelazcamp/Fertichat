# =========================
# MAIN.PY - SOLO SIDEBAR (SIN MENÚ MÓVIL)
# =========================

import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="FertiChat",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="expanded"
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
# CSS SIMPLE
# =========================
st.markdown("""
<style>
/* Ocultar UI de Streamlit */
div.stAppToolbar,
div[data-testid="stToolbar"],
div[data-testid="stToolbarActions"],
div[data-testid="stDecoration"],
#MainMenu,
footer {
  display: none !important;
}

header[data-testid="stHeader"] {
  height: 0 !important;
  background: transparent !important;
}

/* Theme general */
:root {
    --fc-bg-1: #f6f4ef;
    --fc-bg-2: #f3f6fb;
    --fc-primary: #0b3b60;
    --fc-accent: #f59e0b;
}

html, body {
    font-family: Inter, system-ui, sans-serif;
    color: #0f172a;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, var(--fc-bg-1), var(--fc-bg-2));
}

.block-container {
    max-width: 1240px;
    padding-top: 1.25rem;
    padding-bottom: 2.25rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(15, 23, 42, 0.08);
}

section[data-testid="stSidebar"] > div {
    background: rgba(255,255,255,0.70);
    backdrop-filter: blur(8px);
}

div[data-testid="stSidebar"] div[role="radiogroup"] label {
    border-radius: 12px;
    padding: 8px 10px;
    margin: 3px 0;
    border: 1px solid transparent;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(37,99,235,0.06);
}

div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: rgba(245,158,11,0.10);
    border: 1px solid rgba(245,158,11,0.18);
}

/* Móvil: sidebar lateral completo */
@media (max-width: 768px) {
    /* Espacio para el header custom */
    .block-container {
        padding-top: 70px !important;
    }
    
    /* Header fijo con botón hamburguesa */
    #mobile-menu-toggle {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: #0b3b60;
        z-index: 999998;
        display: flex;
        align-items: center;
        padding: 0 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    #mobile-menu-toggle button {
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 8px;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    
    #mobile-menu-toggle button span {
        width: 24px;
        height: 3px;
        background: white;
        border-radius: 2px;
        display: block;
        transition: all 0.3s;
    }
    
    #mobile-menu-toggle .logo {
        color: white;
        font-size: 20px;
        font-weight: 800;
        margin-left: 12px;
    }
    
    /* Sidebar móvil */
    section[data-testid="stSidebar"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        height: 100vh !important;
        width: 320px !important;
        max-width: 85vw !important;
        z-index: 999999 !important;
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        box-shadow: 4px 0 12px rgba(0,0,0,0.2);
    }
    
    section[data-testid="stSidebar"].open {
        transform: translateX(0) !important;
    }
    
    /* Overlay oscuro */
    #sidebar-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        z-index: 999998;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s;
    }
    
    #sidebar-overlay.open {
        opacity: 1;
        visibility: visible;
    }
    
    /* Hacer scroll en el sidebar */
    section[data-testid="stSidebar"] > div {
        overflow-y: auto !important;
        height: 100% !important;
        padding-top: 20px !important;
    }
}
</style>
""", unsafe_allow_html=True)


# =========================
# INICIALIZACIÓN
# =========================
init_db()
require_auth()

user = get_current_user() or {}

if "radio_menu" not in st.session_state:
    st.session_state["radio_menu"] = "🏠 Inicio"


# =========================
# HEADER MÓVIL CON BOTÓN HAMBURGUESA
# =========================
st.markdown("""
<div id="mobile-menu-toggle">
    <button id="hamburger-btn">
        <span></span>
        <span></span>
        <span></span>
    </button>
    <div class="logo">🦋 FertiChat</div>
</div>

<div id="sidebar-overlay"></div>

<script>
(function() {
    let sidebarOpen = false;
    
    function findSidebar() {
        // Buscar en el documento principal y en todos los iframes
        let sidebar = document.querySelector('section[data-testid="stSidebar"]');
        if (!sidebar && window.parent && window.parent.document) {
            sidebar = window.parent.document.querySelector('section[data-testid="stSidebar"]');
        }
        return sidebar;
    }
    
    function toggleSidebar() {
        const sidebar = findSidebar();
        const overlay = document.getElementById('sidebar-overlay') || 
                        (window.parent && window.parent.document.getElementById('sidebar-overlay'));
        
        console.log('Sidebar encontrado:', sidebar);
        console.log('Overlay encontrado:', overlay);
        
        if (sidebar) {
            sidebarOpen = !sidebarOpen;
            
            if (sidebarOpen) {
                sidebar.classList.add('open');
                sidebar.style.transform = 'translateX(0)';
                if (overlay) {
                    overlay.classList.add('open');
                    overlay.style.opacity = '1';
                    overlay.style.visibility = 'visible';
                }
            } else {
                sidebar.classList.remove('open');
                sidebar.style.transform = 'translateX(-100%)';
                if (overlay) {
                    overlay.classList.remove('open');
                    overlay.style.opacity = '0';
                    overlay.style.visibility = 'hidden';
                }
            }
        } else {
            console.error('No se encontró el sidebar');
        }
    }
    
    function closeSidebar() {
        const sidebar = findSidebar();
        const overlay = document.getElementById('sidebar-overlay') || 
                        (window.parent && window.parent.document.getElementById('sidebar-overlay'));
        
        if (sidebar) {
            sidebarOpen = false;
            sidebar.classList.remove('open');
            sidebar.style.transform = 'translateX(-100%)';
            if (overlay) {
                overlay.classList.remove('open');
                overlay.style.opacity = '0';
                overlay.style.visibility = 'hidden';
            }
        }
    }
    
    // Event listeners
    document.addEventListener('DOMContentLoaded', function() {
        const btn = document.getElementById('hamburger-btn');
        const overlay = document.getElementById('sidebar-overlay');
        
        if (btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Click en hamburguesa');
                toggleSidebar();
            });
        }
        
        if (overlay) {
            overlay.addEventListener('click', closeSidebar);
        }
        
        // Cerrar al seleccionar opción
        setTimeout(function() {
            const sidebar = findSidebar();
            if (sidebar) {
                const radioButtons = sidebar.querySelectorAll('input[type="radio"]');
                radioButtons.forEach(function(radio) {
                    radio.addEventListener('change', function() {
                        setTimeout(closeSidebar, 200);
                    });
                });
            }
        }, 1000);
    });
    
    // Si ya está cargado
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        const btn = document.getElementById('hamburger-btn');
        if (btn) {
            btn.onclick = function(e) {
                e.preventDefault();
                console.log('Click directo en hamburguesa');
                toggleSidebar();
            };
        }
    }
})();
</script>
""", unsafe_allow_html=True)


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
    st.markdown(f"📧 _{user.get('Usuario', user.get('usuario', ''))}_")

    st.markdown("---")

    if st.button("🚪 Cerrar sesión", key="btn_logout_sidebar", use_container_width=True):
        logout()
        st.rerun()

    st.markdown("---")
    st.markdown("## 📌 Menú")

    # ESTE ES EL ÚNICO MENÚ - Funciona en PC y móvil
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
