# =========================
# BAJASTOCK.PY - Baja de stock + Movimiento (traslado) con historial
# =========================

import streamlit as st
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# =========================
# CONEXIÓN A POSTGRESQL
# =========================
def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        sslmode="require"
    )


# =========================
# KEYS (EVITA COLISIONES CON OTROS MÓDULOS)
# =========================
K_PREFIX = "BAJASTOCK_"
K_ACCION = K_PREFIX + "ACCION"
K_BUSQ = K_PREFIX + "BUSQUEDA"
K_ITEM_SEL = K_PREFIX + "ITEM_SEL"
K_BTN_BUSCAR = K_PREFIX + "BTN_BUSCAR"

K_BAJA_DEP = K_PREFIX + "BAJA_DEP"
K_BAJA_FIFO = K_PREFIX + "BAJA_FIFO"
K_BAJA_LOTE_SEL = K_PREFIX + "BAJA_LOTE_SEL"
K_BAJA_CONFIRM_NO_FIFO = K_PREFIX + "BAJA_CONFIRM_NO_FIFO"
K_BAJA_CANT = K_PREFIX + "BAJA_CANT"

K_MOV_DEP_ORIG = K_PREFIX + "MOV_DEP_ORIG"
K_MOV_DEP_DEST = K_PREFIX + "MOV_DEP_DEST"
K_MOV_LOTE_SEL = K_PREFIX + "MOV_LOTE_SEL"
K_MOV_CONFIRM_NO_FIFO = K_PREFIX + "MOV_CONFIRM_NO_FIFO"
K_MOV_CANT = K_PREFIX + "MOV_CANT"


# =========================
# HELPERS
# =========================
def _norm_str(x) -> str:
    return ("" if x is None else str(x)).strip()


def _to_float(x) -> float:
    s = _norm_str(x)
    if not s:
        return 0.0
    s = s.replace(" ", "")
    limpio = "".join(ch for ch in s if ch.isdigit() or ch in [",", ".", "-"])
    if not limpio:
        return 0.0
    if "," in limpio and "." in limpio:
        limpio = limpio.replace(",", "")
    else:
        limpio = limpio.replace(",", ".")
    try:
        return float(limpio)
    except Exception:
        return 0.0


def _fmt_num(x: float) -> str:
    if x is None:
        return "0"
    try:
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        return f"{x:.2f}".rstrip("0").rstrip(".")
    except Exception:
        return "0"


def _parse_fecha_for_sort(venc_text: str):
    s = _norm_str(venc_text)
    if not s:
        return pd.Timestamp.max
    dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
    if pd.isna(dt):
        return pd.Timestamp.max
    return dt


def _sum_stock(filas, filtro_deposito: str = None, solo_casa_central: bool = False) -> float:
    total = 0.0
    for r in filas:
        dep = _norm_str(r.get("DEPOSITO"))
        if filtro_deposito is not None and dep != _norm_str(filtro_deposito):
            continue
        if solo_casa_central and ("casa central" not in dep.lower()):
            continue
        total += float(r.get("STOCK_NUM", 0.0) or 0.0)
    return total


# =========================
# REGLAS DEPÓSITO DESTINO POR FAMILIA (MOVIMIENTO)
# =========================
FAMILIA_A_DEPOSITO_DESTINO = {
    "G": "Generales",
    "XX": "Inmunoanalisis",
    "ID": "Inmunodiagnostico",
    "FB": "Microbiologia",
    "LP": "Limpieza",
    "AF": "Alejandra Fajardo",
    "CT": "Citometria",
}


def _sugerir_deposito_destino_por_familia(familia: str, depositos_disponibles: list) -> str:
    fam = _norm_str(familia).upper()
    sugerido = _norm_str(FAMILIA_A_DEPOSITO_DESTINO.get(fam, ""))
    if not sugerido:
        return ""

    disp_lower = {d.lower(): d for d in depositos_disponibles}
    if sugerido.lower() in disp_lower:
        return disp_lower[sugerido.lower()]
    return ""


# =========================
# TABLA HISTORIAL (BAJAS + MOVIMIENTOS)
# =========================
def crear_tabla_historial():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS historial_bajas (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(100),
            fecha DATE,
            hora TIME,
            codigo_interno VARCHAR(50),
            articulo VARCHAR(255),
            cantidad DECIMAL(10,2),
            motivo VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()

    # columnas extra (no rompe)
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS deposito VARCHAR(255)""")
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS lote VARCHAR(255)""")
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS vencimiento VARCHAR(255)""")
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS stock_antes_lote DECIMAL(14,4)""")
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS stock_despues_lote DECIMAL(14,4)""")
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS stock_total_articulo DECIMAL(14,4)""")
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS stock_total_deposito DECIMAL(14,4)""")
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS stock_casa_central DECIMAL(14,4)""")

    # distinguir BAJA vs MOVIMIENTO
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS tipo_registro VARCHAR(50)""")
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS deposito_origen VARCHAR(255)""")
    cur.execute("""ALTER TABLE historial_bajas ADD COLUMN IF NOT EXISTS deposito_destino VARCHAR(255)""")

    conn.commit()
    cur.close()
    conn.close()


# =========================
# STOCK (TABLA: stock)
# =========================
def buscar_items_stock(busqueda: str, limite_filas: int = 400):
    b = _norm_str(busqueda)
    if not b:
        return []

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            "FAMILIA",
            "CODIGO",
            "ARTICULO",
            "DEPOSITO",
            "LOTE",
            "VENCIMIENTO",
            "STOCK"
        FROM stock
        WHERE
            TRIM("CODIGO") = %s
            OR LOWER(TRIM("ARTICULO")) LIKE LOWER(%s)
        LIMIT %s
    """, (b, f"%{b}%", limite_filas))

    filas = cur.fetchall()
    cur.close()
    conn.close()

    agg = {}
    for r in filas:
        codigo = _norm_str(r.get("CODIGO"))
        articulo = _norm_str(r.get("ARTICULO"))
        familia = _norm_str(r.get("FAMILIA"))
        deposito = _norm_str(r.get("DEPOSITO"))
        stock_val = _to_float(r.get("STOCK"))

        key = (codigo, articulo, familia)
        if key not in agg:
            agg[key] = {
                "FAMILIA": familia,
                "CODIGO": codigo,
                "ARTICULO": articulo,
                "STOCK_TOTAL": 0.0,
                "DEPOSITOS": set()
            }
        agg[key]["STOCK_TOTAL"] += stock_val
        if deposito:
            agg[key]["DEPOSITOS"].add(deposito)

    items = list(agg.values())
    items.sort(key=lambda x: x.get("STOCK_TOTAL", 0.0), reverse=True)
    return items[:20]


def obtener_lotes_item(codigo: str, articulo: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            "FAMILIA",
            "CODIGO",
            "ARTICULO",
            "DEPOSITO",
            "LOTE",
            "VENCIMIENTO",
            "STOCK"
        FROM stock
        WHERE
            TRIM("CODIGO") = %s
            AND TRIM("ARTICULO") = %s
    """, (_norm_str(codigo), _norm_str(articulo)))

    filas = cur.fetchall()
    cur.close()
    conn.close()

    out = []
    for r in filas:
        out.append({
            "FAMILIA": _norm_str(r.get("FAMILIA")),
            "CODIGO": _norm_str(r.get("CODIGO")),
            "ARTICULO": _norm_str(r.get("ARTICULO")),
            "DEPOSITO": _norm_str(r.get("DEPOSITO")),
            "LOTE": _norm_str(r.get("LOTE")),
            "VENCIMIENTO": _norm_str(r.get("VENCIMIENTO")),
            "STOCK_TXT": _norm_str(r.get("STOCK")),
            "STOCK_NUM": _to_float(r.get("STOCK")),
        })

    out.sort(key=lambda x: (_parse_fecha_for_sort(x.get("VENCIMIENTO")), x.get("LOTE", "")))
    return out


# =========================
# HISTORIAL (INSERT + SELECT)
# =========================
def registrar_historial(
    usuario,
    codigo_interno,
    articulo,
    cantidad,
    tipo_registro,  # "BAJA" o "MOVIMIENTO"
    deposito=None,
    lote=None,
    vencimiento=None,
    deposito_origen=None,
    deposito_destino=None,
    motivo=None,
    stock_antes_lote=None,
    stock_despues_lote=None,
    stock_total_articulo=None,
    stock_total_deposito=None,
    stock_casa_central=None
):
    conn = get_connection()
    cur = conn.cursor()

    ahora = datetime.now()
    motivo = _norm_str(motivo)  # puede ser ""

    cur.execute("""
        INSERT INTO historial_bajas (
            usuario, fecha, hora, codigo_interno, articulo, cantidad, motivo,
            deposito, lote, vencimiento,
            stock_antes_lote, stock_despues_lote,
            stock_total_articulo, stock_total_deposito, stock_casa_central,
            tipo_registro, deposito_origen, deposito_destino
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s)
    """, (
        usuario, ahora.date(), ahora.time(), str(codigo_interno), str(articulo), float(cantidad), motivo,
        deposito, lote, vencimiento,
        stock_antes_lote, stock_despues_lote,
        stock_total_articulo, stock_total_deposito, stock_casa_central,
        _norm_str(tipo_registro), deposito_origen, deposito_destino
    ))

    conn.commit()
    cur.close()
    conn.close()


def obtener_historial(limite=50):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM historial_bajas
        ORDER BY created_at DESC
        LIMIT %s
    """, (limite,))

    resultados = cur.fetchall()
    cur.close()
    conn.close()
    return resultados


# =========================
# ACCIONES SOBRE STOCK
# =========================
def aplicar_baja_en_lote(
    usuario: str,
    codigo: str,
    articulo: str,
    deposito: str,
    lote: str,
    vencimiento: str,
    cantidad: float
):
    codigo = _norm_str(codigo)
    articulo = _norm_str(articulo)
    deposito = _norm_str(deposito)
    lote = _norm_str(lote)
    vencimiento = _norm_str(vencimiento)

    conn = get_connection()
    try:
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT "STOCK"
            FROM stock
            WHERE
                TRIM("CODIGO") = %s
                AND TRIM("ARTICULO") = %s
                AND TRIM("DEPOSITO") = %s
                AND COALESCE(TRIM("LOTE"), '') = %s
                AND COALESCE(TRIM("VENCIMIENTO"), '') = %s
            FOR UPDATE
        """, (codigo, articulo, deposito, lote, vencimiento))

        row = cur.fetchone()
        if not row:
            raise ValueError("No se encontró el lote seleccionado en la tabla stock.")

        stock_antes = _to_float(row.get("STOCK"))
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        if cantidad > stock_antes + 1e-9:
            raise ValueError(f"No hay stock suficiente en ese lote. Stock lote: {stock_antes}")

        stock_despues = stock_antes - float(cantidad)

        cur.execute("""
            UPDATE stock
            SET "STOCK" = %s
            WHERE
                TRIM("CODIGO") = %s
                AND TRIM("ARTICULO") = %s
                AND TRIM("DEPOSITO") = %s
                AND COALESCE(TRIM("LOTE"), '') = %s
                AND COALESCE(TRIM("VENCIMIENTO"), '') = %s
        """, (_fmt_num(stock_despues), codigo, articulo, deposito, lote, vencimiento))

        cur.execute("""
            SELECT "DEPOSITO", "STOCK"
            FROM stock
            WHERE TRIM("CODIGO") = %s AND TRIM("ARTICULO") = %s
        """, (codigo, articulo))
        rows_all = cur.fetchall()

        filas_norm = []
        for r in rows_all:
            filas_norm.append({
                "DEPOSITO": _norm_str(r.get("DEPOSITO")),
                "STOCK_NUM": _to_float(r.get("STOCK"))
            })

        total_articulo = sum(r["STOCK_NUM"] for r in filas_norm)
        total_deposito = sum(r["STOCK_NUM"] for r in filas_norm if r["DEPOSITO"] == deposito)
        total_casa_central = sum(r["STOCK_NUM"] for r in filas_norm if "casa central" in r["DEPOSITO"].lower())

        registrar_historial(
            usuario=usuario,
            codigo_interno=codigo,
            articulo=articulo,
            cantidad=float(cantidad),
            tipo_registro="BAJA",
            deposito=deposito,
            lote=lote,
            vencimiento=vencimiento,
            deposito_origen=deposito,
            deposito_destino=None,
            motivo="",
            stock_antes_lote=float(stock_antes),
            stock_despues_lote=float(stock_despues),
            stock_total_articulo=float(total_articulo),
            stock_total_deposito=float(total_deposito),
            stock_casa_central=float(total_casa_central)
        )

        conn.commit()
        return {
            "stock_antes_lote": stock_antes,
            "stock_despues_lote": stock_despues,
            "total_articulo": total_articulo,
            "total_deposito": total_deposito,
            "total_casa_central": total_casa_central
        }

    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def aplicar_movimiento_en_lote(
    usuario: str,
    codigo: str,
    articulo: str,
    familia: str,
    deposito_origen: str,
    deposito_destino: str,
    lote: str,
    vencimiento: str,
    cantidad: float
):
    codigo = _norm_str(codigo)
    articulo = _norm_str(articulo)
    familia = _norm_str(familia)
    deposito_origen = _norm_str(deposito_origen)
    deposito_destino = _norm_str(deposito_destino)
    lote = _norm_str(lote)
    vencimiento = _norm_str(vencimiento)

    if not deposito_origen:
        raise ValueError("No elegiste depósito ORIGEN.")
    if not deposito_destino or deposito_destino == "—":
        raise ValueError("No elegiste depósito DESTINO.")
    if deposito_destino.lower() == deposito_origen.lower():
        raise ValueError("El depósito destino no puede ser igual al origen.")
    if not lote:
        raise ValueError("No elegiste lote.")
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a 0.")

    conn = get_connection()
    try:
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Lock origen
        cur.execute("""
            SELECT "STOCK"
            FROM stock
            WHERE
                TRIM("CODIGO") = %s
                AND TRIM("ARTICULO") = %s
                AND TRIM("DEPOSITO") = %s
                AND COALESCE(TRIM("LOTE"), '') = %s
                AND COALESCE(TRIM("VENCIMIENTO"), '') = %s
            FOR UPDATE
        """, (codigo, articulo, deposito_origen, lote, vencimiento))

        row_o = cur.fetchone()
        if not row_o:
            raise ValueError("No se encontró el lote seleccionado en el depósito ORIGEN.")

        stock_antes_origen = _to_float(row_o.get("STOCK"))
        if cantidad > stock_antes_origen + 1e-9:
            raise ValueError(f"No hay stock suficiente en el ORIGEN. Stock lote: {stock_antes_origen}")

        stock_despues_origen = stock_antes_origen - float(cantidad)

        cur.execute("""
            UPDATE stock
            SET "STOCK" = %s
            WHERE
                TRIM("CODIGO") = %s
                AND TRIM("ARTICULO") = %s
                AND TRIM("DEPOSITO") = %s
                AND COALESCE(TRIM("LOTE"), '') = %s
                AND COALESCE(TRIM("VENCIMIENTO"), '') = %s
        """, (_fmt_num(stock_despues_origen), codigo, articulo, deposito_origen, lote, vencimiento))

        # Lock destino / upsert
        cur.execute("""
            SELECT "STOCK"
            FROM stock
            WHERE
                TRIM("CODIGO") = %s
                AND TRIM("ARTICULO") = %s
                AND TRIM("DEPOSITO") = %s
                AND COALESCE(TRIM("LOTE"), '') = %s
                AND COALESCE(TRIM("VENCIMIENTO"), '') = %s
            FOR UPDATE
        """, (codigo, articulo, deposito_destino, lote, vencimiento))

        row_d = cur.fetchone()
        if row_d:
            stock_destino_antes = _to_float(row_d.get("STOCK"))
            stock_destino_despues = stock_destino_antes + float(cantidad)

            cur.execute("""
                UPDATE stock
                SET "STOCK" = %s
                WHERE
                    TRIM("CODIGO") = %s
                    AND TRIM("ARTICULO") = %s
                    AND TRIM("DEPOSITO") = %s
                    AND COALESCE(TRIM("LOTE"), '') = %s
                    AND COALESCE(TRIM("VENCIMIENTO"), '') = %s
            """, (_fmt_num(stock_destino_despues), codigo, articulo, deposito_destino, lote, vencimiento))
        else:
            cur.execute("""
                INSERT INTO stock ("FAMILIA","CODIGO","ARTICULO","DEPOSITO","LOTE","VENCIMIENTO","STOCK")
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (familia, codigo, articulo, deposito_destino, lote, vencimiento, _fmt_num(float(cantidad))))

        # Totales
        cur.execute("""
            SELECT "DEPOSITO", "STOCK"
            FROM stock
            WHERE TRIM("CODIGO") = %s AND TRIM("ARTICULO") = %s
        """, (codigo, articulo))
        rows_all = cur.fetchall()

        filas_norm = []
        for r in rows_all:
            filas_norm.append({
                "DEPOSITO": _norm_str(r.get("DEPOSITO")),
                "STOCK_NUM": _to_float(r.get("STOCK"))
            })

        total_articulo = sum(r["STOCK_NUM"] for r in filas_norm)
        total_origen = sum(r["STOCK_NUM"] for r in filas_norm if r["DEPOSITO"] == deposito_origen)
        total_casa_central = sum(r["STOCK_NUM"] for r in filas_norm if "casa central" in r["DEPOSITO"].lower())

        registrar_historial(
            usuario=usuario,
            codigo_interno=codigo,
            articulo=articulo,
            cantidad=float(cantidad),
            tipo_registro="MOVIMIENTO",
            deposito=deposito_origen,
            lote=lote,
            vencimiento=vencimiento,
            deposito_origen=deposito_origen,
            deposito_destino=deposito_destino,
            motivo="",
            stock_antes_lote=float(stock_antes_origen),
            stock_despues_lote=float(stock_despues_origen),
            stock_total_articulo=float(total_articulo),
            stock_total_deposito=float(total_origen),
            stock_casa_central=float(total_casa_central)
        )

        conn.commit()
        return {
            "stock_origen_antes": stock_antes_origen,
            "stock_origen_despues": stock_despues_origen,
            "total_articulo": total_articulo,
            "total_origen": total_origen,
            "total_casa_central": total_casa_central
        }

    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


# =========================
# UI STREAMLIT
# =========================
def mostrar_baja_stock():
    try:
        crear_tabla_historial()
    except Exception:
        pass

    st.markdown("## 🧾 Stock: Baja / Movimiento")
    st.markdown("---")

    user = st.session_state.get("user", {})
    usuario_actual = user.get("nombre", user.get("Usuario", "Usuario"))

    accion = st.radio(
        "Acción",
        options=["Baja de stock", "Movimiento"],
        index=0,
        horizontal=True,
        key=K_ACCION
    )

    st.markdown("---")

    # =========================
    # BÚSQUEDA
    # =========================
    col1, col2 = st.columns([3, 1])
    with col1:
        busqueda = st.text_input(
            "🔍 Buscar por CODIGO o ARTICULO",
            placeholder="Ej: 12345  /  ana profile",
            key=K_BUSQ
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_buscar = st.button("Buscar", type="primary", use_container_width=True, key=K_BTN_BUSCAR)

    # =========================
    # RESULTADOS
    # =========================
    if busqueda and btn_buscar:
        with st.spinner("Buscando en stock..."):
            try:
                items = buscar_items_stock(busqueda)

                if items:
                    st.success(f"Se encontraron {len(items)} artículo(s)")

                    for i, it in enumerate(items):
                        codigo = it.get("CODIGO", "N/A")
                        articulo = it.get("ARTICULO", "Sin artículo")
                        familia = it.get("FAMILIA", "")
                        stock_total = float(it.get("STOCK_TOTAL", 0.0) or 0.0)
                        depositos = sorted(list(it.get("DEPOSITOS", set())))

                        with st.container():
                            col_info, col_btn = st.columns([4, 1])

                            with col_info:
                                st.markdown(
                                    f"**{codigo}** - {articulo}  \n"
                                    f"🏷️ Familia: **{familia or '—'}**  \n"
                                    f"📦 Stock total (todas las ubicaciones): **{_fmt_num(stock_total)}**  \n"
                                    f"🏠 Depósitos: {', '.join(depositos) if depositos else '—'}"
                                )

                            with col_btn:
                                if st.button("Seleccionar", key=f"{K_PREFIX}SEL_{i}"):
                                    st.session_state[K_ITEM_SEL] = {
                                        "CODIGO": codigo,
                                        "ARTICULO": articulo,
                                        "FAMILIA": familia
                                    }
                                    st.rerun()

                            st.markdown("---")
                else:
                    st.warning("No se encontraron artículos con ese criterio en la tabla stock.")

            except Exception as e:
                st.error(f"Error al buscar: {str(e)}")

    # =========================
    # FORMULARIO (si hay selección)
    # =========================
    if K_ITEM_SEL in st.session_state:
        it = st.session_state[K_ITEM_SEL]
        codigo = _norm_str(it.get("CODIGO"))
        articulo = _norm_str(it.get("ARTICULO"))
        familia = _norm_str(it.get("FAMILIA"))

        st.markdown("### 📝 Operación")
        st.info(f"Seleccionado: **{codigo} - {articulo}** | Familia: **{familia or '—'}**")

        if st.button("🔄 Cambiar artículo", use_container_width=True, key=K_PREFIX + "CAMBIAR_ART"):
            try:
                del st.session_state[K_ITEM_SEL]
            except Exception:
                pass
            st.rerun()

        try:
            lotes_all = obtener_lotes_item(codigo, articulo)
        except Exception as e:
            st.error(f"No se pudo cargar lotes del artículo: {str(e)}")
            lotes_all = []

        if not lotes_all:
            st.warning("Este artículo no tiene lotes/stock cargado en la tabla stock.")
        else:
            depositos = sorted({x.get("DEPOSITO", "") for x in lotes_all if _norm_str(x.get("DEPOSITO"))})

            # Default Casa Central
            default_dep_cc = 0
            for idx, d in enumerate(depositos):
                if "casa central" in d.lower():
                    default_dep_cc = idx
                    break

            # =========================
            # BAJA
            # =========================
            if accion == "Baja de stock":
                colA, colB = st.columns([2, 1])
                with colA:
                    deposito_sel = st.selectbox(
                        "Depósito",
                        options=depositos,
                        index=default_dep_cc if depositos else 0,
                        key=K_BAJA_DEP
                    )
                with colB:
                    total_articulo = _sum_stock(lotes_all)
                    total_casa_central = _sum_stock(lotes_all, solo_casa_central=True)
                    st.caption(f"📦 Total artículo: **{_fmt_num(total_articulo)}**")
                    st.caption(f"🏛️ Casa Central: **{_fmt_num(total_casa_central)}**")

                lotes_dep = [x for x in lotes_all if _norm_str(x.get("DEPOSITO")) == _norm_str(deposito_sel)]
                lotes_dep = [x for x in lotes_dep if float(x.get("STOCK_NUM", 0.0) or 0.0) > 0]  # SOLO > 0

                if not lotes_dep:
                    st.warning("No hay lotes con stock (>0) en el depósito seleccionado.")
                else:
                    df_lotes = pd.DataFrame([{
                        "LOTE": x.get("LOTE") or "—",
                        "VENCIMIENTO": x.get("VENCIMIENTO") or "—",
                        "STOCK": _fmt_num(float(x.get("STOCK_NUM", 0.0) or 0.0))
                    } for x in lotes_dep])

                    st.markdown("#### Lotes / Vencimientos (orden FIFO/FEFO)")
                    st.dataframe(df_lotes, use_container_width=True, hide_index=True)

                    idx_fifo = 0  # siempre el primero (ya está ordenado y filtrado >0)

                    usar_fifo = st.checkbox(
                        "✅ Bajar siguiendo FIFO/FEFO automático (recomendado)",
                        value=True,
                        key=K_BAJA_FIFO
                    )

                    lote_sel = ""
                    venc_sel = ""
                    stock_lote_sel = 0.0
                    confirm_no_fifo = False

                    if not usar_fifo:
                        opciones = []
                        for j, x in enumerate(lotes_dep):
                            opciones.append(
                                f"{j+1}. Lote: {x.get('LOTE') or '—'} | Venc: {x.get('VENCIMIENTO') or '—'} | Stock: {_fmt_num(float(x.get('STOCK_NUM', 0.0) or 0.0))}"
                            )

                        opcion = st.selectbox(
                            "Elegí el lote a bajar",
                            options=opciones,
                            index=0,
                            key=K_BAJA_LOTE_SEL
                        )
                        idx_sel = int(opcion.split(".")[0]) - 1
                        elegido = lotes_dep[idx_sel]

                        lote_sel = _norm_str(elegido.get("LOTE"))
                        venc_sel = _norm_str(elegido.get("VENCIMIENTO"))
                        stock_lote_sel = float(elegido.get("STOCK_NUM", 0.0) or 0.0)

                        if idx_sel != idx_fifo and len(lotes_dep) > 1:
                            fifo_ref = lotes_dep[idx_fifo]
                            st.warning(
                                "⚠️ Estás eligiendo un lote que NO es el recomendado por FIFO/FEFO.\n\n"
                                f"Antes hay: **Lote {fifo_ref.get('LOTE') or '—'}** | "
                                f"Venc: **{fifo_ref.get('VENCIMIENTO') or '—'}** | "
                                f"Stock: **{_fmt_num(float(fifo_ref.get('STOCK_NUM', 0.0) or 0.0))}**"
                            )
                            confirm_no_fifo = st.checkbox(
                                "Sí, estoy seguro y quiero bajar este lote igualmente",
                                value=False,
                                key=K_BAJA_CONFIRM_NO_FIFO
                            )

                        st.caption(f"Stock lote seleccionado: **{_fmt_num(stock_lote_sel)}**")

                    if (not usar_fifo) and stock_lote_sel > 0:
                        cantidad = st.number_input(
                            "Cantidad a bajar",
                            min_value=0.01,
                            value=1.0,
                            step=1.0,
                            max_value=float(stock_lote_sel),
                            key=K_BAJA_CANT
                        )
                    else:
                        cantidad = st.number_input(
                            "Cantidad a bajar",
                            min_value=0.01,
                            value=1.0,
                            step=1.0,
                            key=K_BAJA_CANT
                        )

                    st.markdown("---")
                    col_guardar, col_cancelar = st.columns(2)

                    with col_guardar:
                        if st.button("✅ Confirmar Baja", type="primary", use_container_width=True, key=K_PREFIX + "CONFIRM_BAJA"):
                            try:
                                if (not usar_fifo) and len(lotes_dep) > 1:
                                    opcion_txt = st.session_state.get(K_BAJA_LOTE_SEL, "")
                                    if opcion_txt:
                                        idx_sel = int(opcion_txt.split(".")[0]) - 1
                                        if idx_sel != idx_fifo and not st.session_state.get(K_BAJA_CONFIRM_NO_FIFO, False):
                                            st.error("Tenés un lote anterior. Marcá la confirmación para continuar.")
                                            st.stop()

                                if usar_fifo:
                                    lt0 = lotes_dep[0]
                                    res = aplicar_baja_en_lote(
                                        usuario=usuario_actual,
                                        codigo=codigo,
                                        articulo=articulo,
                                        deposito=deposito_sel,
                                        lote=_norm_str(lt0.get("LOTE")),
                                        vencimiento=_norm_str(lt0.get("VENCIMIENTO")),
                                        cantidad=float(cantidad)
                                    )
                                else:
                                    res = aplicar_baja_en_lote(
                                        usuario=usuario_actual,
                                        codigo=codigo,
                                        articulo=articulo,
                                        deposito=deposito_sel,
                                        lote=lote_sel,
                                        vencimiento=venc_sel,
                                        cantidad=float(cantidad)
                                    )

                                st.success("✅ Baja registrada.")
                                st.caption(f"Resta total artículo: **{_fmt_num(res.get('total_articulo', 0.0))}**")
                                st.caption(f"Resta en {deposito_sel}: **{_fmt_num(res.get('total_deposito', 0.0))}**")

                                del st.session_state[K_ITEM_SEL]
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error al registrar baja: {str(e)}")

                    with col_cancelar:
                        if st.button("❌ Cancelar", use_container_width=True, key=K_PREFIX + "CANCEL_BAJA"):
                            del st.session_state[K_ITEM_SEL]
                            st.rerun()

            # =========================
            # MOVIMIENTO
            # =========================
            else:
                st.markdown("#### Movimiento (traslado)")

                colA, colB = st.columns(2)
                with colA:
                    deposito_origen = st.selectbox(
                        "Depósito ORIGEN",
                        options=depositos,
                        index=default_dep_cc if depositos else 0,
                        key=K_MOV_DEP_ORIG
                    )

                depositos_destino = [d for d in depositos if d.lower() != _norm_str(deposito_origen).lower()]
                sugerido = _sugerir_deposito_destino_por_familia(familia, depositos_destino)

                with colB:
                    idx_sug = 0
                    if sugerido and depositos_destino:
                        for i, d in enumerate(depositos_destino):
                            if d.lower() == sugerido.lower():
                                idx_sug = i
                                break

                    deposito_destino = st.selectbox(
                        "Depósito DESTINO",
                        options=depositos_destino if depositos_destino else ["—"],
                        index=idx_sug if (depositos_destino) else 0,
                        key=K_MOV_DEP_DEST
                    )

                lotes_origen = [x for x in lotes_all if _norm_str(x.get("DEPOSITO")) == _norm_str(deposito_origen)]
                lotes_origen = [x for x in lotes_origen if float(x.get("STOCK_NUM", 0.0) or 0.0) > 0]  # SOLO > 0

                if not lotes_origen:
                    st.warning("No hay lotes con stock (>0) en el depósito ORIGEN.")
                else:
                    df_lotes = pd.DataFrame([{
                        "LOTE": x.get("LOTE") or "—",
                        "VENCIMIENTO": x.get("VENCIMIENTO") or "—",
                        "STOCK": _fmt_num(float(x.get("STOCK_NUM", 0.0) or 0.0))
                    } for x in lotes_origen])

                    st.markdown("##### Lotes disponibles en ORIGEN (orden FIFO/FEFO)")
                    st.dataframe(df_lotes, use_container_width=True, hide_index=True)

                    opciones = []
                    for j, x in enumerate(lotes_origen):
                        opciones.append(
                            f"{j+1}. Lote: {x.get('LOTE') or '—'} | Venc: {x.get('VENCIMIENTO') or '—'} | Stock: {_fmt_num(float(x.get('STOCK_NUM', 0.0) or 0.0))}"
                        )

                    opcion = st.selectbox(
                        "Elegí el lote del ORIGEN para mover",
                        options=opciones,
                        index=0,
                        key=K_MOV_LOTE_SEL
                    )
                    idx_sel = int(opcion.split(".")[0]) - 1
                    elegido = lotes_origen[idx_sel]

                    lote_sel = _norm_str(elegido.get("LOTE"))
                    venc_sel = _norm_str(elegido.get("VENCIMIENTO"))
                    stock_lote_sel = float(elegido.get("STOCK_NUM", 0.0) or 0.0)

                    # Alerta si elige lote no FIFO
                    if idx_sel != 0 and len(lotes_origen) > 1:
                        fifo_ref = lotes_origen[0]
                        st.warning(
                            "⚠️ Estás eligiendo un lote que NO es el recomendado por FIFO/FEFO.\n\n"
                            f"Antes hay: **Lote {fifo_ref.get('LOTE') or '—'}** | "
                            f"Venc: **{fifo_ref.get('VENCIMIENTO') or '—'}** | "
                            f"Stock: **{_fmt_num(float(fifo_ref.get('STOCK_NUM', 0.0) or 0.0))}**"
                        )
                        confirm_no_fifo = st.checkbox(
                            "Sí, estoy seguro y quiero mover este lote igualmente",
                            value=False,
                            key=K_MOV_CONFIRM_NO_FIFO
                        )
                    else:
                        confirm_no_fifo = True

                    st.caption(f"Stock lote seleccionado: **{_fmt_num(stock_lote_sel)}**")

                    cantidad = st.number_input(
                        "Cantidad a mover",
                        min_value=0.01,
                        value=1.0,
                        step=1.0,
                        max_value=float(stock_lote_sel),
                        key=K_MOV_CANT
                    )

                    st.markdown("---")
                    col_guardar, col_cancelar = st.columns(2)

                    with col_guardar:
                        if st.button("✅ Confirmar Movimiento", type="primary", use_container_width=True, key=K_PREFIX + "CONFIRM_MOV"):
                            try:
                                if not confirm_no_fifo:
                                    st.error("Tenés un lote anterior. Marcá la confirmación para continuar.")
                                    st.stop()

                                res = aplicar_movimiento_en_lote(
                                    usuario=usuario_actual,
                                    codigo=codigo,
                                    articulo=articulo,
                                    familia=familia,
                                    deposito_origen=deposito_origen,
                                    deposito_destino=deposito_destino,
                                    lote=lote_sel,
                                    vencimiento=venc_sel,
                                    cantidad=float(cantidad)
                                )

                                st.success("✅ Movimiento registrado.")
                                st.caption(f"Origen ({deposito_origen}) resto lote: **{_fmt_num(res.get('stock_origen_despues', 0.0))}**")
                                st.caption(f"Total artículo: **{_fmt_num(res.get('total_articulo', 0.0))}**")

                                del st.session_state[K_ITEM_SEL]
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error al registrar movimiento: {str(e)}")

                    with col_cancelar:
                        if st.button("❌ Cancelar", use_container_width=True, key=K_PREFIX + "CANCEL_MOV"):
                            del st.session_state[K_ITEM_SEL]
                            st.rerun()

    # =========================
    # HISTORIAL
    # =========================
    st.markdown("---")
    st.markdown("### 📋 Historial (Bajas y Movimientos)")

    try:
        historial = obtener_historial(50)

        if historial:
            df = pd.DataFrame(historial)

            if "fecha" in df.columns:
                df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime("%d/%m/%Y")
            if "hora" in df.columns:
                df["hora"] = df["hora"].astype(str).str[:8]

            columnas_preferidas = [
                "fecha", "hora", "usuario",
                "tipo_registro",
                "codigo_interno", "articulo",
                "deposito_origen", "deposito_destino",
                "deposito", "lote", "vencimiento",
                "cantidad",
                "stock_total_deposito", "stock_casa_central",
            ]
            columnas_existentes = [c for c in columnas_preferidas if c in df.columns]

            st.dataframe(
                df[columnas_existentes],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay registros todavía")

    except Exception as e:
        st.warning(f"No se pudo cargar el historial: {str(e)}")
