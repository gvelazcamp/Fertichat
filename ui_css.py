# =========================
# UI_CSS.PY - CSS GLOBAL (PC + MÓVIL)
# =========================

CSS_GLOBAL = r"""
<style>

/* Ocultar elementos */
#MainMenu, footer { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }

/* FORZAR MODO CLARO GLOBAL */
html, body {
  color-scheme: light !important;
  background: #f6f4ef !important;
}

/* Variables */
:root {
  --fc-bg-1: #f6f4ef;
  --fc-bg-2: #f3f6fb;
  --fc-primary: #0b3b60;
  --fc-accent: #f59e0b;

  --background-color: #f6f4ef;
  --secondary-background-color: #ffffff;
  --text-color: #0f172a;
}

/* Contenedores principales */
html, body,
.stApp,
div[data-testid="stApp"],
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewContainer"] > .main,
div[data-testid="stAppViewContainer"] > .main > div {
  background: linear-gradient(135deg, var(--fc-bg-1), var(--fc-bg-2)) !important;
  color: #0f172a !important;
}

html, body {
  font-family: Inter, system-ui, sans-serif;
  color: #0f172a;
}

.block-container {
  max-width: 1240px;
  padding-top: 1.25rem;
  padding-bottom: 2.25rem;
}

/* =========================================================
   SIDEBAR GLOBAL
   ========================================================= */
section[data-testid="stSidebar"] {
  border-right: 1px solid rgba(15, 23, 42, 0.08);
}

section[data-testid="stSidebar"] > div,
div[data-testid="stSidebar"] > div {
  background: rgba(255,255,255,0.92) !important;
  backdrop-filter: blur(8px);
}

section[data-testid="stSidebar"],
section[data-testid="stSidebar"] *,
div[data-testid="stSidebar"],
div[data-testid="stSidebar"] * {
  color: #0f172a !important;
}

/* =========================================================
   DESKTOP
   ========================================================= */
@media (hover: hover) and (pointer: fine) {
  div[data-testid="stToolbarActions"],
  div[data-testid="collapsedControl"] {
    display: none !important;
  }
}

/* =========================================================
   MÓVIL
   ========================================================= */
@media (hover: none) and (pointer: coarse) {
  .block-container { padding-top: 70px !important; }

  section[data-testid="stSidebar"] > div {
    background: #ffffff !important;
  }
}

/* =========================================================
   LOGIN - ESTILO COMPLETO (COMO ANTES)
   ========================================================= */

/* Fondo violeta SOLO para login */
.stApp {
  background: linear-gradient(180deg, #6b6eea 0%, #7b4fa3 50%, #f6f4ef 100%) !important;
}

/* Tarjeta LOGO */
.block-container h1 {
  font-size: 42px !important;
  font-weight: 900 !important;
  margin-bottom: 6px !important;
  color: #5b5fd6 !important;
}

.block-container p {
  color: #64748b !important;
  font-size: 15px !important;
}

/* Tarjeta blanca del LOGO */
.block-container > div:first-child > div {
  background: rgba(255,255,255,0.96) !important;
  border-radius: 26px !important;
  padding: 28px 36px !important;
  box-shadow: 0 25px 60px rgba(0,0,0,0.18) !important;
  margin-bottom: 22px !important;
}

/* Tarjeta del FORM */
div[data-testid="stForm"] {
  background: rgba(255,255,255,0.97) !important;
  border-radius: 24px !important;
  padding: 32px 36px !important;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.18) !important;
  border: none !important;
}

/* Tabs */
div[data-baseweb="tab-list"] {
  background: #f1f5f9 !important;
  border-radius: 14px !important;
  padding: 6px !important;
}

button[data-baseweb="tab"] {
  border-radius: 12px !important;
  font-weight: 600 !important;
  color: #64748b !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
  background: #ffffff !important;
  color: #5b5fd6 !important;
  box-shadow: 0 6px 16px rgba(15,23,42,0.15) !important;
}

/* Inputs */
div[data-baseweb="input"],
div[data-baseweb="base-input"] {
  background: #f8fafc !important;
  border: 2px solid #e2e8f0 !important;
  border-radius: 14px !important;
}

/* Texto inputs */
div[data-baseweb="input"] input,
div[data-baseweb="base-input"] input {
  color: #1e293b !important;
  background: transparent !important;
}

/* Botón INGRESAR */
button[type="submit"] {
  background: linear-gradient(135deg, #6b6eea, #7b4fa3) !important;
  color: #ffffff !important;
  border-radius: 14px !important;
  font-weight: 800 !important;
  padding: 14px 28px !important;
  box-shadow: 0 12px 30px rgba(107,110,234,0.45) !important;
}
