def get_total_facturas_por_moneda_anio(anio: int) -> pd.DataFrame:
    total_expr = _sql_total_num_expr_general()
    sql = f'''
        SELECT
            EXTRACT(YEAR FROM "Fecha"::date) AS anio,
            "Moneda",
            COUNT(DISTINCT "Nro. Comprobante") AS total_facturas,
            SUM({total_expr}) AS monto_total
        FROM chatbot_raw
        WHERE
            EXTRACT(YEAR FROM "Fecha"::date) = %s
            AND (
                "Tipo Comprobante" ILIKE 'Compra%%'
                OR "Tipo Comprobante" ILIKE 'Factura%%'
            )
        GROUP BY
            EXTRACT(YEAR FROM "Fecha"::date),
            "Moneda"
        ORDER BY
            anio,
            "Moneda"
    '''
    return ejecutar_consulta(sql, (anio,))