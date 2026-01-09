# =========================
# ORQUESTADOR.PY
# =========================

import streamlit as st

ORQUESTADOR_CARGADO = True
ORQUESTADOR_ERROR = None


def _init_orquestador_state():
    global ORQUESTADOR_CARGADO, ORQUESTADOR_ERROR
    ORQUESTADOR_CARGADO = True
    ORQUESTADOR_ERROR = None
    try:
        st.session_state["ORQUESTADOR_CARGADO"] = True
        st.session_state["ORQUESTADOR_ERROR"] = None
    except Exception as e:
        ORQUESTADOR_ERROR = str(e)


_init_orquestador_state()

import pandas as pd
import re
from typing import Tuple, Optional, Any, List
from datetime import datetime

from ia_interpretador import interpretar_pregunta, obtener_info_tipo, es_tipo_valido

from sql_compras import (
    get_compras_anio,
    get_total_compras_anio,
    get_detalle_compras_proveedor_mes,
    get_total_compras_proveedor_anio,
    get_detalle_compras_articulo_mes,
    get_detalle_compras_articulo_anio,
    get_total_compras_articulo_anio,
    get_compras_por_mes_excel,
    get_ultima_factura_inteligente,
    get_facturas_de_articulo,
    get_detalle_factura_por_numero,
    get_total_factura_por_numero,
    get_top_10_proveedores_chatbot,
)

try:
    from sql_compras import get_detalle_compras_proveedor_anio as _get_detalle_prov_anio
except Exception:
    _get_detalle_prov_anio = None

try:
    from sql_compras import get_detalle_facturas_proveedor_anio as _get_detalle_facturas_prov_anio
except Exception:
    _get_detalle_facturas_prov_anio = None


def get_detalle_compras_proveedor_anio(proveedor_like: str, anio: int, limite: int = 5000) -> pd.DataFrame:
    if _get_detalle_prov_anio is not None:
        try:
            return _get_detalle_prov_anio(proveedor_like, anio, limite)
        except TypeError:
            return _get_detalle_prov_anio(proveedor_like, anio)

    if _get_detalle_facturas_prov_anio is not None:
        try:
            return _get_detalle_facturas_prov_anio([proveedor_like], [anio], moneda=None, limite=limite)
        except TypeError:
            return _get_detalle_facturas_prov_anio([proveedor_like], [anio])

    return pd.DataFrame()


try:
    from sql_compras import get_total_factura_proveedor as get_total_factura_proveedor
except Exception:
    try:
        from sql_compras import get_total_facturas_proveedor as get_total_factura_proveedor
    except Exception:
        def get_total_factura_proveedor(*args, **kwargs) -> pd.DataFrame:
            return pd.DataFrame()


try:
    from sql_queries import get_facturas_proveedor_detalle as get_facturas_proveedor_detalle
except Exception:
    try:
        from sql_compras import get_facturas_proveedor_detalle as get_facturas_proveedor_detalle
    except Exception:
        def get_facturas_proveedor_detalle(*args, **kwargs) -> pd.DataFrame:
            return pd.DataFrame()


try:
    from sql_facturas import (
        get_facturas_proveedor as _sf_get_facturas_proveedor,
        get_total_facturas_proveedor as _sf_get_total_facturas_proveedor,
        get_detalle_factura_por_numero as _sf_get_detalle_factura_por_numero,
        get_total_factura_por_numero as _sf_get_total_factura_por_numero,
        get_ultima_factura_inteligente as _sf_get_ultima_factura_inteligente,
        get_facturas_articulo as _sf_get_facturas_articulo,
    )

    get_facturas_proveedor_detalle = _sf_get_facturas_proveedor
    get_total_factura_proveedor = _sf_get_total_facturas_proveedor
    get_detalle_factura_por_numero = _sf_get_detalle_factura_por_numero
    get_total_factura_por_numero = _sf_get_total_factura_por_numero
    get_ultima_factura_inteligente = _sf_get_ultima_factura_inteligente
    get_facturas_de_articulo = _sf_get_facturas_articulo

    try:
        st.session_state["DBG_FACTURAS_ORIGEN"] = "sql_facturas"
    except Exception:
        pass

except Exception:
    pass


from sql_comparativas import (
    get_comparacion_proveedor_meses,
    get_comparacion_articulo_anios,
    get_comparacion_proveedor_anios_like,
    get_comparacion_proveedor_anios_monedas,
    get_comparacion_familia_anios_monedas,
    get_comparacion_proveedores_meses_multi,
    get_comparacion_proveedores_anios_multi,
    get_gastos_todas_familias_mes,
    get_gastos_todas_familias_anio,
    get_gastos_secciones_detalle_completo,
)

try:
    from sql_comparativas import get_comparacion_articulo_meses
except Exception:
    def get_comparacion_articulo_meses(*args, **kwargs) -> pd.DataFrame:
        return pd.DataFrame()

try:
    from sql_comparativas import get_comparacion_familia_meses_moneda
except Exception:
    def get_comparacion_familia_meses_moneda(*args, **kwargs) -> pd.DataFrame:
        return pd.DataFrame()


from sql_stock import (
    get_stock_total,
    get_stock_articulo,
    get_stock_familia,
    get_stock_por_familia,
    get_stock_por_deposito,
    get_lotes_por_vencer,
    get_lotes_vencidos,
    get_stock_bajo,
    get_stock_lote_especifico,
)

from utils_format import formatear_dataframe
from utils_openai import responder_con_openai


def _normalizar_nro_factura(nro: str) -> str:
    nro = str(nro or "").strip().upper()
    if not nro:
        return ""
    if re.fullmatch(r"\d+", nro):
        return "A" + nro.zfill(8)
    m = re.fullmatch(r"([A-Z])(\d+)", nro)
    if m:
        letra = m.group(1)
        dig = m.group(2)
        if len(dig) < 8:
            dig = dig.zfill(8)
        return letra + dig
    return nro


def _extraer_nro_factura_fallback(texto: str) -> Optional[str]:
    if not texto:
        return None
    t = str(texto).strip()
    if re.fullmatch(r"[A-Za-z]\d{5,}", t):
        return _normalizar_nro_factura(t)
    m = re.search(
        r"\b(?:detalle\s+)?(?:factura|comprobante|nro\.?\s*factura|nro\.?\s*comprobante)\b\s*[:#-]?\s*([A-Za-z]?\d{3,})\b",
        t,
        flags=re.IGNORECASE
    )
    if m:
        return _normalizar_nro_factura(m.group(1))
    return None


def _to_like(p: str) -> str:
    p = str(p or "").strip().lower()
    if not p:
        return ""
    if "%" in p:
        return p
    return f"%{p}%"


def procesar_pregunta_v2(pregunta: str) -> Tuple[str, Optional[pd.DataFrame], Optional[dict]]:
    _init_orquestador_state()

    print(f"\n{'='*60}")
    print(f"📝 PREGUNTA: {pregunta}")
    print(f"{'='*60}")

    interpretacion = interpretar_pregunta(pregunta)

    tipo = interpretacion.get("tipo", "no_entendido")
    params = interpretacion.get("parametros", {})
    debug = interpretacion.get("debug", "")

    # 🔍 DEBUG ORQUESTADOR
    print("\n[ORQUESTADOR] DECISIÓN")
    print(f"  Tipo   : {tipo}")
    print(f"  Params : {params}")
    print(f"  Debug  : {debug}")

    try:
        if st.session_state.get("DEBUG_SQL", False):
            st.session_state["DBG_INT_LAST"] = {
                "pregunta": pregunta,
                "tipo": tipo,
                "parametros": params,
                "debug": debug,
            }
    except Exception:
        pass

    if tipo == "conversacion":
        respuesta = responder_con_openai(pregunta, "conversacion")
        return f"💬 {respuesta}", None, None

    if tipo == "conocimiento":
        respuesta = responder_con_openai(pregunta, "conocimiento")
        return f"📚 {respuesta}", None, None

    if tipo == "no_entendido":
        nro_fb = _extraer_nro_factura_fallback(pregunta)
        if nro_fb:
            return _ejecutar_consulta("detalle_factura_numero", {"nro_factura": nro_fb}, pregunta)

    if tipo == "no_entendido":
        sugerencia = interpretacion.get("sugerencia", "No entendí tu pregunta.")
        alternativas = interpretacion.get("alternativas", [])
        return (
            f"🤔 {sugerencia}",
            None,
            {
                "sugerencia": sugerencia,
                "alternativas": alternativas,
                "pregunta_original": pregunta
            }
        )

    return _ejecutar_consulta(tipo, params, pregunta)


def _ejecutar_consulta(tipo: str, params: dict, pregunta_original: str) -> Tuple[str, Optional[pd.DataFrame], None]:
    try:
        # COMPRAS AÑO / MES / ETC (igual que antes) ...

        # (dejo todo lo que ya tenías sin modificar excepto el bloque facturas_proveedor)

        # =========================================================
        # FACTURAS (LISTADO)
        # =========================================================
        if tipo in ("facturas_proveedor", "facturas_proveedor_detalle"):
            proveedores = params.get("proveedores", [])
            if isinstance(proveedores, str):
                proveedores = [proveedores]

            proveedores_raw = [str(p).strip() for p in proveedores if str(p).strip()]
            if not proveedores_raw:
                return "❌ Indicá el proveedor. Ej: todas las facturas roche 2025", None, None

            st.session_state["DBG_SQL_LAST_TAG"] = "sql_facturas - facturas_proveedor"

            # 🔍 DEBUG ANTES DE LLAMAR SQL
            print("\n[ORQUESTADOR] Llamando get_facturas_proveedor_detalle() con:")
            print(f"  proveedores = {proveedores_raw}")
            print(f"  meses       = {params.get('meses')}")
            print(f"  anios       = {params.get('anios')}")
            print(f"  desde       = {params.get('desde')}")
            print(f"  hasta       = {params.get('hasta')}")
            print(f"  articulo    = {params.get('articulo')}")
            print(f"  moneda      = {params.get('moneda')}")
            print(f"  limite      = {params.get('limite', 5000)}")

            df = get_facturas_proveedor_detalle(
                proveedores=proveedores_raw,
                meses=params.get("meses"),
                anios=params.get("anios"),
                desde=params.get("desde"),
                hasta=params.get("hasta"),
                articulo=params.get("articulo"),
                moneda=params.get("moneda"),
                limite=params.get("limite", 5000),
            )

            if df is None or df.empty:
                tiempo_lbl = ""
                if params.get("meses"):
                    tiempo_lbl = f" en {', '.join(params.get('meses'))}"
                elif params.get("anios"):
                    tiempo_lbl = f" en {', '.join(map(str, params.get('anios')))}"
                debug_msg = f"⚠️ No se encontraron resultados para '{pregunta_original}'.\n\n"
                debug_msg += f"**Tipo detectado:** {tipo}\n"
                debug_msg += f"**Parámetros extraídos:**\n"
                for k, v in params.items():
                    debug_msg += f"- {k}: {v}\n"
                debug_msg += "\nRevisá la consola del servidor para ver el SQL impreso (🛠 SQL generado (facturas_proveedor_detalle))."
                return debug_msg, None, None

            prov_lbl = ", ".join([p.upper() for p in proveedores_raw[:3]])
            return f"🧾 Facturas de **{prov_lbl}** ({len(df)} registros):", formatear_dataframe(df), None

        # ... el resto de tipos (comparaciones, stock, etc.) igual que tu archivo original ...

        return f"❌ Tipo de consulta '{tipo}' no implementado.", None, None

    except Exception as e:
        print(f"❌ Error ejecutando consulta: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Error: {str(e)[:150]}", None, None


def procesar_pregunta(pregunta: str) -> Tuple[str, Optional[pd.DataFrame]]:
    mensaje, df, sugerencia = procesar_pregunta_v2(pregunta)

    if sugerencia:
        alternativas = sugerencia.get("alternativas", [])
        if alternativas:
            mensaje += "\n\n**Alternativas:**\n" + "\n".join(f"• {a}" for a in alternativas[:3])

    return mensaje, df


def procesar_pregunta_router(pregunta: str) -> Tuple[str, Optional[pd.DataFrame]]:
    return procesar_pregunta(pregunta)


if __name__ == "__main__":
    print("=" * 60)
    print("🛠 Verificando estado del orquestador...")
    try:
        print(f"ORQUESTADOR_CARGADO (session): {st.session_state.get('ORQUESTADOR_CARGADO', None)}")
    except Exception:
        print("ORQUESTADOR_CARGADO (session): n/a")
    print("=" * 60)
