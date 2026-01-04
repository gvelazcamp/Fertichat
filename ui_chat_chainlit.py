# ui_chat_chainlit.py
import streamlit as st

def mostrar_chat_chainlit():
    st.subheader("💬 Chat (Chainlit)")
    st.write("Abrí el chat en otra pestaña:")

    url = "http://localhost:8000"

    try:
        st.link_button("Abrir Chat", url)
    except Exception:
        st.markdown(f'<a href="{url}" target="_blank">Abrir Chat</a>', unsafe_allow_html=True)
