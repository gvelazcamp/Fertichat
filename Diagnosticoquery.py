# =========================
# QUERIES DE DIAGNÓSTICO
# =========================

import streamlit as st
from supabase_client import ejecutar_consulta

# -------------------------------------------------
# DEBUG REAL DE LA APP
# -------------------------------------------------
def mostrar_debug_real(debug: dict):
    st.subheader("🧠 Lo que entendió la app")

    st.write("### 🧾 Pregunta original")
    st.code(debug.get("pregunta", "—"))

    st.write("### 🔎 Parámetros interpretados")
    st.write(f"- **Proveedor:** `{debug.get('proveedor')}`")
    st.write(f"- **Mes:** `{debug.get('mes')}`")
    st.write(f"- **Año:** `{debug.get('anio')}`")

    st.write("### 🧪 SQL ejecutado")
    st.code(debug.get("sql", ""), language="sql")

    st.write("### 📎 Parámetros SQL")
    st.code(str(debug.get("params", ())), language="python")

    st.write("### 📤 Resultado crudo")

    try:
        df = ejecutar_consulta(
            debug.get("sql"),
            debug.get("params")
        )

        if df is not None and not df.empty:
            st.success("✅ La query ejecutó y devolvió datos")
            st.dataframe(df)
        else:
            st.warning("⚠️ La query ejecutó OK pero no devolvió filas")

    except Exception as e:
        st.error(f"❌ Error ejecutando la query: {e}")

# -------------------------------------------------
# PROVEEDORES SIMILARES
# -------------------------------------------------
def mostrar_proveedores_similares(proveedor: str):
    st.subheader("🔍 Proveedores similares en la base")

    sql = f"""
        SELECT DISTINCT "Cliente / Proveedor"
        FROM chatbot_raw
        WHERE LOWER("Cliente / Proveedor") LIKE LOWER('%{proveedor}%')
        ORDER BY "Cliente / Proveedor"
    """

    df = ejecutar_consulta(sql)

    if df is not None and not df.empty:
        st.dataframe(df)
    else:
        st.warning("⚠️ No se encontraron proveedores similares")

# -------------------------------------------------
# MESES DISPONIBLES
# -------------------------------------------------
def mostrar_meses_disponibles():
    st.subheader("📅 Meses disponibles en la base")

    sql = """
        SELECT DISTINCT "Mes"
        FROM chatbot_raw
        ORDER BY "Mes"
    """

    df = ejecutar_consulta(sql)

    if df is not None and not df.empty:
        st.dataframe(df)
    else:
        st.warning("⚠️ No se encontraron meses")

# -------------------------------------------------
# CRUCE PROVEEDOR / MES
# -------------------------------------------------
def mostrar_cruce_proveedor_mes(proveedor: str):
    st.subheader("🧪 Cruce proveedor / mes")

    sql = f"""
        SELECT 
            "Cliente / Proveedor",
            "Mes",
            COUNT(*) AS registros
        FROM chatbot_raw
        WHERE LOWER("Cliente / Proveedor") LIKE LOWER('%{proveedor}%')
        GROUP BY "Cliente / Proveedor", "Mes"
        ORDER BY "Mes"
    """

    df = ejecutar_consulta(sql)

    if df is not None and not df.empty:
        st.dataframe(df)
    else:
        st.warning("⚠️ No hay cruces proveedor / mes")
