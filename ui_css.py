# =========================
# UI_CSS.PY - CSS GLOBAL (PC + MÓVIL)
# =========================

CSS_GLOBAL = r"""
/* Ocultar elementos */
#MainMenu, footer { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }

/* Theme general */
:root {
  --fc-bg-1: #f6f4ef;
  --fc-bg-2: #f3f6fb;
  --fc-primary: #0b3b60;
  --fc-accent: #f59e0b;
}

html, body { font-family: Inter, system-ui, sans-serif; color: #0f172a; }
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, var(--fc-bg-1), var(--fc-bg-2)); }
.block-container { max-width: 1240px; padding-top: 1.25rem; padding-bottom: 2.25rem; }

/* Sidebar look */
section[data-testid="stSidebar"] { border-right: 1px solid rgba(15, 23, 42, 0.08); }
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
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: rgba(37,99,235,0.06); }
div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: rgba(245,158,11,0.10);
  border: 1px solid rgba(245,158,11,0.18);
}

/* Header móvil visual */
#mobile-header { display: none; }
#campana-mobile { display: none; }

/* DESKTOP (mouse/trackpad) */
@media (hover: hover) and (pointer: fine) {
  [data-testid="stHeader"] { background: var(--fc-bg-1) !important; }
  .stAppHeader { background: var(--fc-bg-1) !important; }
  [data-testid="stToolbar"] { background: var(--fc-bg-1) !important; }

  div[data-testid="stToolbarActions"] { display: none !important; }
  div[data-testid="collapsedControl"] { display: none !important; }

  [data-testid="baseButton-header"],
  button[data-testid="stSidebarCollapseButton"],
  button[data-testid="stSidebarExpandButton"],
  button[title="Close sidebar"],
  button[title="Open sidebar"] {
    display: none !important;
  }
}

/* MÓVIL (touch) */
@media (hover: none) and (pointer: coarse) {
  .block-container { padding-top: 70px !important; }

  #mobile-header {
    display: flex !important;
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 60px;
    background: #0b3b60;
    z-index: 999996;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px 0 56px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }

  #mobile-header .logo {
    color: white;
    font-size: 20px;
    font-weight: 800;
  }

  #campana-mobile {
    display: flex !important;
    position: fixed !important;
    top: 12px !important;
    left: 52px !important;
    z-index: 1000001 !important;
    font-size: 22px;
    text-decoration: none;
    padding: 6px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  }

  #campana-mobile .notif-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: #ef4444;
    color: white;
    font-size: 10px;
    font-weight: 700;
    min-width: 16px;
    height: 16px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 3px;
  }

  div[data-testid="collapsedControl"],
  button[data-testid="stSidebarExpandButton"],
  button[title="Open sidebar"] {
    display: inline-flex !important;
    position: fixed !important;
    top: 12px !important;
    left: 12px !important;
    z-index: 1000000 !important;
  }

  [data-testid="baseButton-header"],
  button[data-testid="stSidebarCollapseButton"],
  button[title="Close sidebar"] {
    display: inline-flex !important;
  }

  /* ============================================= */
  /* 🔥 SELECTBOX MÓVIL - BLANCO + TEXTO NEGRO */
  /* ============================================= */
  div[data-testid="stSelectbox"],
  div[data-testid="stSelectbox"] > div,
  div[data-testid="stSelectbox"] > div > div {
    background: #ffffff !important;
    background-color: #ffffff !important;
  }

  div[data-baseweb="select"],
  div[data-baseweb="select"] > div,
  div[data-baseweb="select"] > div > div,
  div[data-baseweb="select"] > div > div > div {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
  }

  div[data-baseweb="select"] input {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: none !important;
  }

  div[data-baseweb="select"] svg { fill: #64748b !important; }

  div[data-baseweb="popover"],
  div[data-baseweb="popover"] > div,
  div[data-baseweb="menu"],
  div[data-baseweb="menu"] ul,
  div[data-baseweb="menu"] li {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
  }

  div[data-baseweb="menu"] li:hover {
    background: #f1f5f9 !important;
    background-color: #f1f5f9 !important;
  }

  [class*="StyledControl"],
  [class*="StyledControlContainer"],
  [class*="StyledValueContainer"],
  [class*="StyledSingleValue"],
  [class*="StyledInput"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
  }

  [class*="StyledPlaceholder"] { color: #64748b !important; }

  /* TEXT INPUT */
  div[data-testid="stTextInput"] { background: transparent !important; }
  div[data-testid="stTextInput"] > div { background: #ffffff !important; }
  div[data-testid="stTextInput"] input[type="text"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
  }

  /* CHAT INPUT */
  div[data-testid="stChatInput"] { background: transparent !important; }
  div[data-testid="stChatInput"] > div { background: #ffffff !important; }
  textarea[data-testid="stChatInputTextArea"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
  }
}

/* Refuerzo móvil general (768px) */
@media (max-width: 768px) {
  .block-container h1,
  .block-container h2,
  .block-container h3,
  .block-container p,
  .block-container span,
  .block-container label {
    color: #0f172a !important;
  }

  .block-container button {
    background: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
  }

  div[data-testid="stSelectbox"],
  div[data-testid="stSelectbox"] > div,
  div[data-testid="stSelectbox"] > div > div,
  div[data-baseweb="select"],
  div[data-baseweb="select"] > div,
  div[data-baseweb="select"] > div > div,
  div[data-baseweb="select"] > div > div > div {
    background: #ffffff !important;
    background-color: #ffffff !important;
  }

  div[data-baseweb="select"] input {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
  }

  div[data-baseweb="select"] span,
  div[data-baseweb="select"] div,
  [class*="StyledSingleValue"] {
    color: #0f172a !important;
  }

  div[data-baseweb="popover"],
  div[data-baseweb="popover"] *,
  div[data-baseweb="menu"],
  div[data-baseweb="menu"] * {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
  }
}
"""
