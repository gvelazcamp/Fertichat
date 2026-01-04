# =========================
# UI_COMPRAS.PY - INTERFAZ COMPRAS IA
# =========================

import streamlit as st
import pandas as pd
from datetime import datetime# =========================
# UI_COMPRAS.PY - VERSIÓN CON INTERPRETADOR IA
# =========================

import streamlit as st
import pandas as pd
from datetime import datetime

# IMPORTS DEL NUEVO SISTEMA
from interpretador_ia import interpretar_pregunta, obtener_info_tipo
from utils_openai import responder_con_openai

# IMPORTS DE SQL
from sql_queries import (
    get_compras_anio,
    get_detalle_compras_proveedor_mes,
    get_detalle_compras_proveedor_anio,
    get_detalle_compras_articulo_mes,
    get_detalle_compras_articulo_anio,
    get_compras_por_mes_excel,
    get_ultima_factura_inteligente,
    get_facturas_de_articulo,
    get_detalle_factura_por_numero,
    get_comparacion_proveedor_meses,
    get_comparacion_proveedor_anios_monedas,
    get_comparacion_articulo_meses,
    get_comparacion_articulo_anios,
    get_comparacion_familia_meses_moneda,
    get_comparacion_familia_anios_monedas,
    get_gastos_todas_familias_mes,
    get_gastos_todas_familias_anio,
    get_gastos_secciones_detalle_completo,
    get_top_10_proveedores_chatbot,
    get_stock_total,
    get_stock_articulo,
    get_stock_familia,
    get_stock_por_familia,
    get_stock_por_deposito,
    get_lotes_por_vencer,
    get_lotes_vencidos,
    get_stock_bajo,
    get_stock_lote_especifico,
    get_total_compras_anio,
    get_total_compras_proveedor_anio,
    get_total_compras_articulo_anio
)


# =========================
# FUNCIÓN ROUTER PARA EJECUTAR SQL
# =========================

def ejecutar_consulta_por_tipo(tipo: str, parametros: dict):
    """
    Router que ejecuta la función SQL correcta según el tipo
    """
    
    # COMPRAS
    if tipo == "compras_anio":
        return get_compras_anio(parametros["anio"])
    
    elif tipo == "compras_proveedor_mes":
        return get_detalle_compras_proveedor_mes(
            parametros["proveedor"], 
            parametros["mes"]
        )
    
    elif tipo == "compras_proveedor_anio":
        return get_detalle_compras_proveedor_anio(
            parametros["proveedor"],
            parametros["anio"]
        )
    
    elif tipo == "compras_articulo_mes":
        return get_detalle_compras_articulo_mes(
            parametros["articulo"],
            parametros["mes"]
        )
    
    elif tipo == "compras_articulo_anio":
        return get_detalle_compras_articulo_anio(
            parametros["articulo"],
            parametros["anio"]
        )
    
    elif tipo == "compras_mes":
        return get_compras_por_mes_excel(parametros["mes"])
    
    # FACTURAS
    elif tipo == "ultima_factura":
        return get_ultima_factura_inteligente(parametros["patron"])
    
    elif tipo == "facturas_articulo":
        return get_facturas_de_articulo(parametros["articulo"])
    
    elif tipo == "detalle_factura":
        return get_detalle_factura_por_numero(parametros["nro_factura"])
    
    # COMPARACIONES
    elif tipo == "comparar_proveedor_meses":
        return get_comparacion_proveedor_meses(
            parametros["mes1"],
            parametros["mes2"],
            parametros["proveedor"]
        )
    
    elif tipo == "comparar_proveedor_anios":
        return get_comparacion_proveedor_anios_monedas(
            parametros["anios"],
            parametros["proveedor"]
        )
    
    elif tipo == "comparar_articulo_meses":
        return get_comparacion_articulo_meses(
            parametros["mes1"],
            parametros["mes2"],
            parametros["articulo"]
        )
    
    elif tipo == "comparar_articulo_anios":
        return get_comparacion_articulo_anios(
            parametros["anios"],
            parametros["articulo"]
        )
    
    elif tipo == "comparar_familia_meses":
        moneda = parametros.get("moneda", "pesos")
        return get_comparacion_familia_meses_moneda(
            parametros["mes1"],
            parametros["mes2"],
            moneda
        )
    
    elif tipo == "comparar_familia_anios":
        return get_comparacion_familia_anios_monedas(parametros["anios"])
    
    # GASTOS
    elif tipo == "gastos_familias_mes":
        return get_gastos_todas_familias_mes(parametros["mes"])
    
    elif tipo == "gastos_familias_anio":
        return get_gastos_todas_familias_anio(parametros["anio"])
    
    elif tipo == "gastos_secciones":
        return get_gastos_secciones_detalle_completo(
            parametros["familias"],
            parametros["mes"]
        )
    
    # TOP
    elif tipo == "top_proveedores":
        moneda = parametros.get("moneda", "pesos")
        anio = parametros.get("anio")
        mes = parametros.get("mes")
        return get_top_10_proveedores_chatbot(moneda, anio, mes)
    
    # STOCK
    elif tipo == "stock_total":
        return get_stock_total()
    
    elif tipo == "stock_articulo":
        return get_stock_articulo(parametros["articulo"])
    
    elif tipo == "stock_familia":
        return get_stock_familia(parametros["familia"])
    
    elif tipo == "stock_por_familia":
        return get_stock_por_familia()
    
    elif tipo == "stock_por_deposito":
        return get_stock_por_deposito()
    
    elif tipo == "stock_lotes_vencer":
        dias = parametros.get("dias", 90)
        return get_lotes_por_vencer(dias)
    
    elif tipo == "stock_lotes_vencidos":
        return get_lotes_vencidos()
    
    elif tipo == "stock_bajo":
        minimo = parametros.get("minimo", 10)
        return get_stock_bajo(minimo)
    
    elif tipo == "stock_lote":
        return get_stock_lote_especifico(parametros["lote"])
    
    else:
        raise ValueError(f"❌ Tipo '{tipo}' no tiene función implementada")


# =========================
# FUNCIÓN PARA OBTENER RESUMEN (SI EXISTE)
# =========================

def obtener_resumen_si_existe(tipo: str, parametros: dict):
    """
    Algunas consultas tienen una versión 'resumen' además del detalle.
    Esta función intenta obtenerla si existe.
    """
    info_tipo = obtener_info_tipo(tipo)
    if not info_tipo:
        return None
    
    funcion_resumen = info_tipo.get("resumen")
    if not funcion_resumen:
        return None
    
    try:
        if funcion_resumen == "get_total_compras_anio":
            return get_total_compras_anio(parametros["anio"])
        
        elif funcion_resumen == "get_total_compras_proveedor_anio":
            return get_total_compras_proveedor_anio(
                parametros["proveedor"],
                parametros["anio"]
            )
        
        elif funcion_resumen == "get_total_compras_articulo_anio":
            return get_total_compras_articulo_anio(
                parametros["articulo"],
                parametros["anio"]
            )
        
        return None
    except:
        return None


# =========================
# UI PRINCIPAL - COMPRAS IA
# =========================

def Compras_IA():
    """
    Interfaz principal del chatbot de compras con IA
    """
    
    st.markdown("### 🤖 Asistente de Compras IA")
    st.markdown("Preguntá en lenguaje natural sobre compras, gastos, proveedores y más.")
    
    # Ejemplos
    with st.expander("💡 Ver ejemplos de preguntas"):
        st.markdown("""
        **Compras:**
        - "compras roche noviembre 2025"
        - "cuánto le compramos a biodiagnóstico este mes"
        - "compras 2025"
        - "detalle compras wiener 2024"
        
        **Comparaciones:**
        - "comparar roche octubre noviembre 2025"
        - "comparar gastos familias 2024 2025"
        - "comparar vitek 2023 2024"
        
        **Facturas:**
        - "última factura vitek"
        - "cuando vino vitek"
        - "detalle factura 275217"
        
        **Stock:**
        - "stock vitek"
        - "lotes por vencer"
        - "stock total"
        - "stock bajo"
        
        **Gastos:**
        - "gastos familias enero 2026"
        - "top proveedores 2025"
        - "gastos secciones G FB enero 2026"
        
        **Conversación:**
        - "hola"
        - "gracias"
        - "qué puedes hacer"
        """)
    
    # Debug mode toggle (solo para desarrollo)
    if st.checkbox("🔍 Modo debug", value=False, key="debug_mode_compras"):
        st.session_state["debug_mode"] = True
    else:
        st.session_state["debug_mode"] = False
    
    st.markdown("---")
    
    # Input del usuario
    pregunta = st.chat_input("Escribí tu consulta aquí...")
    
    if pregunta:
        # Mostrar mensaje del usuario
        with st.chat_message("user"):
            st.write(pregunta)
        
        # Interpretar con IA
        with st.spinner("🤔 Analizando tu pregunta..."):
            resultado = interpretar_pregunta(pregunta)
        
        tipo = resultado.get("tipo", "")
        parametros = resultado.get("parametros", {})
        debug = resultado.get("debug", "")
        
        # Mostrar debug si está activado
        if st.session_state.get("debug_mode", False):
            with st.expander("🔍 Información de debug"):
                st.json({
                    "tipo": tipo,
                    "parametros": parametros,
                    "debug": debug,
                    "resultado_completo": resultado
                })
        
        # Procesar según el tipo
        with st.chat_message("assistant"):
            
            # CASO 1: CONVERSACIÓN
            if tipo == "conversacion":
                with st.spinner("💬 Generando respuesta..."):
                    respuesta = responder_con_openai(pregunta, tipo="conversacion")
                st.write(respuesta)
            
            # CASO 2: CONOCIMIENTO GENERAL
            elif tipo == "conocimiento":
                with st.spinner("🧠 Buscando información..."):
                    respuesta = responder_con_openai(pregunta, tipo="conocimiento")
                st.write(respuesta)
            
            # CASO 3: NO ENTENDIDO
            elif tipo == "no_entendido":
                st.warning("🤔 No entendí bien tu pregunta.")
                
                if resultado.get("sugerencia"):
                    st.write(f"**¿Quisiste decir:** {resultado['sugerencia']}")
                
                if resultado.get("alternativas"):
                    st.write("**O probá con:**")
                    for alt in resultado["alternativas"]:
                        st.write(f"- `{alt}`")
            
            # CASO 4: CONSULTA DE DATOS
            else:
                # Verificar que el tipo tenga mapeo
                info_tipo = obtener_info_tipo(tipo)
                
                if not info_tipo:
                    st.error(f"❌ El tipo '{tipo}' no tiene una función SQL asociada")
                    st.info("Esto es un error de configuración. Por favor reportalo al desarrollador.")
                    return
                
                # Ejecutar la consulta
                try:
                    with st.spinner("📊 Consultando base de datos..."):
                        resultado_sql = ejecutar_consulta_por_tipo(tipo, parametros)
                    
                    # Obtener resumen si existe
                    resumen = obtener_resumen_si_existe(tipo, parametros)
                    
                    # MOSTRAR RESULTADOS
                    
                    # Si hay resumen, mostrarlo primero
                    if resumen and isinstance(resumen, dict):
                        st.success("📈 Resumen:")
                        cols = st.columns(len(resumen))
                        for idx, (key, value) in enumerate(resumen.items()):
                            with cols[idx]:
                                st.metric(label=key, value=value)
                        st.markdown("---")
                    
                    # Mostrar detalle
                    if isinstance(resultado_sql, pd.DataFrame):
                        if len(resultado_sql) == 0:
                            st.warning("⚠️ No se encontraron resultados para esta consulta.")
                        else:
                            st.success(f"✅ Encontré **{len(resultado_sql)}** resultados")
                            
                            # Mostrar tabla
                            st.dataframe(
                                resultado_sql, 
                                use_container_width=True,
                                height=400
                            )
                            
                            # Botón de descarga
                            csv = resultado_sql.to_csv(index=False, encoding='utf-8-sig')
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            st.download_button(
                                label="📥 Descargar CSV",
                                data=csv,
                                file_name=f"consulta_{tipo}_{timestamp}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    
                    elif isinstance(resultado_sql, dict):
                        # Es un diccionario (resumen/métricas)
                        st.success("✅ Resultado:")
                        cols = st.columns(len(resultado_sql))
                        for idx, (key, value) in enumerate(resultado_sql.items()):
                            with cols[idx]:
                                st.metric(label=key, value=value)
                    
                    elif isinstance(resultado_sql, str):
                        # Es un mensaje de texto
                        st.info(resultado_sql)
                    
                    else:
                        # Otro tipo de resultado
                        st.write(resultado_sql)
                
                except Exception as e:
                    st.error(f"❌ Error ejecutando consulta: {str(e)}")
                    
                    if st.session_state.get("debug_mode", False):
                        st.exception(e)
                    else:
                        st.info("💡 Activá el modo debug para ver más detalles del error")


# =========================
# HISTORIAL DE CHAT (OPCIONAL)
# =========================

def inicializar_historial():
    """Inicializa el historial del chat si no existe"""
    if "historial_compras" not in st.session_state:
        st.session_state["historial_compras"] = []

def agregar_al_historial(pregunta: str, respuesta: str):
    """Agrega una interacción al historial"""
    if "historial_compras" not in st.session_state:
        inicializar_historial()
    
    st.session_state["historial_compras"].append({
        "timestamp": datetime.now(),
        "pregunta": pregunta,
        "respuesta": respuesta
    })

def mostrar_historial():
    """Muestra el historial de consultas"""
    if "historial_compras" in st.session_state and st.session_state["historial_compras"]:
        with st.expander("📜 Ver historial de consultas"):
            for item in reversed(st.session_state["historial_compras"][-10:]):
                st.markdown(f"**{item['timestamp'].strftime('%H:%M:%S')}** - {item['pregunta']}")
                st.text(f"→ {item['respuesta'][:100]}...")
                st.markdown("---")
from typing import Optional

from utils_format import formatear_dataframe, df_to_excel
from utils_graphs import _render_graficos_compras, _render_explicacion_compras

# Importar del orquestador
from orquestador import (
    procesar_pregunta,
    procesar_pregunta_router,
)

# Importar de utils_openai
from utils_openai import (
    obtener_sugerencia_ejecutable,
    recomendar_como_preguntar,
)

# Importar de intent_detector
from intent_detector import normalizar_texto


def render_orquestador_output(pregunta_original: str, respuesta: str, df: Optional[pd.DataFrame]):
    """
    Intercepta marcadores especiales del orquestador y los renderiza en la UI.
    """
    # UID para keys (evita choques de botones en reruns)
    uid = str(abs(hash((pregunta_original or "", respuesta or ""))) % 10**8)

    # -------------------------------------------------
    # 1) SUGERENCIA IA (cuando intent_detector no entiende)
    # -------------------------------------------------
    if respuesta == "__MOSTRAR_SUGERENCIA__":
        st.warning("No entendí esa pregunta tal cual. Te propongo una forma ejecutable 👇")

        with st.spinner("🧠 Generando sugerencia..."):
            sug = obtener_sugerencia_ejecutable(pregunta_original)

        entendido = (sug.get("entendido") or "").strip()
        comando = (sug.get("sugerencia") or "").strip()
        alternativas = sug.get("alternativas") or []

        if entendido:
            st.caption(entendido)

        if comando:
            st.markdown(f"✅ **Sugerencia ejecutable:** `{comando}`")

            if st.button(f"▶️ Ejecutar: {comando}", key=f"btn_exec_{uid}", use_container_width=True):
                with st.spinner("🔎 Ejecutando..."):
                    resp2, df2 = procesar_pregunta(comando)

                # Render normal
                st.markdown(f"**{resp2}**")
                if df2 is not None and not df2.empty:
                    st.dataframe(formatear_dataframe(df2), use_container_width=True, hide_index=True)
        else:
            st.info("No pude generar un comando ejecutable. Probá reformular.")
            st.markdown(recomendar_como_preguntar(pregunta_original))

        if alternativas:
            st.markdown("**Alternativas:**")
            for i, alt in enumerate(alternativas[:5]):
                alt = str(alt).strip()
                if not alt:
                    continue
                if st.button(f"➡️ {alt}", key=f"btn_alt_{uid}_{i}", use_container_width=True):
                    with st.spinner("🔎 Ejecutando alternativa..."):
                        resp3, df3 = procesar_pregunta(alt)

                    st.markdown(f"**{resp3}**")
                    if df3 is not None and not df3.empty:
                        st.dataframe(formatear_dataframe(df3), use_container_width=True, hide_index=True)

        return  # 👈 importante

    # -------------------------------------------------
    # 2) COMPARACIÓN (tabs proveedor/años)
    # -------------------------------------------------
    if respuesta == "__COMPARACION_TABS__":
        info = st.session_state.get("comparacion_tabs", {}) or {}
        st.markdown(f"**{info.get('titulo','📊 Comparación')}**")

        tabs = st.tabs(["📌 Resumen", "📋 Detalle"])
        with tabs[0]:
            df_res = info.get("resumen")
            if df_res is not None and not df_res.empty:
                st.dataframe(df_res, use_container_width=True, hide_index=True)
            else:
                st.info("Sin resumen.")

        with tabs[1]:
            df_det = info.get("detalle")
            if df_det is not None and not df_det.empty:
                st.dataframe(df_det, use_container_width=True, hide_index=True)
            else:
                st.info("Sin detalle.")

        return

    # -------------------------------------------------
    # 3) COMPARACIÓN FAMILIAS (tabs pesos/usd)
    # -------------------------------------------------
    if respuesta == "__COMPARACION_FAMILIA_TABS__":
        info = st.session_state.get("comparacion_familia_tabs", {}) or {}
        st.markdown(f"**{info.get('titulo','📊 Comparación de familias')}**")

        tabs = st.tabs(["$ Pesos", "U$S USD"])
        with tabs[0]:
            dfp = info.get("df_pesos")
            if dfp is not None and not dfp.empty:
                st.dataframe(formatear_dataframe(dfp), use_container_width=True, hide_index=True)
            else:
                st.info("Sin datos en pesos.")

        with tabs[1]:
            duf = info.get("df_usd")
            if duf is not None and not duf.empty:
                st.dataframe(formatear_dataframe(duf), use_container_width=True, hide_index=True)
            else:
                st.info("Sin datos en USD.")

        return

    # -------------------------------------------------
    # 4) RESPUESTA NORMAL
    # -------------------------------------------------
    st.markdown(f"**{respuesta}**")
    if df is not None and not df.empty:
        st.dataframe(formatear_dataframe(df), use_container_width=True, hide_index=True)


def mostrar_detalle_df(
    df,
    titulo="Detalle",
    key="detalle",
    contexto_respuesta=None,
    max_rows=None,  # ✅ Sin límite por defecto
    enable_chart=True,
    enable_explain=True,
):
    """
    ✅ VERSIÓN CON ESTADO PERSISTENTE
    El detalle NO desaparece al hacer refresh/rerun
    """
    # ---------------------------------
    # Validaciones básicas
    # ---------------------------------
    if df is None:
        return

    try:
        if hasattr(df, "empty") and df.empty:
            return
    except Exception:
        pass

    # ✅ GUARDAR EN SESSION STATE (persiste entre reruns)
    estado_key = f"detalle_{key}_estado"
    if estado_key not in st.session_state:
        st.session_state[estado_key] = {
            "df": df.copy(),
            "titulo": titulo,
            "contexto": contexto_respuesta,
            "ver_tabla": True,
            "ver_grafico": False,
            "ver_explicacion": False,
        }
    else:
        # Actualizar solo si cambió el DF
        if not df.equals(st.session_state[estado_key]["df"]):
            st.session_state[estado_key]["df"] = df.copy()
            st.session_state[estado_key]["titulo"] = titulo
            st.session_state[estado_key]["contexto"] = contexto_respuesta

    # Usar datos del estado
    estado = st.session_state[estado_key]
    df_guardado = estado["df"]
    titulo_guardado = estado["titulo"]
    contexto_guardado = estado["contexto"]

    # ---------------------------------
    # DATASET COMPLETO PARA CÁLCULOS
    # ---------------------------------
    df_full = df_guardado.copy()

    # ---------------------------------
    # DATASET RECORTADO PARA TABLA
    # ---------------------------------
    if max_rows is not None:
        try:
            df_view = df_full.head(int(max_rows)).copy()
        except Exception:
            df_view = df_full.copy()
    else:
        df_view = df_full.copy()

    # ---------------------------------
    # HEADER
    # ---------------------------------
    st.markdown(f"### {titulo_guardado}")

    # ---------------------------------
    # CHECKS UI (con estado persistente)
    # ---------------------------------
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        ver_tabla = st.checkbox(
            "📄 Ver tabla (detalle)",
            key=f"{key}_tabla",
            value=estado["ver_tabla"]
        )
        if ver_tabla != estado["ver_tabla"]:
            st.session_state[estado_key]["ver_tabla"] = ver_tabla

    with col2:
        ver_grafico = False
        if enable_chart:
            ver_grafico = st.checkbox(
                "📈 Ver gráfico",
                key=f"{key}_grafico",
                value=estado["ver_grafico"]
            )
            if ver_grafico != estado["ver_grafico"]:
                st.session_state[estado_key]["ver_grafico"] = ver_grafico

    with col3:
        ver_explicacion = False
        if enable_explain:
            ver_explicacion = st.checkbox(
                "🧠 Ver explicación",
                key=f"{key}_explica",
                value=estado["ver_explicacion"]
            )
            if ver_explicacion != estado["ver_explicacion"]:
                st.session_state[estado_key]["ver_explicacion"] = ver_explicacion

    # ---------------------------------
    # TABLA (LIMITADA O COMPLETA)
    # ---------------------------------
    if ver_tabla:
        try:
            st.dataframe(
                df_view,
                use_container_width=True,
                hide_index=True,
                height=400
            )
        except Exception:
            st.dataframe(df_view)

        try:
            total_full = len(df_full)
            total_view = len(df_view)
            if max_rows is not None and total_full > total_view:
                st.caption(
                    f"📊 Mostrando {total_view:,} de {total_full:,} registros. "
                    f"Gráficos y explicación usan el dataset completo."
                )
            else:
                st.caption(f"📊 Mostrando {total_full:,} registros")
        except Exception:
            pass

    # ---------------------------------
    # GRÁFICOS (DATASET COMPLETO)
    # ---------------------------------
    if ver_grafico:
        try:
            _render_graficos_compras(df_full, key_base=key)
        except Exception as e:
            st.warning(f"No se pudo generar el gráfico: {str(e)}")

    # ---------------------------------
    # EXPLICACIÓN (DATASET COMPLETO)
    # ---------------------------------
    if ver_explicacion:
        try:
            _render_explicacion_compras(df_full)
        except Exception as e:
            st.warning(f"No se pudo generar la explicación: {str(e)}")


def Compras_IA():
    """
    ✅ Chat mejorado con estado persistente del detalle
    """
    st.subheader("🛒 Compras IA")
    st.markdown("*Integrado con OpenAI*")

    # Inicializar historial
    if "chat_historial" not in st.session_state:
        st.session_state.chat_historial = []

    # Mostrar historial (últimos 15 mensajes)
    for msg in st.session_state.chat_historial[-15:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input del usuario
    prompt = st.chat_input("Escribí tu consulta… (ej: compras roche noviembre 2025)")

    if prompt:
        # Agregar mensaje del usuario
        st.session_state.chat_historial.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("🔎 Procesando..."):
                resp, df = procesar_pregunta_router(prompt)
                
                # ✅ Guardar respuesta en session_state ANTES de renderizar
                st.session_state["ultima_respuesta"] = resp
                st.session_state["ultimo_df"] = df
                st.session_state["ultima_pregunta"] = prompt
                
                # Render especial (tabs/sugerencias/etc)
                render_orquestador_output(prompt, resp, df)

        # Guardar en historial
        st.session_state.chat_historial.append({"role": "assistant", "content": resp})

    # ✅ MOSTRAR DETALLE PERSISTENTE (si existe)
    if "ultimo_df" in st.session_state and st.session_state["ultimo_df"] is not None:
        if not st.session_state["ultimo_df"].empty:
            mostrar_detalle_df(
                df=st.session_state["ultimo_df"],
                titulo=st.session_state.get("ultima_respuesta", "Detalle"),
                key="compras_detalle_principal",
                max_rows=None,  # Sin límite
                enable_chart=True,
                enable_explain=True
            )
# =========================
# FUNCIÓN COMPRAS_IA() COMPLETA
# =========================

def Compras_IA():
    """
    ✅ Chat mejorado con estado persistente del detalle
    """
    st.subheader("🛒 Compras IA")
    st.markdown("*Integrado con OpenAI*")

    # Inicializar historial
    if "chat_historial" not in st.session_state:
        st.session_state.chat_historial = []

    # Mostrar historial (últimos 15 mensajes)
    for msg in st.session_state.chat_historial[-15:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input del usuario
    prompt = st.chat_input("Escribí tu consulta… (ej: compras roche noviembre 2025)")

    if prompt:
        # Agregar mensaje del usuario
        st.session_state.chat_historial.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("🔎 Procesando..."):
                resp, df = procesar_pregunta_router(prompt)
                
                # ✅ Guardar respuesta en session_state ANTES de renderizar
                st.session_state["ultima_respuesta"] = resp
                st.session_state["ultimo_df"] = df
                st.session_state["ultima_pregunta"] = prompt
                
                # Render especial (tabs/sugerencias/etc)
                render_orquestador_output(prompt, resp, df)

        # Guardar en historial
        st.session_state.chat_historial.append({"role": "assistant", "content": resp})

    # ✅ MOSTRAR DETALLE PERSISTENTE (si existe)
    if "ultimo_df" in st.session_state and st.session_state["ultimo_df"] is not None:
        if not st.session_state["ultimo_df"].empty:
            mostrar_detalle_df(
                df=st.session_state["ultimo_df"],
                titulo=st.session_state.get("ultima_respuesta", "Detalle"),
                key="compras_detalle_principal",
                max_rows=None,  # Sin límite
                enable_chart=True,
                enable_explain=True
            )


# =========================
# CSS PARA AGREGAR EN MAIN.PY
# =========================
# Agregar esto al final del @media (max-width: 768px) en main.py
# JUSTO ANTES del cierre }

"""
  /* ULTRA FIX CHAT INPUT MÓVIL */
  [data-testid="stChatInput"],
  [data-testid="stChatInput"] > div,
  [data-testid="stChatInput"] > div > div {
    background: #f8fafc !important;
  }

  [data-testid="stChatInput"] input,
  [data-testid="stChatInput"] textarea {
    background: #f8fafc !important;
    color: #0f172a !important;
    font-size: 14px !important;
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    padding: 10px 12px !important;
  }
}
"""
