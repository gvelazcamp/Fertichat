# =========================
# SQL QUERIES - TABLA chatbot_raw + MONTO NETO
# =========================
import os
import psycopg2
import pandas as pd
from typing import List, Tuple, Optional
import re
from datetime import datetime

# =====================================================================
# CONEXIÓN DB (SUPABASE / POSTGRES)
# =====================================================================

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

def get_db_connection():
    """Conexión a Postgres (Supabase) usando Secrets/Env vars."""
    try:
        host = st.secrets.get("DB_HOST", os.getenv("DB_HOST"))
        port = st.secrets.get("DB_PORT", os.getenv("DB_PORT", "5432"))
        dbname = st.secrets.get("DB_NAME", os.getenv("DB_NAME", "postgres"))
        user = st.secrets.get("DB_USER", os.getenv("DB_USER"))
        password = st.secrets.get("DB_PASSWORD", os.getenv("DB_PASSWORD"))

        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",
            cursor_factory=RealDictCursor
        )
        return conn

    except Exception as e:
        print(f"Error de conexión a Postgres/Supabase: {e}")
        return None


# =====================================================================
# HELPERS SQL
# =====================================================================

def _sql_fecha_expr() -> str:
    """Convierte fecha texto a DATE"""
    return "COALESCE(TO_DATE(\"Fecha\", 'YYYY-MM-DD'), TO_DATE(\"Fecha\", 'DD/MM/YYYY'))"


def _sql_mes_col() -> str:
    """Columna Mes normalizada"""
    return 'TRIM("Mes")'


def _sql_total_num_expr() -> str:
    """Convierte Monto Neto a número"""
    return """CAST(
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(TRIM("Monto Neto"), '.', ''),
                        ',', '.'
                    ),
                    '(', '-'
                ),
                ')', ''
            ),
            '$', ''
        ) AS NUMERIC(15,2)
    )"""


def _sql_total_num_expr_usd() -> str:
    """Convierte Monto Neto USD a número"""
    return """CAST(
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(TRIM("Monto Neto"), 'U$S', ''),
                            '.', ''
                        ),
                        ',', '.'
                    ),
                    '(', '-'
                ),
                ')', ''
            ),
            '$', ''
        ) AS NUMERIC(15,2)
    )"""


def _sql_total_num_expr_general() -> str:
    """Convierte Monto Neto ($ o USD) a número"""
    return """CAST(
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(TRIM("Monto Neto"), 'U$S', ''),
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
        ) AS NUMERIC(15,2)
    )"""


def _sql_moneda_norm_expr() -> str:
    """Normaliza moneda"""
    return 'TRIM("Moneda")'


def _sql_cantidad_num_expr() -> str:
    """Convierte cantidad a número"""
    return 'CAST(REPLACE(TRIM("Cantidad"), \',\', \'.\') AS NUMERIC(15,2))'


def ejecutar_consulta(query: str, params: tuple = None) -> pd.DataFrame:
    """Ejecuta consulta SQL y retorna DataFrame"""
    import time
    
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    inicio = time.time()
    
    try:
        if params is None:
            params = ()

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            data = cursor.fetchall()

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        return df

    except Exception as e:
        print(f"Error en consulta SQL: {e}")
        return pd.DataFrame()

    finally:
        try:
            conn.close()
        except Exception:
            pass


# =====================================================================
# CONSULTAS ESPECÍFICAS
# =====================================================================

def get_ultima_factura_de_articulo(patron_articulo: str) -> pd.DataFrame:
    """Última factura donde vino un artículo"""
    total_expr = _sql_total_num_expr()
    fecha_expr = _sql_fecha_expr()

    query = f"""
        SELECT
            "Cliente / Proveedor" AS Proveedor,
            "Articulo",
            "Cantidad",
            "Nro. Comprobante" AS nro_factura,
            {total_expr} AS total_linea,
            "Fecha"
        FROM chatbot_raw
        WHERE LOWER("Articulo") LIKE %s
        ORDER BY {fecha_expr} DESC
        LIMIT 1
    """
    return ejecutar_consulta(query, (f"%{patron_articulo.lower()}%",))


def get_facturas_de_articulo(patron_articulo: str, solo_ultima: bool = False) -> pd.DataFrame:
    """Lista todas las facturas donde apareció un artículo"""
    fecha_expr = _sql_fecha_expr()
    total_expr = _sql_total_num_expr_general()

    limit_sql = "LIMIT 1" if solo_ultima else "LIMIT 50"

    query = f"""
        SELECT
            "Cliente / Proveedor" AS Proveedor,
            "Articulo",
            "Nro. Comprobante" AS Nro_Factura,
            TO_CHAR({fecha_expr}, 'DD/MM/YYYY') AS Fecha,
            "Cantidad",
            {total_expr} AS Total
        FROM chatbot_raw
        WHERE
            ("Tipo Comprobante" = 'Compra Contado' OR "Tipo Comprobante" LIKE 'Compra%')
            AND LOWER("Articulo") LIKE %s
        ORDER BY {fecha_expr} DESC
        {limit_sql}
    """
    return ejecutar_consulta(query, (f"%{patron_articulo.lower()}%",))


def get_ultima_factura_inteligente(patron: str) -> pd.DataFrame:
    """Busca última factura por patrón en ARTÍCULO o PROVEEDOR automáticamente"""
    total_expr = _sql_total_num_expr()
    fecha_expr = _sql_fecha_expr()

    query = f"""
        SELECT
            "Cliente / Proveedor" AS Proveedor,
            "Articulo",
            "Cantidad",
            "Nro. Comprobante" AS nro_factura,
            {total_expr} AS total_linea,
            "Fecha"
        FROM chatbot_raw
        WHERE 
            ("Tipo Comprobante" = 'Compra Contado' OR "Tipo Comprobante" LIKE 'Compra%')
            AND (
                LOWER("Articulo") LIKE %s 
                OR LOWER("Cliente / Proveedor") LIKE %s
            )
        ORDER BY {fecha_expr} DESC
        LIMIT 1
    """
    patron_like = f"%{patron.lower()}%"
    return ejecutar_consulta(query, (patron_like, patron_like))


def get_valores_unicos() -> dict:
    """Lista proveedores, familias y artículos únicos"""
    conn = get_db_connection()
    if not conn:
        return {}

    valores = {}

    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT DISTINCT "Cliente / Proveedor" FROM chatbot_raw WHERE "Cliente / Proveedor" IS NOT NULL ORDER BY "Cliente / Proveedor"')
            valores['proveedores'] = [row['Cliente / Proveedor'] for row in cursor.fetchall()]

            cursor.execute('SELECT DISTINCT "Familia" FROM chatbot_raw WHERE "Familia" IS NOT NULL ORDER BY "Familia"')
            valores['familias'] = [row['Familia'] for row in cursor.fetchall()]

            cursor.execute('SELECT DISTINCT "Articulo" FROM chatbot_raw WHERE "Articulo" IS NOT NULL ORDER BY "Articulo" LIMIT 50')
            valores['articulos'] = [row['Articulo'] for row in cursor.fetchall()]

    finally:
        try:
            conn.close()
        except Exception:
            pass

    return valores


def get_lista_proveedores():
    """Obtiene lista única de proveedores"""
    sql = """
        SELECT DISTINCT TRIM("Cliente / Proveedor") as proveedor
        FROM chatbot_raw
        WHERE "Cliente / Proveedor" IS NOT NULL AND TRIM("Cliente / Proveedor") != ''
        ORDER BY proveedor
    """
    df = ejecutar_consulta(sql)
    if df is not None and not df.empty:
        return ["Todos"] + df['proveedor'].tolist()
    return ["Todos"]


def get_lista_tipos_comprobante():
    """Obtiene lista única de tipos de comprobante"""
    sql = """
        SELECT DISTINCT TRIM("Tipo Comprobante") as tipo
        FROM chatbot_raw
        WHERE "Tipo Comprobante" IS NOT NULL AND TRIM("Tipo Comprobante") != ''
        ORDER BY tipo
    """
    df = ejecutar_consulta(sql)
    if df is not None and not df.empty:
        return ["Todos"] + df['tipo'].tolist()
    return ["Todos"]


def get_lista_articulos():
    """Obtiene lista única de artículos"""
    sql = """
        SELECT DISTINCT TRIM("Articulo") as articulo
        FROM chatbot_raw
        WHERE "Articulo" IS NOT NULL AND TRIM("Articulo") != ''
        ORDER BY articulo
    """
    df = ejecutar_consulta(sql)
    if df is not None and not df.empty:
        return ["Todos"] + df['articulo'].tolist()
    return ["Todos"]


def buscar_comprobantes(proveedor=None, tipo_comprobante=None, articulo=None, 
                        fecha_desde=None, fecha_hasta=None, texto_busqueda=None):
    """Búsqueda de comprobantes con filtros múltiples"""
    
    fecha_expr = _sql_fecha_expr()
    
    sql = f"""
        SELECT 
            "Tipo Comprobante" AS Tipo,
            "Nro. Comprobante" AS Nro_Factura,
            TO_CHAR({fecha_expr}, 'DD/MM/YYYY') AS Fecha,
            "Cliente / Proveedor" AS Proveedor,
            "Articulo",
            "Familia",
            "Cantidad",
            "Monto Neto" AS Monto
        FROM chatbot_raw
        WHERE 1=1
    """
    
    params = []
    
    if proveedor and proveedor != "Todos":
        prov_clean = proveedor.split('(')[0].strip()
        sql += ' AND LOWER(TRIM("Cliente / Proveedor")) LIKE LOWER(%s)'
        params.append(f"%{prov_clean}%")
    
    if tipo_comprobante and tipo_comprobante != "Todos":
        tipo_clean = tipo_comprobante.split('(')[0].strip()
        sql += ' AND LOWER(TRIM("Tipo Comprobante")) LIKE LOWER(%s)'
        params.append(f"%{tipo_clean}%")
    
    if articulo and articulo != "Todos":
        sql += ' AND LOWER(TRIM("Articulo")) LIKE LOWER(%s)'
        params.append(f"%{articulo.strip()}%")
    
    if fecha_desde:
        fecha_str = fecha_desde.strftime('%Y-%m-%d')
        sql += f" AND {fecha_expr} >= %s"
        params.append(fecha_str)
    
    if fecha_hasta:
        fecha_str = fecha_hasta.strftime('%Y-%m-%d')
        sql += f" AND {fecha_expr} <= %s"
        params.append(fecha_str)
    
    if texto_busqueda and texto_busqueda.strip():
        sql += """ AND (
            "Nro. Comprobante" LIKE %s 
            OR LOWER("Articulo") LIKE LOWER(%s)
            OR LOWER("Cliente / Proveedor") LIKE LOWER(%s)
        )"""
        texto = f"%{texto_busqueda.strip()}%"
        params.extend([texto, texto, texto])
    
    sql += f" ORDER BY {fecha_expr} DESC LIMIT 200"
    
    return ejecutar_consulta(sql, tuple(params) if params else None)


# =====================================================================
# FUNCIONES PARA DASHBOARD
# =====================================================================

def get_dashboard_totales(anio: int) -> dict:
    """Totales generales para métricas"""
    total_pesos = _sql_total_num_expr()
    total_usd = _sql_total_num_expr_usd()
    fecha_expr = _sql_fecha_expr()
    mon_expr = _sql_moneda_norm_expr()
    
    query = f"""
        SELECT 
            SUM(CASE WHEN {mon_expr} = '$' THEN {total_pesos} ELSE 0 END) AS Total_Pesos,
            SUM(CASE WHEN {mon_expr} = 'U$S' THEN {total_usd} ELSE 0 END) AS Total_USD,
            COUNT(DISTINCT "Cliente / Proveedor") AS Proveedores,
            COUNT(DISTINCT "Nro. Comprobante") AS Facturas
        FROM chatbot_raw
        WHERE EXTRACT(YEAR FROM {fecha_expr}) = %s
          AND ("Tipo Comprobante" = 'Compra Contado' OR "Tipo Comprobante" LIKE 'Compra%')
    """
    df = ejecutar_consulta(query, (anio,))
    if df is not None and not df.empty:
        row = df.iloc[0]
        return {
            'total_pesos': float(row['total_pesos']) if pd.notna(row['total_pesos']) else 0,
            'total_usd': float(row['total_usd']) if pd.notna(row['total_usd']) else 0,
            'proveedores': int(row['proveedores']) if pd.notna(row['proveedores']) else 0,
            'facturas': int(row['facturas']) if pd.notna(row['facturas']) else 0
        }
    return {'total_pesos': 0, 'total_usd': 0, 'proveedores': 0, 'facturas': 0}


def get_dashboard_top_proveedores(anio: int, limite: int = 10, moneda: str = "$") -> pd.DataFrame:
    """Top proveedores por monto"""
    fecha_expr = _sql_fecha_expr()
    mon_expr = _sql_moneda_norm_expr()

    mon = (moneda or "$").strip().upper()

    if mon in ("U$S", "USD", "U$$"):
        total_expr = _sql_total_num_expr_usd()
        moneda_where = f'{mon_expr} IN (\'U$S\', \'U$$\')'
        label_m = "U$S"
    else:
        total_expr = _sql_total_num_expr()
        moneda_where = f'{mon_expr} = \'$\''
        label_m = "$"

    query = f"""
        SELECT
            "Cliente / Proveedor" AS Proveedor,
            '{label_m}' AS Moneda,
            SUM({total_expr}) AS Total,
            COUNT(DISTINCT "Nro. Comprobante") AS Cantidad_Facturas
        FROM chatbot_raw
        WHERE EXTRACT(YEAR FROM {fecha_expr}) = %s
          AND ("Tipo Comprobante" = 'Compra Contado' OR "Tipo Comprobante" LIKE 'Compra%')
          AND "Cliente / Proveedor" IS NOT NULL
          AND {moneda_where}
        GROUP BY "Cliente / Proveedor"
        ORDER BY SUM({total_expr}) DESC
        LIMIT %s
    """
    return ejecutar_consulta(query, (anio, limite))


def get_top_10_proveedores_chatbot(moneda: str = None, anio: int = None, mes: str = None):
    """Top 10 proveedores para chatbot"""
    fecha_expr = _sql_fecha_expr()
    mon_expr = _sql_moneda_norm_expr()

    where_fecha = ""
    params = []

    if anio:
        where_fecha += f" AND EXTRACT(YEAR FROM {fecha_expr}) = %s"
        params.append(anio)

    if mes:
        where_fecha += f' AND "Mes" = %s'
        params.append(mes)

    if moneda and moneda.upper() in ("$", "UYU", "PESOS"):
        total_expr = _sql_total_num_expr()

        sql = f"""
            SELECT
                "Cliente / Proveedor" AS Proveedor,
                '$' AS Moneda,
                SUM({total_expr}) AS Total,
                COUNT(DISTINCT "Nro. Comprobante") AS Facturas
            FROM chatbot_raw
            WHERE
                ("Tipo Comprobante" = 'Compra Contado' OR "Tipo Comprobante" LIKE 'Compra%')
                AND "Cliente / Proveedor" IS NOT NULL
                AND {mon_expr} = '$'
                {where_fecha}
            GROUP BY "Cliente / Proveedor"
            ORDER BY Total DESC
            LIMIT 10
        """
        return ejecutar_consulta(sql, tuple(params))

    if moneda and moneda.upper() in ("U$S", "USD", "U$$"):
        total_expr = _sql_total_num_expr_usd()

        sql = f"""
            SELECT
                "Cliente / Proveedor" AS Proveedor,
                'U$S' AS Moneda,
                SUM({total_expr}) AS Total,
                COUNT(DISTINCT "Nro. Comprobante") AS Facturas
            FROM chatbot_raw
            WHERE
                ("Tipo Comprobante" = 'Compra Contado' OR "Tipo Comprobante" LIKE 'Compra%')
                AND "Cliente / Proveedor" IS NOT NULL
                AND {mon_expr} IN ('U$S','U$$')
                {where_fecha}
            GROUP BY "Cliente / Proveedor"
            ORDER BY Total DESC
            LIMIT 10
        """
        return ejecutar_consulta(sql, tuple(params))

    total_pesos = _sql_total_num_expr()
    total_usd = _sql_total_num_expr_usd()

    sql = f"""
        SELECT
            "Cliente / Proveedor" AS Proveedor,
            {mon_expr} AS Moneda,
            SUM(
                CASE
                    WHEN {mon_expr} = '$' THEN {total_pesos}
                    WHEN {mon_expr} IN ('U$S','U$$') THEN {total_usd}
                    ELSE 0
                END
            ) AS Total,
            COUNT(DISTINCT "Nro. Comprobante") AS Facturas
        FROM chatbot_raw
        WHERE
            ("Tipo Comprobante" = 'Compra Contado' OR "Tipo Comprobante" LIKE 'Compra%')
            AND "Cliente / Proveedor" IS NOT NULL
            AND {mon_expr} IN ('$', 'U$S', 'U$$')
            {where_fecha}
        GROUP BY "Cliente / Proveedor", {mon_expr}
        ORDER BY Total DESC
        LIMIT 10
    """
    return ejecutar_consulta(sql, tuple(params))
