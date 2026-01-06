# =========================
# __init__.py - MÓDULO SQL_QUERIES UNIFICADO
# =========================
# Exporta todas las funciones manteniendo 100% compatibilidad

# =====================================================================
# CORE - Conexión y Helpers Base
# =====================================================================
from .sql_core import (
    # Conexión
    get_db_connection,
    ejecutar_consulta,
    
    # Constantes
    TABLE_COMPRAS,
    COL_TIPO_COMP,
    COL_NRO_COMP,
    COL_MONEDA,
    COL_PROV,
    COL_FAMILIA,
    COL_ART,
    COL_ANIO,
    COL_MES,
    COL_FECHA,
    COL_CANT,
    COL_MONTO,
    
    # Helpers SQL
    _sql_fecha_expr,
    _sql_mes_col,
    _sql_moneda_norm_expr,
    _sql_num_from_text,
    _sql_total_num_expr,
    _sql_total_num_expr_usd,
    _sql_total_num_expr_general,
    
    # Listados genéricos
    get_lista_proveedores,
    get_lista_tipos_comprobante,
    get_lista_articulos,
    get_valores_unicos,
    
    # Helpers auxiliares
    get_ultimo_mes_disponible_hasta,
    resolver_mes_existente,
    _safe_ident,
)


# =====================================================================
# COMPRAS - Consultas Transaccionales
# =====================================================================
from .sql_compras import (
    # Compras por año
    get_compras_anio,
    get_total_compras_anio,
    
    # Detalle compras: Proveedor
    get_detalle_compras_proveedor_mes,
    get_detalle_compras_proveedor_anio,
    get_total_compras_proveedor_anio,
    get_detalle_compras_proveedor_anios,
    
    # Detalle compras: Artículo
    get_detalle_compras_articulo_mes,
    get_detalle_compras_articulo_anio,
    get_total_compras_articulo_anio,
    
    # Facturas
    get_detalle_factura_por_numero,
    get_total_factura_por_numero,
    get_ultima_factura_de_articulo,
    get_ultima_factura_inteligente,
    get_ultima_factura_numero_de_articulo,
    get_facturas_de_articulo,
    
    # Series y datasets
    get_serie_compras_agregada,
    get_dataset_completo,
    get_detalle_compras,
    get_compras_por_mes_excel,
    
    # Top proveedores
    get_top_10_proveedores_chatbot,
    
    # Dashboard
    get_dashboard_totales,
    get_dashboard_compras_por_mes,
    get_dashboard_top_proveedores,
    get_dashboard_gastos_familia,
    get_dashboard_ultimas_compras,
    get_total_compras_proveedor_moneda_periodos,
)


# =====================================================================
# COMPARATIVAS - Análisis y Comparaciones
# =====================================================================
from .sql_comparativas import (
    # Comparaciones por meses
    get_comparacion_proveedor_meses,
    
    # Comparaciones por años
    get_comparacion_articulo_anios,
    get_comparacion_proveedor_anios_like,
    get_comparacion_proveedor_anios_monedas,
    get_comparacion_familia_anios_monedas,
    
    # Gastos por familias
    get_gastos_todas_familias_mes,
    get_gastos_todas_familias_anio,
    get_gastos_secciones_detalle_completo,
    get_gastos_por_familia,
)


# =====================================================================
# STOCK - Inventario y Lotes
# =====================================================================
from .sql_stock import (
    # Listados de stock
    get_lista_articulos_stock,
    get_lista_familias_stock,
    get_lista_depositos_stock,
    
    # Búsquedas
    buscar_stock_por_lote,
    get_stock_articulo,
    get_stock_lote_especifico,
    get_stock_familia,
    
    # Resúmenes
    get_stock_total,
    get_stock_por_familia,
    get_stock_por_deposito,
    
    # Alertas y vencimientos
    get_lotes_por_vencer,
    get_lotes_vencidos,
    get_stock_bajo,
    get_alertas_vencimiento_multiple,
)


# =====================================================================
# EXPORTS EXPLÍCITOS (para IDEs y linters)
# =====================================================================
__all__ = [
    # Core
    'get_db_connection',
    'ejecutar_consulta',
    'TABLE_COMPRAS',
    'COL_TIPO_COMP',
    'COL_NRO_COMP',
    'COL_MONEDA',
    'COL_PROV',
    'COL_FAMILIA',
    'COL_ART',
    'COL_ANIO',
    'COL_MES',
    'COL_FECHA',
    'COL_CANT',
    'COL_MONTO',
    '_sql_fecha_expr',
    '_sql_mes_col',
    '_sql_moneda_norm_expr',
    '_sql_num_from_text',
    '_sql_total_num_expr',
    '_sql_total_num_expr_usd',
    '_sql_total_num_expr_general',
    'get_lista_proveedores',
    'get_lista_tipos_comprobante',
    'get_lista_articulos',
    'get_valores_unicos',
    'get_ultimo_mes_disponible_hasta',
    'resolver_mes_existente',
    '_safe_ident',
    
    # Compras
    'get_compras_anio',
    'get_total_compras_anio',
    'get_detalle_compras_proveedor_mes',
    'get_detalle_compras_proveedor_anio',
    'get_total_compras_proveedor_anio',
    'get_detalle_compras_proveedor_anios',
    'get_detalle_compras_articulo_mes',
    'get_detalle_compras_articulo_anio',
    'get_total_compras_articulo_anio',
    'get_detalle_factura_por_numero',
    'get_total_factura_por_numero',
    'get_ultima_factura_de_articulo',
    'get_ultima_factura_inteligente',
    'get_ultima_factura_numero_de_articulo',
    'get_facturas_de_articulo',
    'get_serie_compras_agregada',
    'get_dataset_completo',
    'get_detalle_compras',
    'get_compras_por_mes_excel',
    'get_top_10_proveedores_chatbot',
    'get_dashboard_totales',
    'get_dashboard_compras_por_mes',
    'get_dashboard_top_proveedores',
    'get_dashboard_gastos_familia',
    'get_dashboard_ultimas_compras',
    'get_total_compras_proveedor_moneda_periodos',
    
    # Comparativas
    'get_comparacion_proveedor_meses',
    'get_comparacion_articulo_anios',
    'get_comparacion_proveedor_anios_like',
    'get_comparacion_proveedor_anios_monedas',
    'get_comparacion_familia_anios_monedas',
    'get_gastos_todas_familias_mes',
    'get_gastos_todas_familias_anio',
    'get_gastos_secciones_detalle_completo',
    'get_gastos_por_familia',
    
    # Stock
    'get_lista_articulos_stock',
    'get_lista_familias_stock',
    'get_lista_depositos_stock',
    'buscar_stock_por_lote',
    'get_stock_articulo',
    'get_stock_lote_especifico',
    'get_stock_familia',
    'get_stock_total',
    'get_stock_por_familia',
    'get_stock_por_deposito',
    'get_lotes_por_vencer',
    'get_lotes_vencidos',
    'get_stock_bajo',
    'get_alertas_vencimiento_multiple',
]
