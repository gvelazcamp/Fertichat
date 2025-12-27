Ver todo:
sql

SELECT * FROM chat_log ORDER BY fecha DESC LIMIT 50

Ver solo los que fallaron (sin datos):
sql

SELECT * FROM chat_log WHERE tuvo_datos = 0 ORDER BY fecha DESC

Ver por intención específica:
sql

SELECT * FROM chat_log WHERE intencion = 'detalle_compras_proveedor_anio' ORDER BY fecha DESC


Buscar una pregunta:
sql

SELECT * FROM chat_log WHERE pregunta LIKE '%roche%' ORDER BY fecha DESC

Buscar Audit observaciones
SELECT *
FROM chat_log
WHERE observaciones LIKE '%\\\\%';
