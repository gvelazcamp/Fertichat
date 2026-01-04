# =========================
# UI_COMPRAS.PY - CON TOTALES Y PESTAÑAS
# =========================

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# IMPORTS
from ia_interpretador import interpretar_pregunta, obtener_info_tipo
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
# INICIALIZAR HISTORIAL
# =========================

def inicializar_historial():
    if "historial_compras" not in st.session_state:
        st.session_state["historial_compras"] = []


# =========================
# CALCULAR TOTALES POR MONEDA
# =========================

def calcular_totales_por_moneda(df: pd.DataFrame) -> dict:
    """
    Calcula totales separados por moneda si la columna 'Moneda' existe
    """
    if df is None or len(df) == 0:
        return {"Pesos": 0, "USD": 0}
    
    # Verificar si existe columna de moneda
    col_moneda = None
    for col in df.columns:
        if col.lower() in ['moneda', 'currency']:
            col_moneda = col
            break
    
    # Verificar si existe columna de total
    col_total = None
    for col in df.columns:
        if col.lower() in ['total', 'monto', 'importe', 'valor']:
            col_total = col
            break
    
    if not col_moneda or not col_total:
        return None
    
    try:
        # Limpiar y convertir totales
        df_calc = df.copy()
        df_calc[col_total] = df_calc[col_total].astype(str).str.replace('.', '').str.replace(',', '.').str.replace('$', '').str.strip()
        df_calc[col_total] = pd.to_numeric(df_calc[col_total], errors='coerce').fillna(0)
        
        # Calcular por moneda
        totales = {}
        
        # Pesos
        pesos_df = df_calc[df_calc[col_moneda].str.contains('$|peso|ARS|ars', case=False, na=False)]
        totales['Pesos'] = pesos_df[col_total].sum()
        
        # USD
        usd_df = df_calc[df_calc[col_moneda].str.contains('USD|US|dolar|dólar', case=False, na=False)]
        totales['USD'] = usd_df[col_total].sum()
        
        return totales
    
    except Exception as e:
        print(f"Error calculando totales: {e}")
        return None


# =========================
# GENERAR EXPLICACIÓN CON IA
# =========================

def generar_explicacion_ia(df: pd.DataFrame, pregunta: str, tipo: str) -> str:
    """
    Genera una explicación de los resultados usando OpenAI
    """
    try:
        if df is None or len(df) == 0:
            return "No hay datos para analizar."
        
        # Resumen básico
        resumen = f"La consulta '{pregunta}' devolvió {len(df)} resultados.\n\n"
        
        # Totales por moneda
        totales = calcular_totales_por_moneda(df)
        if totales:
            resumen += f"**Totales:**\n"
            if totales.get('Pesos', 0) > 0:
                resumen += f"- Pesos: ${totales['Pesos']:,.2f}\n"
            if totales.get('USD', 0) > 0:
                resumen += f"- USD: ${totales['USD']:,.2f}\n"
        
        # Top 3 items si hay columna de proveedor o artículo
        if 'proveedor' in df.columns:
            top3 = df.groupby('proveedor').size().sort_values(ascending=False).head(3)
            resumen += f"\n**Top 3 proveedores por cantidad de registros:**\n"
            for prov, cant in top3.items():
                resumen += f"- {prov}: {cant} registros\n"
        
        elif 'articulo' in df.columns:
            top3 = df.groupby('articulo').size().sort_values(ascending=False).head(3)
            resumen += f"\n**Top 3 artículos por cantidad de registros:**\n"
            for art, cant in top3.items():
                resumen += f"- {art}: {cant} registros\n"
        
        return resumen
    
    except Exception as e:
        return f"No se pudo generar explicación: {str(e)}"


# =========================
# GENERAR GRÁFICO
# =========================

def generar_grafico(df: pd.DataFrame, tipo: str) -> object:
    """
    Genera un gráfico según el tipo de consulta
    """
    try:
        if df is None or len(df) == 0:
            return None
        
        # GRÁFICO DE BARRAS - Top proveedores/artículos
        if 'proveedor' in df.columns and 'total' in df.columns:
            # Agrupar por proveedor
            df_grouped = df.groupby('proveedor')['total'].sum().sort_values(ascending=False).head(10)
            fig = px.bar(
                x=df_grouped.values,
                y=df_grouped.index,
                orientation='h',
                title="Top 10 Proveedores por Total",
                labels={'x': 'Total', 'y': 'Proveedor'}
            )
            return fig
        
        elif 'articulo' in df.columns and 'total' in df.columns:
            # Agrupar por artículo
            df_grouped = df.groupby('articulo')['total'].sum().sort_values(ascending=False).head(10)
            fig = px.bar(
                x=df_grouped.values,
                y=df_grouped.index,
                orientation='h',
                title="Top 10 Artículos por Total",
                labels={'x': 'Total', 'y': 'Artículo'}
            )
            return fig
        
        # GRÁFICO DE LÍNEA TEMPORAL - Si hay fechas
        elif 'Fecha' in df.columns or 'fecha' in df.columns:
            col_fecha = 'Fecha' if 'Fecha' in df.columns else 'fecha'
            df_temp = df.copy()
            df_temp[col_fecha] = pd.to_datetime(df_temp[col_fecha], errors='coerce')
            df_temp = df_temp.dropna(subset=[col_fecha])
            
            if len(df_temp) > 0:
                df_grouped = df_temp.groupby(df_temp[col_fecha].dt.to_period('M')).size()
                fig = px.line(
                    x=[str(p) for p in df_grouped.index],
                    y=df_grouped.values,
                    title="Registros por mes",
                    labels={'x': 'Mes', 'y': 'Cantidad'}
                )
                return fig
        
        return None
    
    except Exception as e:
        print(f"Error generando gráfico: {e}")
        return None


# =========================
# ROUTER SQL
# =========================

def ejecutar_consulta_por_tipo(tipo: str, parametros: dict):
    
    if tipo == "compras_anio":
        return get_compras_anio(parametros["anio"])
    
    elif tipo == "compras_proveedor_mes":
        return get_detalle_compras_proveedor_mes(parametros["proveedor"], parametros["mes"])
    
    elif tipo == "compras_proveedor_anio":
        return get_detalle_compras_proveedor_anio(parametros["proveedor"], parametros["anio"])
    
    elif tipo == "compras_articulo_mes":
        return get_detalle_compras_articulo_mes(parametros["articulo"], parametros["mes"])
    
    elif tipo == "compras_articulo_anio":
        return get_detalle_compras_articulo_anio(parametros["articulo"], parametros["anio"])
    
    elif tipo == "compras_mes":
        return get_compras_por_mes_excel(parametros["mes"])
    
    elif tipo == "ultima_factura":
        return get_ultima_factura_inteligente(parametros["patron"])
    
    elif tipo == "facturas_articulo":
        return get_facturas_de_articulo(parametros["articulo"])
    
    elif tipo == "detalle_factura":
        return get_detalle_factura_por_numero(parametros["nro_factura"])
    
    elif tipo == "comparar_proveedor_meses":
        return get_comparacion_proveedor_meses(parametros["mes1"], parametros["mes2"], parametros["proveedor"])
    
    elif tipo == "comparar_proveedor_anios":
        return get_comparacion_proveedor_anios_monedas(parametros["anios"], parametros["proveedor"])
    
    elif tipo == "comparar_articulo_meses":
        return get_comparacion_articulo_meses(parametros["mes1"], parametros["mes2"], parametros["articulo"])
    
    elif tipo == "comparar_articulo_anios":
        return get_comparacion_articulo_anios(parametros["anios"], parametros["articulo"])
    
    elif tipo == "comparar_familia_meses":
        moneda = parametros.get("moneda", "pesos")
        return get_comparacion_familia_meses_moneda(parametros["mes1"], parametros["mes2"], moneda)
    
    elif tipo == "comparar_familia_anios":
        return get_comparacion_familia_anios_monedas(parametros["anios"])
    
    elif tipo == "gastos_familias_mes":
        return get_gastos_todas_familias_mes(parametros["mes"])
    
    elif tipo == "gastos_familias_anio":
        return get_gastos_todas_familias_anio(parametros["anio"])
    
    elif tipo == "gastos_secciones":
        return get_gastos_secciones_detalle_completo(parametros["familias"], parametros["mes"])
    
    elif tipo == "top_proveedores":
        moneda = parametros.get("moneda", "pesos")
        anio = parametros.get("anio")
        mes = parametros.get("mes")
        return get_top_10_proveedores_chatbot(moneda, anio, mes)
    
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
        raise ValueError(f"Tipo '{tipo}' no implementado")


# =========================
# UI PRINCIPAL
# =========================

def Compras_IA():
    
    inicializar_historial()
    
    st.markdown("### 🤖 Asistente de Compras IA")
    
    # Botón limpiar
    if st.button("🗑️ Limpiar chat"):
        st.session_state["historial_compras"] = []
        st.rerun()
    
    st.markdown("---")
    
    # MOSTRAR HISTORIAL
    for idx, msg in enumerate(st.session_state["historial_compras"]):
        with st.chat_message(msg["role"]):
            
            # Texto
            st.markdown(msg["content"])
            
            # Si hay tabla y totales
            if "df" in msg and msg["df"] is not None:
                df = msg["df"]
                
                # TOTALES AL COSTADO
                totales = calcular_totales_por_moneda(df)
                if totales:
                    col1, col2, col3 = st.columns([1, 1, 3])
                    with col1:
                        st.metric("💵 Total Pesos", f"${totales.get('Pesos', 0):,.2f}")
                    with col2:
                        st.metric("💵 Total USD", f"${totales.get('USD', 0):,.2f}")
                
                st.markdown("---")
                
                # PESTAÑAS: Tabla / Gráfico / Explicación
                tab1, tab2, tab3 = st.tabs(["📊 Tabla", "📈 Gráfico", "💡 Explicación"])
                
                with tab1:
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    # Generar Excel en memoria
                    from io import BytesIO
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Resultados')
                    buffer.seek(0)
                    
                    st.download_button(
                        "📥 Descargar Excel",
                        buffer,
                        f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_{msg['timestamp']}_{idx}"
                    )
                
                with tab2:
                    fig = generar_grafico(df, msg.get("tipo", ""))
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No se puede generar gráfico para este tipo de datos")
                
                with tab3:
                    explicacion = generar_explicacion_ia(df, msg.get("pregunta", ""), msg.get("tipo", ""))
                    st.markdown(explicacion)
    
    # INPUT
    pregunta = st.chat_input("Escribí tu consulta...")
    
    if pregunta:
        
        # Agregar pregunta al historial
        st.session_state["historial_compras"].append({
            "role": "user",
            "content": pregunta,
            "timestamp": datetime.now().timestamp()
        })
        
        # Procesar
        resultado = interpretar_pregunta(pregunta)
        tipo = resultado.get("tipo", "")
        parametros = resultado.get("parametros", {})
        
        respuesta_content = ""
        respuesta_df = None
        
        # CONVERSACIÓN
        if tipo == "conversacion":
            respuesta_content = responder_con_openai(pregunta, tipo="conversacion")
        
        # CONOCIMIENTO
        elif tipo == "conocimiento":
            respuesta_content = responder_con_openai(pregunta, tipo="conocimiento")
        
        # NO ENTENDIDO
        elif tipo == "no_entendido":
            respuesta_content = "🤔 No entendí bien tu pregunta."
            if resultado.get("sugerencia"):
                respuesta_content += f"\n\n**Sugerencia:** {resultado['sugerencia']}"
        
        # CONSULTA DE DATOS
        else:
            try:
                resultado_sql = ejecutar_consulta_por_tipo(tipo, parametros)
                
                if isinstance(resultado_sql, pd.DataFrame):
                    if len(resultado_sql) == 0:
                        respuesta_content = "⚠️ No se encontraron resultados"
                    else:
                        respuesta_content = f"✅ Encontré **{len(resultado_sql)}** resultados"
                        respuesta_df = resultado_sql
                else:
                    respuesta_content = str(resultado_sql)
                
            except Exception as e:
                respuesta_content = f"❌ Error: {str(e)}"
        
        # Agregar respuesta al historial
        st.session_state["historial_compras"].append({
            "role": "assistant",
            "content": respuesta_content,
            "df": respuesta_df,
            "tipo": tipo,
            "pregunta": pregunta,
            "timestamp": datetime.now().timestamp()
        })
        
        st.rerun()
