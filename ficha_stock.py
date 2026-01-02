# =====================================================================
# 📒 MÓDULO FICHA DE STOCK - FERTI CHAT
# Archivo: ficha_stock.py
# =====================================================================

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from supabase_client import supabase


# =====================================================================
# Helpers
# =====================================================================

def _to_datetime_safe(x) -> Optional[pd.Timestamp]:
    if x is None or x == "":
        return None
    try:
        return pd.to_datetime(x)
    except Exception:
        return None


def _safe_float(x) -> float:
    try:
        if x is None or x == "":
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def _fmt_num(x, dec=2) -> str:
    try:
        return f"{float(x):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0"


def _fetch_articulos(q: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Requiere tabla 'articulos' con al menos: (id o Id), nombre.
    Opcionales: codigo_interno.
    """
    q = (q or "").strip()

    def _run_select(select_str: str) -> List[Dict[str, Any]]:
        query = supabase.table("articulos").select(select_str)
        if q:
            query = query.or_(f"nombre.ilike.%{q}%,codigo_interno.ilike.%{q}%")
        resp = query.limit(limit).execute()
        return resp.data or []

    try:
        # Caso normal (columna id)
        return _run_select("id,nombre,codigo_interno")
    except Exception:
        try:
            # Caso Supabase con Id (I mayúscula) -> alias a id
            return _run_select("Id:id,nombre,codigo_interno")
        except Exception as e:
            st.error(f"No pude leer 'articulos' desde Supabase. Error: {e}")
            return []


def _fetch_movimientos(
    articulo_id: Any,
    fecha_desde: Optional[date],
    fecha_hasta: Optional[date]
) -> List[Dict[str, Any]]:
    """
    Requiere tabla 'movimientos_stock' con columnas sugeridas:
    - id, articulo_id, fecha_hora, tipo_mov
    - deposito_id (o deposito_origen_id/deposito_destino_id)
    - qty_base (entrada + / salida -)
    - lote, vencimiento
    - ref_tipo, ref_nro, proveedor/proveedor_id, usuario, observacion
    - precio_unit_aplicado, moneda
    """
    try:
        sel = (
            "id,articulo_id,fecha_hora,tipo_mov,"
            "deposito_id,deposito_origen_id,deposito_destino_id,"
            "qty_base,unidad_mov,factor_conversion,"
            "lote,vencimiento,"
            "ref_tipo,ref_nro,proveedor,proveedor_id,usuario,observacion,"
            "precio_unit_aplicado,moneda"
        )

        q = supabase.table("movimientos_stock").select(sel).eq("articulo_id", articulo_id)

        if fecha_desde:
            q = q.gte("fecha_hora", datetime.combine(fecha_desde, datetime.min.time()).isoformat())
        if fecha_hasta:
            q = q.lte("fecha_hora", datetime.combine(fecha_hasta, datetime.max.time()).isoformat())

        resp = q.order("fecha_hora", desc=False).execute()
        return resp.data or []
    except Exception as e:
        st.error(f"No pude leer 'movimientos_stock' desde Supabase. Error: {e}")
        return []


def _calcular_kardex_promedio_movil(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula:
    - qty_in / qty_out
    - costo_promedio móvil
    - costo_unit_aplicado en BAJAS (usa costo_promedio previo)
    - valor_mov (positivo entradas / negativo salidas)
    - saldo_qty / saldo_valor
    """
    if df.empty:
        return df

    df = df.copy()

    # Normaliza fecha
    if "fecha_hora" in df.columns:
        df["fecha_hora_dt"] = df["fecha_hora"].apply(_to_datetime_safe)
    else:
        df["fecha_hora_dt"] = None

    # qty_base
    if "qty_base" not in df.columns:
        df["qty_base"] = 0
    df["qty_base"] = df["qty_base"].apply(_safe_float)

    # Entradas / salidas
    df["qty_in"] = df["qty_base"].apply(lambda x: x if x > 0 else 0)
    df["qty_out"] = df["qty_base"].apply(lambda x: abs(x) if x < 0 else 0)

    # Precio entrada
    if "precio_unit_aplicado" not in df.columns:
        df["precio_unit_aplicado"] = 0
    df["precio_unit_aplicado"] = df["precio_unit_aplicado"].apply(_safe_float)

    saldo_qty = 0.0
    saldo_valor = 0.0
    costo_prom = 0.0

    costo_unit_baja: List[float] = []
    valor_mov: List[float] = []
    saldo_qty_list: List[float] = []
    saldo_valor_list: List[float] = []
    costo_prom_list: List[float] = []

    for _, r in df.iterrows():
        qty = _safe_float(r.get("qty_base", 0))
        precio_in = _safe_float(r.get("precio_unit_aplicado", 0))
        costo_previo = costo_prom

        if qty > 0:
            v = qty * precio_in
            saldo_qty += qty
            saldo_valor += v
        elif qty < 0:
            q_out = abs(qty)
            v = -1 * q_out * costo_previo
            saldo_qty -= q_out
            saldo_valor += v
        else:
            v = 0.0

        if saldo_qty > 0:
            costo_prom = saldo_valor / saldo_qty
        else:
            costo_prom = 0.0
            saldo_valor = 0.0

        costo_unit_baja.append(costo_previo if qty < 0 else 0.0)
        valor_mov.append(v)
        saldo_qty_list.append(saldo_qty)
        saldo_valor_list.append(saldo_valor)
        costo_prom_list.append(costo_prom)

    df["costo_unit_aplicado"] = costo_unit_baja
    df["valor_mov"] = valor_mov
    df["saldo_qty"] = saldo_qty_list
    df["saldo_valor"] = saldo_valor_list
    df["costo_promedio"] = costo_prom_list

    return df


# =====================================================================
# UI principal (MEJORADA)
# =====================================================================

def mostrar_ficha_stock():
    # -------------------------
    # CSS SOLO para esta vista
    # -------------------------
    st.markdown("""
    <style>
    .fs-title{
        font-size: 1.6rem;
        font-weight: 800;
        margin: 0.2rem 0 0.8rem 0;
        display:flex;
        gap:.6rem;
        align-items:center;
    }
    .fs-sub{
        color: rgba(0,0,0,0.55);
        margin-top:-.4rem;
        margin-bottom: 1rem;
        font-size: .95rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]{
        border-radius: 16px !important;
        border: 1px solid rgba(0,0,0,0.08) !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.04) !important;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stDateInput"] input{
        border-radius: 12px !important;
    }
    div[data-testid="stDataFrame"]{
        border-radius: 14px !important;
        overflow: hidden !important;
        border: 1px solid rgba(0,0,0,0.08) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="fs-title">📒 Ficha de stock</div>', unsafe_allow_html=True)
    st.markdown('<div class="fs-sub">Kardex por artículo • Entradas/Salidas • Saldo y valorización (costo promedio móvil)</div>', unsafe_allow_html=True)

    # -------------------------
    # Filtros (tarjeta)
    # -------------------------
    with st.container(border=True):
        c1, c2, c3 = st.columns([2.2, 1, 1])

        with c1:
            st.caption("Buscar artículo")
            q = st.text_input(
                "Buscar artículo (nombre o código interno):",
                value="",
                placeholder="Ej: Roche, Pepito, 12345",
                label_visibility="collapsed"
            )

        with c2:
            st.caption("Desde (opcional)")
            fecha_desde = st.date_input("Desde", value=None, label_visibility="collapsed")

        with c3:
            st.caption("Hasta (opcional)")
            fecha_hasta = st.date_input("Hasta", value=None, label_visibility="collapsed")

        mostrar_avanzado = st.toggle("Mostrar columnas avanzadas", value=False)

    # -------------------------
    # Datos: artículos
    # -------------------------
    articulos = _fetch_articulos(q, limit=80)

    if not articulos:
        st.info("No hay artículos para mostrar (o no se encontró el texto buscado).")
        return

    opciones = []
    mapa = {}
    for a in articulos:
        nombre = a.get("nombre", "")
        cod = a.get("codigo_interno", "")
        label = f"{nombre}  |  {cod}" if cod else nombre
        opciones.append(label)
        mapa[label] = a

    sel = st.selectbox("Seleccionar artículo:", opciones, index=0)
    art = mapa.get(sel, {})
    articulo_id = art.get("id")

    if articulo_id is None:
        st.error("El artículo seleccionado no tiene 'id'.")
        return

    nombre_sel = art.get("nombre", "")
    cod_sel = art.get("codigo_interno", "")
    st.caption(
        f"Artículo: **{nombre_sel}**"
        + (f" • Código: **{cod_sel}**" if cod_sel else "")
        + f" • ID: **{articulo_id}**"
    )

    # -------------------------
    # Datos: movimientos
    # -------------------------
    movs = _fetch_movimientos(articulo_id, fecha_desde, fecha_hasta)

    if not movs:
        st.warning("No hay movimientos para este artículo en el rango seleccionado.")
        return

    df = pd.DataFrame(movs)

    if "fecha_hora" in df.columns:
        df["fecha_hora_dt"] = df["fecha_hora"].apply(_to_datetime_safe)
        df = df.sort_values(by=["fecha_hora_dt", "id"], ascending=[True, True], na_position="last")

    df_k = _calcular_kardex_promedio_movil(df)

    # -------------------------
    # Resumen
    # -------------------------
    stock_final = float(df_k["saldo_qty"].iloc[-1]) if not df_k.empty else 0.0
    valor_final = float(df_k["saldo_valor"].iloc[-1]) if not df_k.empty else 0.0
    costo_final = float(df_k["costo_promedio"].iloc[-1]) if not df_k.empty else 0.0

    with st.container(border=True):
        a, b, c, d = st.columns([1, 1, 1, 1])
        a.metric("Stock actual", f"{_fmt_num(stock_final, 2)}")
        b.metric("Valor stock", f"$ {_fmt_num(valor_final, 2)}")
        c.metric("Costo promedio", f"$ {_fmt_num(costo_final, 4)}")
        d.metric("Movimientos", f"{len(df_k)}")

    # -------------------------
    # Tabla “humana”
    # -------------------------
    df_view = df_k.copy()

    rename_map = {
        "fecha_hora": "Fecha",
        "tipo_mov": "Tipo",
        "lote": "Lote",
        "vencimiento": "Vencimiento",
        "qty_in": "Entrada",
        "qty_out": "Salida",
        "qty_base": "Cantidad (base)",
        "precio_unit_aplicado": "Precio entrada",
        "costo_unit_aplicado": "Costo baja",
        "valor_mov": "Valor mov.",
        "saldo_qty": "Saldo qty",
        "saldo_valor": "Saldo $",
        "ref_tipo": "Ref tipo",
        "ref_nro": "Ref nro",
        "proveedor": "Proveedor",
        "usuario": "Usuario",
        "observacion": "Obs",
        "deposito_id": "Depósito",
        "deposito_origen_id": "Origen",
        "deposito_destino_id": "Destino",
    }
    df_view = df_view.rename(columns={k: v for k, v in rename_map.items() if k in df_view.columns})

    cols_simple = [
        "Fecha", "Tipo", "Lote", "Vencimiento",
        "Entrada", "Salida", "Saldo qty",
        "Costo baja", "Precio entrada", "Valor mov.", "Saldo $",
        "Ref tipo", "Ref nro", "Proveedor", "Usuario", "Obs"
    ]
    cols_simple = [c for c in cols_simple if c in df_view.columns]

    cols_adv = cols_simple.copy()
    for extra in ["Depósito", "Origen", "Destino", "Cantidad (base)"]:
        if extra in df_view.columns and extra not in cols_adv:
            cols_adv.insert(4, extra)

    cols_show = cols_adv if mostrar_avanzado else cols_simple

    # Orden por fecha usando dt (si existe)
    if "fecha_hora_dt" in df_k.columns:
        df_view["_orden"] = df_k["fecha_hora_dt"]
        df_view = df_view.sort_values(by=["_orden"], ascending=True, na_position="last").drop(columns=["_orden"])

    st.dataframe(
        df_view[cols_show],
        use_container_width=True,
        hide_index=True
    )

    # -------------------------
    # Descarga
    # -------------------------
    with st.expander("⬇️ Descargar", expanded=False):
        csv = df_view[cols_show].to_csv(index=False).encode("utf-8")
        st.download_button(
            "Descargar ficha (CSV)",
            data=csv,
            file_name=f"ficha_stock_articulo_{articulo_id}.csv",
            mime="text/csv",
            use_container_width=True
        )
