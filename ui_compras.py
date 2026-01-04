# =========================
# UI_COMPRAS.PY - VERSIÓN SIMPLIFICADA Y FUNCIONAL
# =========================

import streamlit as st
import pandas as pd
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
    for msg in st.session_state["historial_compras"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Si hay tabla
            if "df" in msg and msg["df"] is not None:
                st.dataframe(msg["df"], use_container_width=True, height=400)
                
                csv = msg["df"].to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Descargar CSV",
                    csv,
                    f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    key=f"dl_{msg['timestamp']}"
                )
    
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
        print(f"🔍 Pregunta: {pregunta}")
        
        resultado = interpretar_pregunta(pregunta)
        print(f"🤖 IA respondió: {resultado}")
        
        tipo = resultado.get("tipo", "")
        parametros = resultado.get("parametros", {})
        
        respuesta_content = ""
        respuesta_df = None
        
        # CONVERSACIÓN
        if tipo == "conversacion":
            print("💬 Es conversación, llamando a OpenAI...")
            respuesta_content = responder_con_openai(pregunta, tipo="conversacion")
            print(f"✅ OpenAI respondió: {respuesta_content[:100]}...")
        
        # CONOCIMIENTO
        elif tipo == "conocimiento":
            print("🧠 Es conocimiento, llamando a OpenAI...")
            respuesta_content = responder_con_openai(pregunta, tipo="conocimiento")
            print(f"✅ OpenAI respondió: {respuesta_content[:100]}...")
        
        # NO ENTENDIDO
        elif tipo == "no_entendido":
            respuesta_content = "🤔 No entendí bien tu pregunta."
            if resultado.get("sugerencia"):
                respuesta_content += f"\n\n**Sugerencia:** {resultado['sugerencia']}"
        
        # CONSULTA DE DATOS
        else:
            try:
                print(f"📊 Ejecutando consulta tipo: {tipo}")
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
                print(f"❌ Error: {e}")
                respuesta_content = f"❌ Error: {str(e)}"
        
        # Agregar respuesta al historial
        st.session_state["historial_compras"].append({
            "role": "assistant",
            "content": respuesta_content,
            "df": respuesta_df,
            "timestamp": datetime.now().timestamp()
        })
        
        print("🔄 Haciendo rerun...")
        st.rerun()
