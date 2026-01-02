# =====================================================================
# 📚 MÓDULO ARTÍCULOS - FERTI CHAT
# Archivo: articulos.py
#
# Objetivo:
# - LISTAR artículos ya creados desde tabla Supabase: public.articulos (estructura GNS)
# - Permite buscar, seleccionar y adjuntar imágenes/manuales (Storage)
#
# Requiere:
# - supabase_client.py con objeto: supabase
# - Tabla (Supabase/Postgres): articulos
# - Bucket Storage (Supabase): "articulos"
# - Tabla articulo_archivos (opcional)
# =====================================================================

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import uuid

from supabase_client import supabase  # NO cambiar

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
except Exception:
    AgGrid = None


# =====================================================================
# CONFIG
# =====================================================================
BUCKET_ARTICULOS = "articulos"
TABLE_ARTICULOS_GNS = "articulos"


COL_ALIASES = {
    "id": ["id", "Id", "ID"],
    "descripcion": ["descripcion", "Descripcion", "Descripción"],
    "familia": ["familia", "Familia"],
    "codigo_int": ["Codigo Int.", "Código Int.", "codigo_int"],
    "codigo_ext": ["Codigo Ext.", "Código Ext.", "codigo_ext"],
    "unidad": ["unidad", "Unidad"],
    "tipo_articulo": ["Tipo Articulo", "Tipo Artículo"],
    "tipo_impuesto": ["Tipo Impuesto"],
    "tipo_concepto": ["Tipo Concepto"],
    "cuenta_compra": ["Cuenta Compra"],
    "cuenta_venta": ["Cuenta Venta"],
    "cuenta_venta_exe": ["Cuenta Venta Exe.", "Cuenta Venta Exe"],
    "cuenta_costo_venta": ["Cuenta Costo Venta"],
    "proveedor": ["Proveedor"],
    "activo": ["Activo"],
    "mueve_stock": ["Mueve Stock"],
    "ecommerce": ["e-Commerce", "ecommerce"],
    "stock_minimo": ["Stock Minimo", "Stock Mínimo"],
    "stock_maximo": ["Stock Maximo", "Stock Máximo"],
    "costo_fijo": ["Costo Fijo"],
}


# =====================================================================
# SUPABASE HELPERS
# =====================================================================
def _sb_select(
    table: str,
    columns: str = "*",
    filters: Optional[List[Tuple[str, str, Any]]] = None,
) -> pd.DataFrame:
    q = supabase.table(table).select(columns)
    if filters:
        for col, op, val in filters:
            if op == "eq":
                q = q.eq(col, val)
    res = q.execute()
    return pd.DataFrame(getattr(res, "data", []) or [])


def _sb_insert_archivo(payload: Dict[str, Any]) -> None:
    supabase.table("articulo_archivos").insert(payload).execute()


def _sb_upload_storage(bucket: str, path: str, content: bytes, mime: str) -> None:
    supabase.storage.from_(bucket).upload(
        path,
        content,
        file_options={"content-type": mime or "application/octet-stream"},
    )


# =====================================================================
# NORMALIZACIÓN
# =====================================================================
def _find_col(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    for a in aliases:
        if a in df.columns:
            return a
    norm = {c.lower().strip(): c for c in df.columns}
    for a in aliases:
        k = a.lower().strip()
        if k in norm:
            return norm[k]
    return None


def _normalize(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=COL_ALIASES.keys())

    out = pd.DataFrame()
    for key, aliases in COL_ALIASES.items():
        col = _find_col(df_raw, aliases)
        out[key] = df_raw[col] if col else None

    for b in ["activo", "mueve_stock", "ecommerce"]:
        if b in out.columns:
            out[b] = out[b].astype(str).str.lower().isin(
                ["1", "true", "t", "x", "si", "sí", "yes"]
            )

    out["id"] = out["id"].astype(str)
    out["descripcion"] = out["descripcion"].astype(str)
    out = out.sort_values("descripcion")

    return out.reset_index(drop=True)


# =====================================================================
# CACHE
# =====================================================================
@st.cache_data(ttl=30)
def _cache_articulos() -> pd.DataFrame:
    df = _sb_select(TABLE_ARTICULOS_GNS, "*")
    return _normalize(df)


def _invalidate_cache():
    _cache_articulos.clear()


# =====================================================================
# GRID
# =====================================================================
def _grid(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    if df is None or df.empty:
        st.info("Sin artículos para mostrar.")
        return None

    st.caption(f"Mostrando {len(df)} artículo(s).")

    if AgGrid is None:
        st.dataframe(df, use_container_width=True, height=420)
        return None

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection("single", use_checkbox=True)
    grid = AgGrid(
        df,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        height=420,
    )

    sel = grid.get("selected_rows") or []
    return sel[0] if sel else None


# =====================================================================
# ARCHIVOS
# =====================================================================
def _ui_archivos(articulo_id: str):
    st.markdown("### Archivos")

    col1, col2 = st.columns(2)

    with col1:
        img = st.file_uploader("Imagen", type=["png", "jpg", "jpeg"], key=f"img_{articulo_id}")
        if st.button("Subir imagen", key=f"btn_img_{articulo_id}"):
            if img:
                path = f"{articulo_id}/img_{uuid.uuid4().hex}"
                _sb_upload_storage(BUCKET_ARTICULOS, path, img.getvalue(), img.type)
                _sb_insert_archivo({
                    "articulo_id": articulo_id,
                    "tipo": "imagen",
                    "storage_bucket": BUCKET_ARTICULOS,
                    "storage_path": path,
                    "created_at": datetime.utcnow().isoformat(),
                })
                st.success("Imagen subida")

    with col2:
        pdf = st.file_uploader("Manual PDF", type=["pdf"], key=f"pdf_{articulo_id}")
        if st.button("Subir manual", key=f"btn_pdf_{articulo_id}"):
            if pdf:
                path = f"{articulo_id}/manual_{uuid.uuid4().hex}.pdf"
                _sb_upload_storage(BUCKET_ARTICULOS, path, pdf.getvalue(), pdf.type)
                _sb_insert_archivo({
                    "articulo_id": articulo_id,
                    "tipo": "manual",
                    "storage_bucket": BUCKET_ARTICULOS,
                    "storage_path": path,
                    "created_at": datetime.utcnow().isoformat(),
                })
                st.success("Manual subido")


# =====================================================================
# MAIN
# =====================================================================
def mostrar_articulos():
    st.title("📚 Artículos (GNS)")

    if "art_sel" not in st.session_state:
        st.session_state.art_sel = None
    if "art_buscar" not in st.session_state:
        st.session_state.art_buscar = ""

    tab1, tab2 = st.tabs(["📋 Listado", "🧾 Detalle / Archivos"])

    with tab1:
        c1, c2, c3 = st.columns([0.7, 0.15, 0.15])
        with c1:
            filtro = st.text_input(
                "Buscar (Descripción / Familia / Código / Proveedor)",
                key="art_buscar",
                placeholder="Vacío = muestra todos",
            )
        with c2:
            if st.button("Limpiar"):
                st.session_state.art_buscar = ""
                st.rerun()
        with c3:
            if st.button("Recargar"):
                _invalidate_cache()
                st.rerun()

        df = _cache_articulos()

        if filtro.strip():
            t = filtro.lower()
            df = df[df.apply(lambda r: t in r.astype(str).str.lower().to_string(), axis=1)]

        sel = _grid(df)
        if sel:
            st.session_state.art_sel = sel["id"]
            st.info("Artículo seleccionado")

    with tab2:
        if not st.session_state.art_sel:
            st.info("Seleccioná un artículo en el listado")
            return

        df = _cache_articulos()
        row = df[df["id"] == st.session_state.art_sel]
        if row.empty:
            st.warning("Artículo no encontrado")
            return

        st.write(row.iloc[0].to_dict())
        st.markdown("---")
        _ui_archivos(st.session_state.art_sel)
