# =========================
# SQL CORE - CONEXIÓN Y HELPERS COMPARTIDOS
# =========================

import os
import re
import pandas as pd
from typing import Optional, List
import streamlit as st

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None


# =====================================================================
# CONEXIÓN DB (SUPABASE / POSTGRES)
# =====================================================================

def get_db_connection():
    """Conexión a Postgres (Supabase) usando Secrets/Env vars."""
    if psycopg2 is None:
        print("❌ psycopg2 no instalado")
        return None
    try:
        # Obtener credenciales de la base de datos
        host = st.secrets.get("DB_HOST", os.getenv("DB_HOST"))
        port = st.secrets.get("DB_PORT", os.getenv("DB_PORT", "5432"))
        dbname = st.secrets.get("DB_NAME", os.getenv("DB_NAME", "postgres"))
        user = st.secrets.get("DB_USER", os.getenv("DB_USER"))
        password = st.secrets.get("DB_PASSWORD", os.getenv("DB_PASSWORD"))

        # DEBUG: ver qué credenciales se están usando realmente
        print("DEBUG DB CREDS:", host, port, dbname, user)

        # Verificación previa de las credenciales
        if not host or not user or not password:
            print("❌ Faltan credenciales para la conexión.")
            return None

        # Establecer conexión
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",
        )
        return conn

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


# =====================================================================
# CONSTANTES - TABLAS Y COLUMNAS
# =====================================================================

TABLE_COMPRAS = "chatbot_raw"

COL_TIPO_COMP = '"Tipo Comprobante"'
COL_NRO_COMP = '"Nro. Comprobante"'
COL_MONEDA = '"Moneda"'
COL_PROV = '"Cliente / Proveedor"'
COL_FAMILIA = '"Familia"'
COL_ART = '"Articulo"'
COL_ANIO = '"Año"'
COL_MES = '"Mes"'
COL_FECHA = '"Fecha"'
COL_CANT = '"Cantidad"'
COL_MONTO = '"Monto Neto"'


# =====================================================================
# HELPERS SQL (POSTGRES)
# =====================================================================

def _safe_ident(col_name: str) -> str:
    """Escapa un nombre de columna para usar en SQL de forma segura."""
    clean = str(col_name).strip().strip('"')
    return f'"{clean}"'


def _sql_fecha_expr() -> str:
    return '"Fecha"'


def _sql_mes_col() -> str:
    return 'TRIM(COALESCE("Mes", \'\'))'


def _sql_moneda_norm_expr() -> str:
    return 'TRIM(COALESCE("Moneda", \'\'))'


def _sql_num_from_text(text_expr: str) -> str:
    return f"CAST(NULLIF(TRIM({text_expr}), '') AS NUMERIC(15,2))"


def _sql_total_num_expr() -> str:
    """Convierte Monto Neto a número (pesos)."""
    limpio = """
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(TRIM(COALESCE("Monto Neto", '')), '.', ''),
                        ',', '.'
                    ),
                    '(', '-'
                ),
                ')', ''
            ),
            '$', ''
        )
    """
    return _sql_num_from_text(limpio)


def _sql_total_num_expr_usd() -> str:
    """Convierte Monto Neto a número (USD)."""
    limpio = """
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(TRIM(COALESCE("Monto Neto", '')), 'U$S', ''),
                                'U$$', ''
                            ),
                            '$', ''
                        ),
                        '.', ''
                    ),
                    ',', '.'
                ),
                '(', '-'
            ),
            ')', ''
        )
    """
    return _sql_num_from_text(limpio)


def _sql_total_num_expr_general() -> str:
    """Convierte Monto Neto a número (sirve para $ o U$S)."""
    limpio = """
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(TRIM(COALESCE("Monto Neto", '')), 'U$S', ''),
                                    'U$$', ''
                                ),
                                '$', ''
                            ),
                            '.', ''
                        ),
                        ',', '.'
                    ),
                    '(', '-'
                ),
                ')', ''
            ),
            ' ', ''
        )
    """
    return _sql_num_from_text(limpio)


# =====================================================================
# EJECUTOR SQL
# =====================================================================

def ejecutar_consulta(query: str, params: tuple = None) -> pd.DataFrame:
    """
    Ejecuta una consulta SQL y retorna los resultados en un DataFrame.

    Usa cursor psycopg2 en vez de pd.read_sql_query para evitar conflictos
    con % y placeholders %s.
    """
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ No se pudo establecer conexión con la base de datos.")
            return pd.DataFrame()

        if params is None:
            params = ()

        print("\n🛠 SQL ejecutado:")
        print(query)
        print("🛠 Parámetros usados:")
        print(params)

        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description is None:
                conn.commit()
                conn.close()
                print("✅ Consulta sin retorno ejecutada.")
                return pd.DataFrame()

            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()

        conn.close()

        df = pd.DataFrame(rows, columns=cols)

        if df.empty:
            print("⚠️ Consulta ejecutada, pero no devolvió resultados.")
        else:
            print(f"✅ Resultados obtenidos: {len(df)} filas.")
        return df

    except Exception as e:
        print(f"❌ Error ejecutando consulta SQL: {e}")
        print(f"SQL fallido:\n{query}")
        print(f"Parámetros:\n{params}")
        return pd.DataFrame()


# =====================================================================
# LISTADOS Y HELPERS QUE YA USABAS
# (los dejo como los tenías, no son el origen del fallo)
# =====================================================================

def get_valores_unicos(
    tabla: str,
    columna: str,
    incluir_todos: bool = True,
    label_todos: str = "Todos",
    limite: int = 500
) -> list:
    """
    Devuelve valores únicos (TRIM) de una columna en una tabla.
    Pensada para armar filtros/selector.
    """
    try:
        t = str(tabla).strip().strip('"')
        if not re.fullmatch(r"[A-Za-z0-9_]+", t):
            print(f"⚠️ Tabla inválida para get_valores_unicos: {tabla}")
            return [label_todos] if incluir_todos else []

        col_sql = _safe_ident(columna)
        tabla_sql = f'"{t}"'

        sql = f"""
            SELECT DISTINCT TRIM({col_sql}) AS valor
            FROM {tabla_sql}
            WHERE {col_sql} IS NOT NULL AND TRIM({col_sql}) <> ''
            ORDER BY valor
            LIMIT %s
        """
        df = ejecutar_consulta(sql, (int(limite),))

        if df.empty:
            return [label_todos] if incluir_todos else []

        vals = df["valor"].dropna().astype(str).tolist()
        return ([label_todos] + vals) if incluir_todos else vals

    except Exception as e:
        print(f"❌ Error en get_valores_unicos: {e}")
        return [label_todos] if incluir_todos else []


def get_lista_anios() -> list:
    sql = """
        SELECT DISTINCT "Año"::int AS anio
        FROM chatbot_raw
        WHERE "Año" IS NOT NULL AND "Año" <> ''
        ORDER BY anio DESC
    """
    df = ejecutar_consulta(sql)
    if df.empty:
        print("⚠️ No se encontraron años en la base de datos.")
        return []
    return df["anio"].tolist()


def get_lista_meses() -> list:
    sql = """
        SELECT DISTINCT TRIM("Mes") AS mes
        FROM chatbot_raw
        WHERE "Mes" IS NOT NULL AND TRIM("Mes") <> ''
        ORDER BY mes
    """
    df = ejecutar_consulta(sql)
    if df.empty:
        print("⚠️ No se encontraron meses en la base de datos.")
        return []
    return df["mes"].tolist()


# =====================================================================
# FUNCIÓN PARA OBTENER ÚLTIMO MES DISPONIBLE  ✅ (LA QUE FALTABA)
# =====================================================================

def get_ultimo_mes_disponible_hasta(mes_key: str) -> Optional[str]:
    """
    Busca el último mes disponible en la tabla chatbot_raw hasta el mes indicado.
    Se usa desde sql_compras.py.
    """
    try:
        sql = """
            SELECT DISTINCT TRIM("Mes") AS mes
            FROM chatbot_raw
            WHERE TRIM("Mes") IS NOT NULL 
              AND TRIM("Mes") <> ''
              AND TRIM("Mes") <= %s
            ORDER BY TRIM("Mes") DESC
            LIMIT 1
        """
        df = ejecutar_consulta(sql, (mes_key,))

        if df.empty:
            print(f"⚠️ No se encontró mes disponible hasta {mes_key}")
            return None

        mes_encontrado = df["mes"].iloc[0]
        print(f"✅ Último mes disponible hasta {mes_key}: {mes_encontrado}")
        return mes_encontrado

    except Exception as e:
        print(f"❌ Error buscando último mes disponible: {e}")
        return None
