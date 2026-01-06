# =========================
# SQL CORE - CONEXIÓN Y HELPERS COMPARTIDOS
# =========================

import os
import re
import pandas as pd
from typing import Optional
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
        print("psycopg2 no instalado")
        return None
    try:
        host = st.secrets.get("DB_HOST", os.getenv("DB_HOST"))
        port = st.secrets.get("DB_PORT", os.getenv("DB_PORT", "5432"))
        dbname = st.secrets.get("DB_NAME", os.getenv("DB_NAME", "postgres"))
        user = st.secrets.get("DB_USER", os.getenv("DB_USER"))
        password = st.secrets.get("DB_PASSWORD", os.getenv("DB_PASSWORD"))

        if not host or not user or not password:
            return None

        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require"
        )
        return conn

    except Exception as e:
        print(f"Error de conexión: {e}")
        return None


# =====================================================================
# CONSTANTES - TABLAS Y COLUMNAS
# =====================================================================

TABLE_COMPRAS = "chatbot_raw"

COL_TIPO_COMP = '"Tipo Comprobante"'
COL_NRO_COMP  = '"Nro. Comprobante"'
COL_MONEDA    = '"Moneda"'
COL_PROV      = '"Cliente / Proveedor"'
COL_FAMILIA   = '"Familia"'
COL_ART       = '"Articulo"'
COL_ANIO      = '"Año"'
COL_MES       = '"Mes"'
COL_FECHA     = '"Fecha"'
COL_CANT      = '"Cantidad"'
COL_MONTO     = '"Monto Neto"'


# =====================================================================
# HELPERS SQL (POSTGRES)
# =====================================================================

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
    """Ejecuta consulta SQL y retorna DataFrame."""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        if params is None:
            params = ()

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    except Exception as e:
        print(f"Error en consulta SQL: {e}")
        return pd.DataFrame()


# =====================================================================
# LISTADOS GENÉRICOS
# =====================================================================

def get_lista_proveedores() -> list:
    sql = """
        SELECT DISTINCT TRIM("Cliente / Proveedor") AS proveedor
        FROM chatbot_raw
        WHERE "Cliente / Proveedor" IS NOT NULL AND TRIM("Cliente / Proveedor") <> ''
        ORDER BY proveedor
        LIMIT 500
    """
    df = ejecutar_consulta(sql)
    if df.empty:
        return ["Todos"]
    return ["Todos"] + df['proveedor'].tolist()

def get_lista_articulos_stock() -> list:
    sql = """
        SELECT DISTINCT TRIM("Articulo") AS articulo
        FROM stock_raw
        WHERE "Articulo" IS NOT NULL AND TRIM("Articulo") <> ''
        ORDER BY articulo
        LIMIT 500
    """
    df = ejecutar_consulta(sql)
    if df.empty:
        return ["Todos"]
    return ["Todos"] + df['articulo'].tolist()

def get_lista_familias_stock() -> list:
    sql = """
        SELECT DISTINCT TRIM("Familia") AS familia
        FROM stock_raw
        WHERE "Familia" IS NOT NULL AND TRIM("Familia") <> ''
        ORDER BY familia
        LIMIT 500
    """
    df = ejecutar_consulta(sql)
    if df.empty:
        return ["Todos"]
    return ["Todos"] + df['familia'].tolist()

def get_stock_total() -> pd.DataFrame:
    sql = """
        SELECT SUM(CAST(NULLIF(TRIM("STOCK"), '') AS NUMERIC)) AS total_stock
        FROM stock_raw
    """
    df = ejecutar_consulta(sql)
    return df

def get_stock_por_familia() -> pd.DataFrame:
    sql = """
        SELECT TRIM("Familia") AS familia, SUM(CAST(NULLIF(TRIM("STOCK"), '') AS NUMERIC)) AS total
        FROM stock_raw
        GROUP BY TRIM("Familia")
        ORDER BY familia
    """
    df = ejecutar_consulta(sql)
    return df

def get_stock_por_deposito() -> pd.DataFrame:
    sql = """
        SELECT TRIM("Deposito") AS deposito, SUM(CAST(NULLIF(TRIM("STOCK"), '') AS NUMERIC)) AS total
        FROM stock_raw
        GROUP BY TRIM("Deposito")
        ORDER BY deposito
    """
    df = ejecutar_consulta(sql)
    return df

def get_stock_articulo(articulo: str) -> pd.DataFrame:
    sql = """
        SELECT TRIM("Articulo") AS articulo, TRIM("Familia") AS familia, TRIM("Deposito") AS deposito, TRIM("STOCK") AS stock
        FROM stock_raw
        WHERE LOWER(TRIM("Articulo")) LIKE %s
        ORDER BY TRIM("Articulo")
    """
    df = ejecutar_consulta(sql, (f"%{articulo.lower()}%",))
    return df

def get_stock_familia(familia: str) -> pd.DataFrame:
    sql = """
        SELECT TRIM("Articulo") AS articulo, TRIM("Deposito") AS deposito, TRIM("STOCK") AS stock
        FROM stock_raw
        WHERE LOWER(TRIM("Familia")) = %s
        ORDER BY TRIM("Articulo")
    """
    df = ejecutar_consulta(sql, (familia.lower(),))
    return df

def get_lotes_por_vencer(dias: int) -> pd.DataFrame:
    sql = """
        SELECT TRIM("Articulo") AS articulo, TRIM("Lote") AS lote, TRIM("Vencimiento") AS vencimiento, TRIM("STOCK") AS stock,
               DATE_PART('day', TRIM("Vencimiento")::date - NOW()::date) AS dias_restantes
        FROM stock_raw
        WHERE DATE_PART('day', TRIM("Vencimiento")::date - NOW()::date) <= %s
        ORDER BY dias_restantes
    """
    df = ejecutar_consulta(sql, (dias,))
    return df

def get_lotes_vencidos() -> pd.DataFrame:
    sql = """
        SELECT TRIM("Articulo") AS articulo, TRIM("Lote") AS lote, TRIM("Vencimiento") AS vencimiento, TRIM("STOCK") AS stock
        FROM stock_raw
        WHERE TRIM("Vencimiento")::date < NOW()::date
        ORDER BY TRIM("Vencimiento")
    """
    df = ejecutar_consulta(sql)
    return df

def get_stock_bajo(umbral: int) -> pd.DataFrame:
    sql = """
        SELECT TRIM("Articulo") AS articulo, TRIM("Deposito") AS deposito, TRIM("STOCK") AS stock
        FROM stock_raw
        WHERE CAST(NULLIF(TRIM("STOCK"), '') AS NUMERIC) <= %s
        ORDER BY CAST(NULLIF(TRIM("STOCK"), '') AS NUMERIC)
    """
    df = ejecutar_consulta(sql, (umbral,))
    return df

def get_stock_lote_especifico(lote: str) -> pd.DataFrame:
    sql = """
        SELECT TRIM("Articulo") AS articulo, TRIM("Deposito") AS deposito, TRIM("STOCK") AS stock
        FROM stock_raw
        WHERE LOWER(TRIM("Lote")) = %s
    """
    df = ejecutar_consulta(sql, (lote.lower(),))
    return df

def get_alertas_vencimiento_multiple(dias_umbral: int) -> pd.DataFrame:
    sql = """
        SELECT TRIM("Articulo") AS articulo, TRIM("Lote") AS lote, TRIM("Vencimiento") AS vencimiento, TRIM("STOCK") AS stock,
               DATE_PART('day', TRIM("Vencimiento")::date - NOW()::date) AS dias_restantes
        FROM stock_raw
        WHERE DATE_PART('day', TRIM("Vencimiento")::date - NOW()::date) <= %s
        ORDER BY dias_restantes
    """
    df = ejecutar_consulta(sql, (dias_umbral,))
    return df

def get_lista_depositos_stock() -> list:
    sql = """
        SELECT DISTINCT TRIM("Deposito") AS deposito
        FROM stock_raw
        WHERE "Deposito" IS NOT NULL AND TRIM("Deposito") <> ''
        ORDER BY deposito
        LIMIT 500
    """
    df = ejecutar_consulta(sql)
    if df.empty:
        return ["Todos"]
    return ["Todos"] + df['deposito'].tolist()

def buscar_stock_por_lote(lote: str) -> pd.DataFrame:
    sql = """
        SELECT *
        FROM stock_raw
        WHERE TRIM("Lote") = %s
    """
    df = ejecutar_consulta(sql, (lote,))
    return df

def get_lista_tipos_comprobante() -> list:
    sql = """
        SELECT DISTINCT TRIM("Tipo Comprobante") AS tipo
        FROM chatbot_raw
        WHERE "Tipo Comprobante" IS NOT NULL AND TRIM("Tipo Comprobante") <> ''
        ORDER BY tipo
    """
    df = ejecutar_consulta(sql)
    if df.empty:
        return ["Todos"]
    return ["Todos"] + df['tipo'].tolist()


def get_lista_articulos() -> list:
    sql = """
        SELECT DISTINCT TRIM("Articulo") AS articulo
        FROM chatbot_raw
        WHERE "Articulo" IS NOT NULL AND TRIM("Articulo") <> ''
        ORDER BY articulo
        LIMIT 500
    """
    df = ejecutar_consulta(sql)
    if df.empty:
        return ["Todos"]
    return ["Todos"] + df['articulo'].tolist()


def get_valores_unicos() -> dict:
    return {
        "proveedores": get_lista_proveedores()[1:],
        "familias": [],
        "articulos": get_lista_articulos()[1:]
    }


# =====================================================================
# HELPERS AUXILIARES
# =====================================================================

def get_ultimo_mes_disponible_hasta(mes_key: str) -> Optional[str]:
    """
    Devuelve el último mes disponible (YYYY-MM) menor o igual al mes_key.
    """
    sql = """
        SELECT MAX(TRIM("Mes")) AS mes
        FROM chatbot_raw
        WHERE TRIM("Mes") <= %s
    """
    df = ejecutar_consulta(sql, (mes_key,))
    if df is None or df.empty:
        return None
    return df["mes"].iloc[0]


def resolver_mes_existente(mes_key: str) -> str:
    """
    Si el mes existe, lo devuelve.
    Si no existe, devuelve el último mes disponible menor.
    """
    sql = """
        SELECT MAX(TRIM("Mes")) AS mes
        FROM chatbot_raw
        WHERE TRIM("Mes") <= %s
    """
    df = ejecutar_consulta(sql, (mes_key,))
    if df is None or df.empty or not df.iloc[0]["mes"]:
        return mes_key
    return df.iloc[0]["mes"]


def _safe_ident(name: str) -> str:
    """Sanitiza identificadores simples (schema / table / column)."""
    if not name:
        return ""
    name = name.strip()
    return name if re.match(r"^[A-Za-z0-9_]+$", name) else ""
