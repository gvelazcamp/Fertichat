"""
DIAGNÓSTICO DE BASE DE DATOS - FERTILAB
Ejecutar: python diagnostico_db.py

Verifica:
1. Totales por proveedor
2. Registros duplicados
3. Comparación de cálculos
"""

import pymysql
import pandas as pd

# Conexión
def conectar():
    return pymysql.connect(
        host='localhost',
        port=3307,
        user='root',
        password='1234',
        database='chatbot',
        cursorclass=pymysql.cursors.DictCursor
    )

def ejecutar(sql, params=None):
    conn = conectar()
    try:
        df = pd.read_sql(sql, conn, params=params)
        return df
    finally:
        conn.close()

print("="*70)
print("DIAGNÓSTICO DE BASE DE DATOS - FERTILAB")
print("="*70)

# =====================================================================
# 1. VERIFICAR ESTRUCTURA DE UN REGISTRO
# =====================================================================
print("\n1️⃣ MUESTRA DE UN REGISTRO (para ver estructura):")
print("-"*50)

sql = """
SELECT 
    Proveedor,
    Articulo,
    `N Factura`,
    Fecha,
    cantidad,
    Total,
    Mes
FROM chatbot 
WHERE Proveedor LIKE '%ROCHE%' 
  AND (tipo_comprobante = 'Compra Contado' OR tipo_comprobante LIKE 'Compra%')
LIMIT 3
"""
df = ejecutar(sql)
print(df.to_string())

# =====================================================================
# 2. TOTAL ROCHE 2025 - MÉTODO SIMPLE
# =====================================================================
print("\n\n2️⃣ TOTAL ROCHE 2025 - SUM(Total) directo:")
print("-"*50)

sql = """
SELECT 
    COUNT(*) as Registros,
    SUM(
        CAST(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(TRIM(Total), '.', ''),
                            ',', '.'
                        ),
                        '(', '-'
                    ),
                    ')', ''
                ),
                '$', ''
            ) AS DECIMAL(15,2)
        )
    ) as Total_Calculado
FROM chatbot
WHERE Proveedor LIKE '%ROCHE%'
  AND (tipo_comprobante = 'Compra Contado' OR tipo_comprobante LIKE 'Compra%')
  AND Mes LIKE '2025%'
"""
df = ejecutar(sql)
print(df.to_string())

# =====================================================================
# 3. VERIFICAR DUPLICADOS POR N FACTURA + ARTICULO
# =====================================================================
print("\n\n3️⃣ POSIBLES DUPLICADOS (misma factura + artículo aparece más de 1 vez):")
print("-"*50)

sql = """
SELECT 
    `N Factura`,
    Articulo,
    Proveedor,
    COUNT(*) as Veces,
    GROUP_CONCAT(DISTINCT Total) as Totales_Distintos
FROM chatbot
WHERE Proveedor LIKE '%ROCHE%'
  AND (tipo_comprobante = 'Compra Contado' OR tipo_comprobante LIKE 'Compra%')
  AND Mes LIKE '2025%'
GROUP BY `N Factura`, Articulo, Proveedor
HAVING COUNT(*) > 1
LIMIT 20
"""
df = ejecutar(sql)
if df.empty:
    print("✅ No hay duplicados de factura+artículo")
else:
    print(f"⚠️ HAY {len(df)} POSIBLES DUPLICADOS:")
    print(df.to_string())

# =====================================================================
# 4. TOTAL POR MES (ROCHE 2025)
# =====================================================================
print("\n\n4️⃣ DESGLOSE POR MES - ROCHE 2025:")
print("-"*50)

sql = """
SELECT 
    Mes,
    COUNT(*) as Registros,
    SUM(
        CAST(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(TRIM(Total), '.', ''),
                            ',', '.'
                        ),
                        '(', '-'
                    ),
                    ')', ''
                ),
                '$', ''
            ) AS DECIMAL(15,2)
        )
    ) as Total
FROM chatbot
WHERE Proveedor LIKE '%ROCHE%'
  AND (tipo_comprobante = 'Compra Contado' OR tipo_comprobante LIKE 'Compra%')
  AND Mes LIKE '2025%'
GROUP BY Mes
ORDER BY Mes
"""
df = ejecutar(sql)
print(df.to_string())
print(f"\n📊 SUMA TOTAL: ${df['Total'].sum():,.2f}")

# =====================================================================
# 5. VERIFICAR SI HAY FACTURAS CON MISMO NÚMERO PERO DISTINTO TOTAL
# =====================================================================
print("\n\n5️⃣ FACTURAS CON MISMO NÚMERO PERO DISTINTOS TOTALES:")
print("-"*50)

sql = """
SELECT 
    `N Factura`,
    COUNT(DISTINCT Total) as Totales_Distintos,
    COUNT(*) as Lineas,
    SUM(
        CAST(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(TRIM(Total), '.', ''),
                            ',', '.'
                        ),
                        '(', '-'
                    ),
                    ')', ''
                ),
                '$', ''
            ) AS DECIMAL(15,2)
        )
    ) as Suma_Total
FROM chatbot
WHERE Proveedor LIKE '%ROCHE%'
  AND (tipo_comprobante = 'Compra Contado' OR tipo_comprobante LIKE 'Compra%')
  AND Mes LIKE '2025%'
GROUP BY `N Factura`
ORDER BY Lineas DESC
LIMIT 15
"""
df = ejecutar(sql)
print(df.to_string())

# =====================================================================
# 6. TOP 5 PROVEEDORES 2025
# =====================================================================
print("\n\n6️⃣ TOP 10 PROVEEDORES 2025 (para comparar):")
print("-"*50)

sql = """
SELECT 
    Proveedor,
    COUNT(*) as Registros,
    SUM(
        CAST(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(TRIM(Total), '.', ''),
                            ',', '.'
                        ),
                        '(', '-'
                    ),
                    ')', ''
                ),
                '$', ''
            ) AS DECIMAL(15,2)
        )
    ) as Total
FROM chatbot
WHERE (tipo_comprobante = 'Compra Contado' OR tipo_comprobante LIKE 'Compra%')
  AND Mes LIKE '2025%'
GROUP BY Proveedor
ORDER BY Total DESC
LIMIT 10
"""
df = ejecutar(sql)
print(df.to_string())

print("\n" + "="*70)
print("FIN DEL DIAGNÓSTICO")
print("="*70)
