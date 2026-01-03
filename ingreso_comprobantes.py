# =====================================================================
# 📥 MÓDULO: INGRESO DE COMPROBANTES - FERTI CHAT
# Archivo: ingreso_comprobantes.py
# =====================================================================

import streamlit as st
import pandas as pd
from datetime import date
import os
import re
import io

from supabase import create_client

# PDF (ReportLab)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# =====================================================================
# CONFIGURACIÓN SUPABASE
# =====================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    supabase = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLA_COMPROBANTES = "comprobantes_compras"
TABLA_DETALLE = "comprobantes_detalle"
TABLA_STOCK = "stock"
TABLA_PROVEEDORES = "proveedores"
TABLA_ARTICULOS = "articulos"

# =====================================================================
# HELPERS
# =====================================================================

def _safe_float(x, default=0.0) -> float:
    try:
        if x is None or x == "":
            return float(default)
        return float(x)
    except Exception:
        return float(default)

def _safe_int(x, default=0) -> int:
    try:
        if x is None or x == "":
            return int(default)
        return int(x)
    except Exception:
        return int(default)

def _iva_rate_from_tipo(iva_tipo: str) -> float:
    if iva_tipo == "Exento":
        return 0.0
    if iva_tipo == "10%":
        return 0.10
    if iva_tipo == "22%":
        return 0.22
    return 0.0

def _map_iva_tipo_from_articulo_row(row: dict) -> str:
    """
    Lee IVA desde la fila del artículo, especialmente desde:
    - "Tipo Impuesto" (ej: "1- Exento 0%", "IVA 10%", "IVA 22%")
    Devuelve: "Exento" / "10%" / "22%"
    """
    if not row:
        return "22%"

    candidates = [
        "Tipo Impuesto", "tipo impuesto", "tipo_impuesto",
        "tipo_impuesto_text", "TipoImpuesto",
        "iva_tipo", "IVA", "iva", "tasa_iva", "Tasa IVA"
    ]

    val = None
    for k in candidates:
        if k in row and row.get(k) not in (None, ""):
            val = row.get(k)
            break

    if val is None:
        return "22%"

    # Numérico (0 / 0.1 / 0.22)
    if isinstance(val, (int, float)):
        f = _safe_float(val, 0.0)
        if abs(f - 0.0) < 1e-9:
            return "Exento"
        if abs(f - 0.10) < 1e-6:
            return "10%"
        return "22%"

    v_raw = str(val).strip()
    v = v_raw.lower()

    # Caso típico Supabase: "1- Exento 0%"
    # Capturamos si dice exento
    if "exent" in v or "exento" in v:
        return "Exento"

    # Buscar porcentajes explícitos
    if re.search(r"\b10\b", v) or "10%" in v:
        return "10%"
    if re.search(r"\b22\b", v) or "22%" in v:
        return "22%"

    # Si aparece 0% lo tratamos como Exento
    if "0%" in v or re.search(r"\b0\b", v):
        return "Exento"

    # Fallback: si arranca con "1-" suele ser exento
    if re.match(r"^\s*1\s*[-]", v):
        return "Exento"

    return "22%"

def _map_precio_sin_iva_from_articulo_row(row: dict) -> float:
    """
    Intenta leer precio unitario SIN IVA desde la fila del artículo.
    """
    if not row:
        return 0.0

    candidates = [
        "precio_unit_sin_iva", "precio_unitario_sin_iva", "precio_sin_iva",
        "precio_unitario", "precio",
        "costo", "costo_unitario"
    ]

    for k in candidates:
        if k in row and row.get(k) not in (None, ""):
            return _safe_float(row.get(k), 0.0)

    return 0.0

def _articulo_desc_from_row(row: dict) -> str:
    """
    Descripción usable del artículo.
    """
    if not row:
        return ""
    candidates = ["descripción", "Descripción", "descripcion", "nombre", "articulo", "Artículo", "detalle", "Detalle"]
    for k in candidates:
        if k in row and row.get(k) not in (None, ""):
            return str(row.get(k)).strip()
    if "id" in row and row.get("id"):
        return str(row.get("id"))
    return ""

def _articulo_label(row: dict) -> str:
    """
    Label visible en el selectbox (incluye id corto para evitar duplicados).
    """
    desc = _articulo_desc_from_row(row) or ""
    rid = str(row.get("id", "") or "")
    rid8 = rid[:8] if rid else ""
    if rid8:
        return f"{desc} [{rid8}]"
    return desc

def _calc_linea(cantidad: int, precio_unit_sin_iva: float, iva_rate: float, descuento_pct: float) -> dict:
    cantidad = _safe_int(cantidad, 0)
    precio_unit_sin_iva = _safe_float(precio_unit_sin_iva, 0.0)
    iva_rate = _safe_float(iva_rate, 0.0)
    descuento_pct = _safe_float(descuento_pct, 0.0)

    base = float(cantidad) * float(precio_unit_sin_iva)
    desc_monto = base * (descuento_pct / 100.0)
    subtotal = base - desc_monto
    iva_monto = subtotal * iva_rate
    total = subtotal + iva_monto

    return {
        "base_sin_iva": base,
        "descuento_monto": desc_monto,
        "subtotal_sin_iva": subtotal,
        "iva_monto": iva_monto,
        "total_con_iva": total,
    }

def _fmt_money(v: float, moneda: str) -> str:
    v = _safe_float(v, 0.0)
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{moneda} {s}"

# =====================================================================
# CACHE SUPABASE (LISTAS)
# =====================================================================

@st.cache_data(ttl=600)
def _cache_proveedores() -> list:
    if not supabase:
        return []
    out = []
    start = 0
    page = 1000
    max_rows = 20000
    while start < max_rows:
        end = start + page - 1
        res = (
            supabase.table(TABLA_PROVEEDORES)
            .select("*")
            .order("nombre")
            .range(start, end)
            .execute()
        )
        batch = res.data or []
        out.extend(batch)
        if len(batch) < page:
            break
        start += page
    return out

@st.cache_data(ttl=600)
def _cache_articulos() -> list:
    if not supabase:
        return []
    out = []
    start = 0
    page = 1000
    max_rows = 20000
    while start < max_rows:
        end = start + page - 1
        res = (
            supabase.table(TABLA_ARTICULOS)
            .select("*")
            .range(start, end)
            .execute()
        )
        batch = res.data or []
        out.extend(batch)
        if len(batch) < page:
            break
        start += page
    return out

def _get_proveedor_options() -> tuple[list, dict]:
    data = _cache_proveedores()
    name_to_id = {}
    options = [""]
    for r in data:
        nombre = str(r.get("nombre", "") or "").strip()
        if not nombre:
            continue
        options.append(nombre)
        name_to_id[nombre] = r.get("id")
    return options, name_to_id

def _get_articulo_options() -> tuple[list, dict]:
    data = _cache_articulos()
    label_to_row = {}
    options = [""]
    for r in data:
        label = _articulo_label(r)
        if not label:
            continue
        options.append(label)
        label_to_row[label] = r
    return options, label_to_row

# =====================================================================
# STOCK
# =====================================================================

def _impactar_stock(articulo: str, cantidad: int) -> None:
    if not supabase:
        return

    articulo = (articulo or "").strip()
    if not articulo:
        return

    existe = (
        supabase.table(TABLA_STOCK)
        .select("id,cantidad")
        .eq("articulo", articulo)
        .execute()
    )

    if existe.data:
        stock_id = existe.data[0]["id"]
        cant_actual = existe.data[0].get("cantidad", 0) or 0
        nueva_cant = int(cant_actual) + int(cantidad)
        supabase.table(TABLA_STOCK).update({"cantidad": nueva_cant}).eq("id", stock_id).execute()
    else:
        supabase.table(TABLA_STOCK).insert({"articulo": articulo, "cantidad": int(cantidad)}).execute()

# =====================================================================
# INSERTS CON FALLBACK
# =====================================================================

def _insert_cabecera_con_fallback(cabecera_full: dict) -> dict:
    try:
        return supabase.table(TABLA_COMPROBANTES).insert(cabecera_full).execute()
    except Exception:
        pass

    cabecera_min = {
        "fecha": cabecera_full.get("fecha"),
        "proveedor": cabecera_full.get("proveedor"),
        "tipo_comprobante": cabecera_full.get("tipo_comprobante"),
        "nro_comprobante": cabecera_full.get("nro_comprobante"),
        "total": cabecera_full.get("total_calculado", cabecera_full.get("total", 0.0)),
        "usuario": cabecera_full.get("usuario"),
    }
    return supabase.table(TABLA_COMPROBANTES).insert(cabecera_min).execute()

def _insert_detalle_con_fallback(detalle_full: dict) -> None:
    try:
        supabase.table(TABLA_DETALLE).insert(detalle_full).execute()
        return
    except Exception:
        pass

    detalle_min = {
        "comprobante_id": detalle_full.get("comprobante_id"),
        "articulo": detalle_full.get("articulo"),
        "cantidad": detalle_full.get("cantidad"),
        "lote": detalle_full.get("lote", ""),
        "vencimiento": detalle_full.get("vencimiento", ""),
        "usuario": detalle_full.get("usuario"),
    }
    supabase.table(TABLA_DETALLE).insert(detalle_min).execute()

# =====================================================================
# PDF
# =====================================================================

def _generar_pdf_comprobante(cabecera: dict, items: list, moneda: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=28,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Comprobante de compra", styles["Title"]))
    story.append(Spacer(1, 10))

    # Cabecera
    proveedor = cabecera.get("proveedor", "")
    nro = cabecera.get("nro_comprobante", "")
    tipo = cabecera.get("tipo_comprobante", "")
    fecha = cabecera.get("fecha", "")
    condicion = cabecera.get("condicion_pago", "")

    story.append(Paragraph(f"<b>Proveedor:</b> {proveedor}", styles["Normal"]))
    story.append(Paragraph(f"<b>Nº Comprobante:</b> {nro}", styles["Normal"]))
    story.append(Paragraph(f"<b>Tipo:</b> {tipo}", styles["Normal"]))
    story.append(Paragraph(f"<b>Fecha:</b> {fecha}", styles["Normal"]))
    if condicion:
        story.append(Paragraph(f"<b>Condición:</b> {condicion}", styles["Normal"]))
    story.append(Paragraph(f"<b>Moneda:</b> {moneda}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Tabla items
    data = [["Artículo", "Cant.", "P.Unit s/IVA", "IVA", "Desc.%", "Subtotal", "Impuestos", "Total"]]
    subtotal = 0.0
    iva_total = 0.0
    desc_total = 0.0
    total = 0.0

    for it in items:
        art = it.get("articulo", "")
        cant = it.get("cantidad", 0)
        pu = _safe_float(it.get("precio_unit_sin_iva", 0.0), 0.0)
        iva_tipo = it.get("iva_tipo", "22%")
        desc = _safe_float(it.get("descuento_pct", 0.0), 0.0)
        sub = _safe_float(it.get("subtotal_sin_iva", 0.0), 0.0)
        imp = _safe_float(it.get("iva_monto", 0.0), 0.0)
        tot = _safe_float(it.get("total_con_iva", 0.0), 0.0)
        descm = _safe_float(it.get("descuento_monto", 0.0), 0.0)

        subtotal += sub
        iva_total += imp
        total += tot
        desc_total += descm

        data.append([
            str(art),
            str(cant),
            f"{pu:,.2f}",
            str(iva_tipo),
            f"{desc:,.2f}",
            f"{sub:,.2f}",
            f"{imp:,.2f}",
            f"{tot:,.2f}",
        ])

    tbl = Table(data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
    ]))

    story.append(tbl)
    story.append(Spacer(1, 12))

    # Totales
    tot_tbl = Table([
        ["SUB TOTAL", f"{moneda} {subtotal:,.2f}"],
        ["DESC./REC.", f"{moneda} {desc_total:,.2f}"],
        ["IMPUESTOS", f"{moneda} {iva_total:,.2f}"],
        ["TOTAL", f"{moneda} {total:,.2f}"],
    ], colWidths=[100, 140])

    tot_tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))

    story.append(tot_tbl)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# =====================================================================
# FUNCIÓN PRINCIPAL DEL MÓDULO
# =====================================================================

def mostrar_ingreso_comprobantes():
    st.title("📥 Ingreso de comprobantes")

    usuario_actual = st.session_state.get(
        "usuario",
        st.session_state.get("user", "desconocido")
    )

    if not supabase:
        st.warning("Supabase no configurado.")
        st.stop()

    if "comp_items" not in st.session_state:
        st.session_state.comp_items = []

    if "comp_moneda" not in st.session_state:
        st.session_state.comp_moneda = "UYU"

    if "comp_condicion_pago" not in st.session_state:
        st.session_state.comp_condicion_pago = "Contado"

    menu = st.radio(
        "Modo:",
        ["🧾 Ingreso manual", "📄 Carga por archivo (CSV/PDF)"],
        horizontal=True
    )

    # =========================
    # INGRESO MANUAL
    # =========================
    if menu == "🧾 Ingreso manual":

        proveedores_options, prov_name_to_id = _get_proveedor_options()
        articulos_options, art_label_to_row = _get_articulo_options()

        with st.form("form_comprobante"):

            # Cabecera: N° Comprobante al lado de Proveedor
            col1, col2, col3 = st.columns(3)

            with col1:
                fecha = st.date_input("Fecha", value=date.today())

                cprov, cnro = st.columns([2, 1])
                with cprov:
                    proveedor_sel = st.selectbox(
                        "Proveedor",
                        proveedores_options,
                        index=0,
                        key="comp_proveedor_sel"
                    )
                with cnro:
                    nro_comprobante = st.text_input("Nº Comprobante")

            with col2:
                tipo_comprobante = st.selectbox(
                    "Tipo",
                    ["Factura", "Remito", "Nota de Crédito"]
                )
                condicion_pago = st.selectbox(
                    "Condición",
                    ["Contado", "Crédito"],
                    index=0 if st.session_state.comp_condicion_pago == "Contado" else 1,
                    key="comp_condicion_pago"
                )

            with col3:
                moneda = st.selectbox(
                    "Moneda",
                    ["UYU", "USD"],
                    index=0 if st.session_state.comp_moneda == "UYU" else 1,
                    key="comp_moneda"
                )

            st.markdown("### 📦 Artículos")

            c1, c2, c3, c4, c5, c6, c7 = st.columns([2.6, 1, 1.2, 1.1, 1.1, 1.2, 1.4])
            with c1:
                articulo_sel = st.selectbox(
                    "Artículo",
                    articulos_options,
                    index=0,
                    key="comp_articulo_sel"
                )
            with c2:
                cantidad = st.number_input("Cantidad", min_value=1, step=1)
            with c3:
                precio_unit_sin_iva = st.number_input("Precio unit. s/IVA", min_value=0.0, step=0.01)
            with c4:
                # Se muestra, pero al agregar se pisará por el IVA del artículo
                iva_tipo = st.selectbox("IVA", ["Exento", "10%", "22%"], index=2)
            with c5:
                descuento_pct = st.number_input("Desc. %", min_value=0.0, max_value=100.0, step=0.5)
            with c6:
                lote = st.text_input("Lote")
            with c7:
                vencimiento = st.date_input("Vencimiento")

            btn_add = st.form_submit_button("➕ Agregar artículo")
            guardar = st.form_submit_button("💾 Guardar comprobante")

        # ----------------------------------
        # Agregar artículo (IVA y precio salen del artículo)
        # ----------------------------------
        if btn_add:
            if not proveedor_sel:
                st.error("Seleccioná un proveedor.")
            elif not articulo_sel:
                st.error("Seleccioná un artículo.")
            else:
                art_row = art_label_to_row.get(articulo_sel, {})
                art_desc = _articulo_desc_from_row(art_row) or articulo_sel
                art_id = art_row.get("id")

                # IVA desde artículo (fuerte)
                iva_tipo_final = _map_iva_tipo_from_articulo_row(art_row)
                iva_rate = _iva_rate_from_tipo(iva_tipo_final)

                # Precio desde artículo SOLO si el usuario dejó 0
                if _safe_float(precio_unit_sin_iva, 0.0) <= 0.0:
                    precio_db = _map_precio_sin_iva_from_articulo_row(art_row)
                    if precio_db > 0:
                        precio_unit_sin_iva = float(precio_db)

                calc = _calc_linea(int(cantidad), float(precio_unit_sin_iva), float(iva_rate), float(descuento_pct))

                st.session_state.comp_items.append({
                    "articulo": art_desc,
                    "articulo_id": art_id,
                    "cantidad": int(cantidad),
                    "precio_unit_sin_iva": float(precio_unit_sin_iva),
                    "iva_tipo": iva_tipo_final,
                    "iva_rate": float(iva_rate),
                    "descuento_pct": float(descuento_pct),
                    "descuento_monto": float(calc["descuento_monto"]),
                    "subtotal_sin_iva": float(calc["subtotal_sin_iva"]),
                    "iva_monto": float(calc["iva_monto"]),
                    "total_con_iva": float(calc["total_con_iva"]),
                    "lote": (lote or "").strip(),
                    "vencimiento": str(vencimiento),
                    "moneda": st.session_state.comp_moneda,
                })

        # ----------------------------------
        # Vista items (más compacta)
        # ----------------------------------
        if st.session_state.comp_items:
            df_items = pd.DataFrame(st.session_state.comp_items)

            df_show = df_items.copy()
            rename_map = {
                "articulo": "articulo",
                "cantidad": "cantidad",
                "precio_unit_sin_iva": "precio_unit_sin_iva",
                "iva_tipo": "iva_tipo",
                "descuento_pct": "descuento_pct",
                "subtotal_sin_iva": "subtotal_sin_iva",
                "iva_monto": "iva_monto",
                "total_con_iva": "total_con_iva",
                "lote": "lote",
                "vencimiento": "vencimiento",
            }
            df_show = df_show[list(rename_map.keys())].rename(columns=rename_map)

            st.dataframe(df_show, use_container_width=True, hide_index=True, height=180)

            moneda_actual = st.session_state.comp_moneda
            subtotal = float(df_items["subtotal_sin_iva"].sum())
            iva_total = float(df_items["iva_monto"].sum())
            total_calculado = float(df_items["total_con_iva"].sum())
            desc_total = float(df_items["descuento_monto"].sum()) if "descuento_monto" in df_items.columns else 0.0

            # Barra inferior compacta (tipo POS)
            st.markdown("")

            b1, b2, b3, b4 = st.columns([2.2, 2.2, 2.2, 2.4])

            with b1:
                st.caption("SUB TOTAL")
                st.text_input(
                    label="",
                    value=_fmt_money(subtotal, moneda_actual),
                    disabled=True,
                    label_visibility="collapsed",
                    key="sum_subtotal"
                )

            with b2:
                st.caption("DESC./REC.")
                st.text_input(
                    label="",
                    value=_fmt_money(desc_total, moneda_actual),
                    disabled=True,
                    label_visibility="collapsed",
                    key="sum_desc"
                )

            with b3:
                st.caption("IMPUESTOS")
                st.text_input(
                    label="",
                    value=_fmt_money(iva_total, moneda_actual),
                    disabled=True,
                    label_visibility="collapsed",
                    key="sum_iva"
                )

            with b4:
                st.caption("TOTAL")
                st.text_input(
                    label="",
                    value=_fmt_money(total_calculado, moneda_actual),
                    disabled=True,
                    label_visibility="collapsed",
                    key="sum_total"
                )

        # ----------------------------------
        # Guardar comprobante + generar PDF
        # ----------------------------------
        if guardar:
            if not proveedor_sel or not nro_comprobante or not st.session_state.comp_items:
                st.error("Faltan datos obligatorios.")
                st.stop()

            proveedor_nombre = str(proveedor_sel).strip()
            proveedor_id = prov_name_to_id.get(proveedor_nombre)
            nro_norm = str(nro_comprobante).strip()

            existe = (
                supabase.table(TABLA_COMPROBANTES)
                .select("id")
                .eq("proveedor", proveedor_nombre)
                .eq("nro_comprobante", nro_norm)
                .execute()
            )
            if existe.data:
                st.warning("Comprobante duplicado.")
                st.stop()

            df_items = pd.DataFrame(st.session_state.comp_items)
            subtotal = float(df_items["subtotal_sin_iva"].sum())
            iva_total = float(df_items["iva_monto"].sum())
            total_calculado = float(df_items["total_con_iva"].sum())

            moneda_actual = st.session_state.comp_moneda
            condicion_pago = st.session_state.comp_condicion_pago

            cabecera_full = {
                "fecha": str(fecha),
                "proveedor": proveedor_nombre,
                "proveedor_id": proveedor_id,
                "tipo_comprobante": tipo_comprobante,
                "nro_comprobante": nro_norm,
                "condicion_pago": condicion_pago,
                "usuario": str(usuario_actual),
                "moneda": moneda_actual,
                "subtotal": subtotal,
                "iva_total": iva_total,
                "total_calculado": total_calculado,
                "total": total_calculado,
            }

            res = _insert_cabecera_con_fallback(cabecera_full)
            comprobante_id = res.data[0]["id"]

            for item in st.session_state.comp_items:
                detalle_full = {
                    "comprobante_id": comprobante_id,
                    "articulo": item["articulo"],
                    "articulo_id": item.get("articulo_id"),
                    "cantidad": int(item["cantidad"]),
                    "lote": item.get("lote", ""),
                    "vencimiento": item.get("vencimiento", ""),
                    "usuario": str(usuario_actual),

                    "moneda": moneda_actual,
                    "precio_unit_sin_iva": float(item.get("precio_unit_sin_iva", 0.0)),
                    "iva_tipo": item.get("iva_tipo", "22%"),
                    "iva_rate": float(item.get("iva_rate", 0.22)),
                    "descuento_pct": float(item.get("descuento_pct", 0.0)),
                    "descuento_monto": float(item.get("descuento_monto", 0.0)),
                    "subtotal_sin_iva": float(item.get("subtotal_sin_iva", 0.0)),
                    "iva_monto": float(item.get("iva_monto", 0.0)),
                    "total_con_iva": float(item.get("total_con_iva", 0.0)),
                }

                _insert_detalle_con_fallback(detalle_full)
                _impactar_stock(detalle_full["articulo"], detalle_full["cantidad"])

            # PDF
            try:
                pdf_bytes = _generar_pdf_comprobante(cabecera_full, st.session_state.comp_items, moneda_actual)
                st.session_state["ultimo_pdf_comprobante"] = pdf_bytes
                st.session_state["ultimo_pdf_nombre"] = f"comprobante_{nro_norm}.pdf"
            except Exception:
                st.session_state["ultimo_pdf_comprobante"] = None
                st.session_state["ultimo_pdf_nombre"] = None

            st.success("Comprobante guardado correctamente.")
            st.session_state.comp_items = []

        # Botón descarga PDF (si existe)
        if st.session_state.get("ultimo_pdf_comprobante"):
            st.download_button(
                "⬇️ Descargar PDF del comprobante",
                data=st.session_state["ultimo_pdf_comprobante"],
                file_name=st.session_state.get("ultimo_pdf_nombre", "comprobante.pdf"),
                mime="application/pdf",
                use_container_width=True
            )

    # =========================
    # CARGA POR ARCHIVO
    # =========================
    else:
        archivo = st.file_uploader("Subir CSV o PDF", type=["csv", "pdf"])

        if archivo and archivo.name.lower().endswith(".csv"):
            df = pd.read_csv(archivo)
            st.dataframe(df, use_container_width=True, hide_index=True)

            if st.button("Importar CSV"):
                for _, row in df.iterrows():
                    proveedor_norm = str(row.get("proveedor", "")).strip()
                    nro_norm = str(row.get("nro_comprobante", "")).strip()

                    moneda_row = str(row.get("moneda", st.session_state.comp_moneda)).strip().upper()
                    if moneda_row not in ("UYU", "USD"):
                        moneda_row = st.session_state.comp_moneda

                    iva_tipo_row = str(row.get("iva_tipo", "22%")).strip()
                    iva_rate_row = _safe_float(row.get("iva_rate", _iva_rate_from_tipo(iva_tipo_row)), 0.0)
                    if iva_rate_row not in (0.0, 0.1, 0.22):
                        iva_rate_row = _iva_rate_from_tipo(iva_tipo_row)

                    cantidad_row = _safe_int(row.get("cantidad", 0), 0)
                    precio_row = _safe_float(row.get("precio_unit_sin_iva", 0.0), 0.0)
                    desc_pct_row = _safe_float(row.get("descuento_pct", 0.0), 0.0)

                    calc = _calc_linea(cantidad_row, precio_row, iva_rate_row, desc_pct_row)

                    cabecera_full = {
                        "fecha": str(row.get("fecha", "")),
                        "proveedor": proveedor_norm,
                        "tipo_comprobante": str(row.get("tipo", "")),
                        "nro_comprobante": nro_norm,
                        "usuario": str(usuario_actual),
                        "moneda": moneda_row,
                        "subtotal": float(calc["subtotal_sin_iva"]),
                        "iva_total": float(calc["iva_monto"]),
                        "total_calculado": float(calc["total_con_iva"]),
                        "total": float(calc["total_con_iva"]),
                    }

                    res = _insert_cabecera_con_fallback(cabecera_full)
                    comprobante_id = res.data[0]["id"]

                    detalle_full = {
                        "comprobante_id": comprobante_id,
                        "articulo": str(row.get("articulo", "")).strip(),
                        "cantidad": int(cantidad_row),
                        "lote": str(row.get("lote", "")).strip(),
                        "vencimiento": str(row.get("vencimiento", "")).strip(),
                        "usuario": str(usuario_actual),
                        "moneda": moneda_row,
                        "precio_unit_sin_iva": float(precio_row),
                        "iva_tipo": iva_tipo_row,
                        "iva_rate": float(iva_rate_row),
                        "descuento_pct": float(desc_pct_row),
                        "descuento_monto": float(calc["descuento_monto"]),
                        "subtotal_sin_iva": float(calc["subtotal_sin_iva"]),
                        "iva_monto": float(calc["iva_monto"]),
                        "total_con_iva": float(calc["total_con_iva"]),
                    }

                    _insert_detalle_con_fallback(detalle_full)
                    _impactar_stock(detalle_full["articulo"], detalle_full["cantidad"])

                st.success("CSV importado correctamente.")

        elif archivo:
            st.info("PDF cargado (no parseado).")
