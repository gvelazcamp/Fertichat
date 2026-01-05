# =========================
# UI_CSS.PY - CSS GLOBAL
# =========================

CSS_GLOBAL = """
<style>

/* Ocultar menú Streamlit */
#MainMenu, footer {
  display: none !important;
}

div[data-testid="stDecoration"] {
  display: none !important;
}

/* FORZAR MODO CLARO */
html, body {
  color-scheme: light !important;
  background: #f6f4ef !important;
}

/* Variables */
:root {
  --bg-main: #f6f4ef;
  --bg-secondary: #ffffff;
  --text-main: #0f172a;
  --primary: #0b3b60;
}

/* Fondo general */
.stApp,
div[data-testid="stApp"],
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewContainer"] > .main {
  background: linear-gradient(135deg, #f6f4ef, #f3f6fb) !important;
  color: var(--text-main) !important;
}

/* Tipografía */
html, body {
  font-family: Inter, system-ui, sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] > div {
  background: #ffffff !important;
}

section[data-testid="stSidebar"] * {
  color: var(--text-main) !important;
}

/* Inputs / select / date */
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-baseweb="select"],
div[data-baseweb="datepicker"],
textarea {
  background: #ffffff !important;
  color: var(--text-main) !important;
  border-color: #e2e8f0 !important;
}

/* Toolbar (campana / share / menú) — OCULTO */
[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
[data-testid="stBaseButton-header"],
button[kind="header"],
button[kind="headerNoPadding"] {
  display: none !important;
}

</style>
"""
