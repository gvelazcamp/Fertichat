# =========================
# TESTS - Verificar intenciones
# =========================
"""
Ejecutá este archivo para verificar que las intenciones
se detecten correctamente:

    python tests.py
"""

from intent_detector import detectar_intencion

# =====================================================================
# 20 PREGUNTAS MÁS COMUNES
# =====================================================================

TESTS = [
    # Facturas
    ("detalle factura 00699559", "detalle_factura_numero"),
    ("última factura vitek", "ultima_factura_articulo"),
    ("factura completa vitek", "factura_completa_articulo"),
    ("en qué facturas vino vitek", "facturas_articulo"),
    
    # Comparaciones meses
    ("comparar familias junio julio", "comparar_familia_meses"),
    ("comparar proveedores junio vs julio", "comparar_proveedor_meses"),
    ("comparar articulos junio julio 2025", "comparar_articulo_meses"),
    
    # Comparaciones años
    ("comparar proveedores 2023 2024 2025", "comparar_proveedor_anios_monedas"),
    ("comparar articulos 2023 vs 2024", "comparar_articulo_anios_monedas"),
    
    # Detalle por mes/proveedor
    ("compras roche octubre 2024", "detalle_compras_proveedor_mes"),
    ("compras abbott junio", "detalle_compras_proveedor_mes"),
    
    # Total proveedores múltiples períodos
    ("total compras por proveedor octubre 2024 y noviembre 2025", "total_proveedor_moneda_periodos"),
    
    # Compras por mes
    ("compras por mes junio 2025", "compras_por_mes"),
    ("listar compras del mes 2025-06", "compras_por_mes"),
    
    # Gastos secciones
    ("gastos secciones G,FB,ID 2025-06", "gastos_secciones"),
    
    # Gastos familia
    ("gastos familia ID", "gastos_familia"),
    ("gastos familias AF octubre", "gastos_familia"),
    
    # Listar
    ("listar proveedores", "listar_valores"),
    ("listar familias", "listar_valores"),
    
    # Detalle general
    ("detalle compras roche", "detalle"),
]


def run_tests():
    """Ejecuta todos los tests"""
    print("=" * 70)
    print("🧪 EJECUTANDO TESTS DE DETECCIÓN DE INTENCIONES")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for pregunta, esperado in TESTS:
        resultado = detectar_intencion(pregunta)
        tipo_detectado = resultado.get('tipo')
        debug = resultado.get('debug', '')
        
        if tipo_detectado == esperado:
            print(f"✅ PASS: {pregunta}")
            print(f"   → {tipo_detectado}")
            passed += 1
        else:
            print(f"❌ FAIL: {pregunta}")
            print(f"   Esperado: {esperado}")
            print(f"   Obtenido: {tipo_detectado}")
            print(f"   Debug: {debug}")
            failed += 1
        
        print()
    
    print("=" * 70)
    print(f"📊 RESULTADOS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("🎉 ¡Todos los tests pasaron!")
    else:
        print("⚠️  Algunos tests fallaron. Revisá el orden en intent_detector.py")


if __name__ == "__main__":
    run_tests()
