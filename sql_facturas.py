# =========================
# SQL_FACTURAS.PY - CONSULTAS DE FACTURAS (VERSIÓN AJUSTADA ROCHE 2025)
# =========================

import re
import pandas as pd
from typing import List, Optional, Any
from sql_core import (
    ejecutar_consulta,
    _sql_total_num_expr_general,
)


# =====================================================================
# HELPERS DE NORMALIZACIÓN DE FACTURA
# =====================================================================

def _factura_variantes(nro_factura: str) -> List[str]:
    s = (nro_factura or "").strip().upper()
    if not s:
        return []
    variantes = [s]
    if s.isdigit():
        if len(s) <= 8:
            variantes.append("A" + s.zfill(8))
        if len(s) < 8:
            variantes.append(s.zfill(8))
    else:
        i = 0
        while i < len(s) and s[i].isalpha():
            i += 1
        pref = s[:i]
        dig = s[i:]
        if dig.isdigit() and dig:
            variantes.append(dig)
            variantes.append(dig.lstrip("0") or dig)
            if pref and len(dig) < 8:
                variantes.append(pref + dig.zfill(8))
    out: List[str] = []
    seen = set()
    for v in variantes:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _sql_monto_neto_num_expr() -> str:
    return """
        (
          CASE
            WHEN TRIM("Monto Neto") LIKE '(%'
              THEN -1 * REPLACE(
                         REPLACE(
                           REPLACE(TRIM("Monto Neto"), '(', ''),
                           ')', ''),
                         '.', ''),
                       ',', '.'
                 )::numeric
            ELSE REPLACE(
                   REPLACE(TRIM("Monto Neto"), '.', ''),
                   ',', '.'
                 )::numeric
          END
        )
    """


# =====================================================================
# DETALLE / TOTAL POR NÚMERO
# =====================================================================

def get_detalle_factura_por_numero(nro_factura: str) -> pd.DataFrame:
    total_expr = _sql_total_num_expr_general()
    sql = f"""
        SELECT
            TRIM("Nro. Comprobante") AS nro_factura,
            TRIM("Cliente / Proveedor") AS Proveedor,
            TRIM("Articulo") AS Articulo,
            "Fecha",
            "Cantidad",
            "Precio Unitario",
            "Moneda",
            {total_expr} AS Total
        FROM chatbot_raw
        WHERE TRIM("Nro. Comprobante") = %s
          AND TRIM("Nro. Comprobante") <> 'A0000000'
          AND (
            "Tipo Comprobante" = 'Compra Contado'
            OR "Tipo Comprobante" ILIKE 'Compra%%'
            OR "Tipo Comprobante" ILIKE 'Factura%%'
          )
        ORDER BY TRIM("Articulo")
    """
    variantes = _factura_variantes(nro_factura)
    if not variantes:
        return ejecutar_consulta(sql, ("",))
    df = ejecutar_consulta(sql, (variantes[0],))
    if df is not None and not df.empty:
        return df
    for alt in variantes[1:]:
        df2 = ejecutar_consulta(sql, (alt,))
        if df2 is not None and not df2.empty:
            df2.attrs["nro_factura_fallback"] = alt
            return df2
    return df if df is not None else pd.DataFrame()


def get_total_factura_por_numero(nro_factura: str) -> dict:
    total_expr = _sql_total_num_expr_general()
    sql = f"""
        SELECT 
            COALESCE(SUM({total_expr}), 0) AS total_factura,
            COUNT(*) AS lineas,
            TRIM("Moneda") AS Moneda
        FROM chatbot_raw
        WHERE TRIM("Nro. Comprobante") = %s
          AND (
            "Tipo Comprobante" = 'Compra Contado'
            OR "Tipo Comprobante" ILIKE 'Compra%%'
            OR "Tipo Comprobante" ILIKE 'Factura%%'
          )
        GROUP BY TRIM("Moneda")
    """
    variantes = _factura_variantes(nro_factura)
    if not variantes:
        return {"total": 0, "lineas": 0, "moneda": ""}
    df = ejecutar_consulta(sql, (variantes[0],))
    if df is None or df.empty:
        for alt in variantes[1:]:
            df2 = ejecutar_consulta(sql, (alt,))
            if df2 is not None and not df2.empty:
                df = df2
                break
    if df is not None and not df.empty:
        return {
            "total": float(df["total_factura"].iloc[0] or 0),
            "lineas": int(df["lineas"].iloc[0] or 0),
            "moneda": str(df["Moneda"].iloc[0] or "")
        }
    return {"total": 0, "lineas": 0, "moneda": ""}


# =====================================================================
# FACTURAS POR PROVEEDOR (la que usa “todas las facturas roche 2025”)
# =====================================================================

def get_facturas_proveedor(
    proveedores: List[str],
    meses: Optional[List[str]] = None,
    anios: Optional[List[int]] = None,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    articulo: Optional[str] = None,
    moneda: Optional[str] = None,
    limite: int = 5000,
) -> pd.DataFrame:
    if not proveedores:
        return pd.DataFrame()

    limite = int(limite or 5000)
    if limite <= 0:
        limite = 5000

    where_parts = [
        '"Tipo Comprobante" IN (\'Compra Crédito\', \'Nota de Crédito - Proveedor\')'
    ]
    params: List[Any] = []

    # Proveedores
    prov_clauses: List[str] = []
    for p in [str(x).strip() for x in proveedores if str(x).strip()]:
        p_clean = p.lower().strip()
        prov_clauses.append('LOWER(TRIM("Cliente / Proveedor")) LIKE %s')
        params.append(f"%{p_clean}%")
    where_parts.append("(" + " OR ".join(prov_clauses) + ")")

    # Artículo (opcional)
    if articulo and str(articulo).strip():
        where_parts.append('LOWER(TRIM("Articulo")) LIKE %s')
        params.append(f"%{str(articulo).lower().strip()}%")

    # Moneda (opcional)
    if moneda and str(moneda).strip():
        m = str(moneda).strip().upper()
        if m in ("USD", "U$S", "U$$", "US$"):
            where_parts.append('TRIM("Moneda") IN (\'U$S\', \'U$$\', \'USD\', \'US$\')')
        elif m in ("$", "PESOS", "UYU", "URU"):
            where_parts.append('TRIM("Moneda") = \'$\'')
        else:
            where_parts.append('UPPER(TRIM("Moneda")) LIKE %s')
            params.append(f"%{m}%")

    # Tiempo (rango > meses > años)
    if desde and hasta:
        where_parts.append('"Fecha"::date BETWEEN %s AND %s')
        params.extend([desde, hasta])
    else:
        if meses:
            meses_ok = [m for m in (meses or []) if m]
            if meses_ok:
                ph = ", ".join(["%s"] * len(meses_ok))
                where_parts.append(f'TRIM("Mes") IN ({ph})')
                params.extend(meses_ok)
        if (not meses) and anios:
            anios_ok = [int(a) for a in (anios or []) if a]
            if anios_ok:
                if len(anios_ok) == 1:
                    where_parts.append('"Año" = %s')
                    params.append(anios_ok[0])
                else:
                    ph = ", ".join(["%s"] * len(anios_ok))
                    where_parts.append(f'"Año" IN ({ph})')
                    params.extend(anios_ok)

    monto_expr = _sql_monto_neto_num_expr()

    query = f"""
        SELECT
          ROW_NUMBER() OVER (ORDER BY "Fecha"::date, "Nro. Comprobante") AS nro,
          TRIM("Cliente / Proveedor") AS proveedor,
          "Fecha",
          "Tipo Comprobante",
          "Nro. Comprobante",
          "Moneda",
          SUM({monto_expr}) AS monto_neto
        FROM chatbot_raw
        WHERE {" AND ".join(where_parts)}
        GROUP BY
          TRIM("Cliente / Proveedor"),
          "Fecha",
          "Tipo Comprobante",
          "Nro. Comprobante",
          "Moneda"
        ORDER BY nro
        LIMIT {limite};
    """

    # Debug y panel
    from sql_core import ejecutar_consulta as _exec  # ya importado arriba, pero por claridad

    try:
        import streamlit as st
        st.session_state["DBG_SQL_LAST_TAG"] = "facturas_proveedor"
        st.session_state["DBG_SQL_LAST_QUERY"] = query
        st.session_state["DBG_SQL_LAST_PARAMS"] = tuple(params)
    except Exception:
        pass

    print(f"DEBUG: Intentando consultar tabla 'chatbot_raw' con query: {query.strip()}")
    print(f"DEBUG: Parámetros: {tuple(params)}")

    return ejecutar_consulta(query, tuple(params))
