# ui_chat_chainlit.py
import streamlit as st
import streamlit.components.v1 as components

# =========================
# CHAT (CHAINLIT) - PUENTE DESDE STREAMLIT
# =========================
def mostrar_chat_chainlit():
    st.subheader("💬 Chat (Chainlit)")

    # 1) URL configurable desde secrets (recomendado en Streamlit Cloud)
    # En Streamlit Cloud -> Settings -> Secrets:
    # CHAINLIT_URL = "https://tu-chainlit-app..."
    chainlit_url = None
    try:
        chainlit_url = st.secrets.get("CHAINLIT_URL", None)
    except Exception:
        chainlit_url = None

    # 2) Default para local
    if not chainlit_url:
        chainlit_url = "http://localhost:8000"

    st.write("Abrí el chat (recomendado):")
    try:
        st.link_button("Abrir Chat", chainlit_url)
    except Exception:
        st.markdown(
            f'<a href="{chainlit_url}" target="_blank">Abrir Chat</a>',
            unsafe_allow_html=True
        )

    st.divider()
    st.caption("Si querés probar embebido (puede fallar si el hosting bloquea iframes):")
    components.iframe(chainlit_url, height=800, scrolling=True)
