# =========================
# IA_INTERPRETADOR.PY - VERSIÓN MEJORADA (CANÓNICA)
# =========================
# OBJETIVO:
# - NO romper SQL ni orquestador
# - Mes SIEMPRE YYYY-MM
# - Reconocer proveedores y artículos desde Supabase
# - Incluir TABLA CANÓNICA (50 combinaciones) para guiar a la IA
# =========================

import os
import re
import json
from typing import Dict, Optional, List
from datetime import datetime

import streamlit as st
from openai import OpenAI
from config import OPENAI_MODEL

# =====================================================================
# CONFIGURACIÓN OPENAI
# =====================================================================

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =====================================================================
# REGLAS FIJAS
# =====================================================================

MESES = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}

ANIOS_VALIDOS = {2023, 2024, 2025, 2026}

MAX_PROVEEDORES = 5
MAX_ARTICULOS = 5
MAX_MESES = 6
MAX_ANIOS = 4  # (2023–2026)

# =====================================================================
# TABLA DE TIPOS (LO QUE DEVUELVE EL INTÉRPRETE)
# =====================================================================

TABLA_TIPOS = """
| TIPO | DESCRIPCIÓN | PARÁMETROS | EJEMPLOS |
|------|-------------|------------|----------|
| compras_anio | Todas las compras de un año | anio | "compras 2025", "que compramos en 2025" |
| compras_proveedor_mes | Compras de un proveedor en un mes | proveedor, mes (YYYY-MM) | "compras roche noviembre 2025" |
| compras_proveedor_anio | Compras de un proveedor en un año | proveedor, anio | "compras roche 2025" |
| compras_mes | Todas las compras de un mes | mes (YYYY-MM) | "compras noviembre 2025" |
| ultima_factura | Última factura de un artículo/proveedor | patron | "ultima factura vitek" |
| facturas_articulo | Todas las facturas de un artículo | articulo | "cuando vino vitek" |
| stock_total | Resumen total de stock | (ninguno) | "stock total" |
| stock_articulo | Stock de un artículo | articulo | "stock vitek" |
| comparar_proveedor_meses | Comparar compras proveedor mes vs mes | proveedor, mes1, mes2, label1, label2 | "comparar compras roche junio julio 2025" |
| comparar_proveedor_anios | Comparar compras proveedor año vs año | proveedor, anios | "comparar compras roche 2024 2025" |
| conversacion | Saludos y charla casual | (ninguno) | "hola", "gracias" |
| conocimiento | Preguntas generales | (ninguno) | "que es HPV" |
| no_entendido | No se entiende | sugerencia | (ambiguo) |
"""

# =====================================================================
# TABLA CANÓNICA (50 combinaciones permitidas) - PARA GUIAR A LA IA
# (No rompe nada: es guía / contrato mental del intérprete)
# =====================================================================

TABLA_CANONICA_50 = r"""
| # | ACCIÓN | OBJETO | TIEMPO | MULTI | TIPO (output) | PARAMS |
|---|--------|--------|--------|-------|---------------|--------|
| 01 | compras | (ninguno) | anio | no | compras_anio | anio |
| 02 | compras | (ninguno) | mes | no | compras_mes | mes |
| 03 | compras | proveedor | anio | no | compras_proveedor_anio | proveedor, anio |
| 04 | compras | proveedor | mes | no | compras_proveedor_mes | proveedor, mes |
| 05 | compras | proveedor | mes | si (<=5) | compras_proveedor_mes | proveedor(s), mes |
| 06 | compras | proveedor | anio | si (<=5) | compras_proveedor_anio | proveedor(s), anio |
| 07 | compras | (ninguno) | meses | si (<=6) | compras_mes | mes(s) |
| 08 | compras | (ninguno) | anios | si (<=4) | compras_anio | anio(s) |
| 09 | compras | articulo | (ninguno) | no | facturas_articulo | articulo |
| 10 | compras | articulo | anio | no | facturas_articulo | articulo (+ filtro anio si existiera) |
| 11 | compras | articulo | mes | no | facturas_articulo | articulo (+ filtro mes si existiera) |
| 12 | stock | (ninguno) | (ninguno) | no | stock_total | - |
| 13 | stock | articulo | (ninguno) | no | stock_articulo | articulo |
| 14 | ultima_factura | articulo | (ninguno) | no | ultima_factura | patron |
| 15 | ultima_factura | proveedor | (ninguno) | no | ultima_factura | patron |
| 16 | comparar | proveedor | mes+mes (mismo anio) | no | comparar_proveedor_meses | proveedor, mes1, mes2, label1, label2 |
| 17 | comparar | proveedor | anio+anio | no | comparar_proveedor_anios | proveedor, anios |
| 18 | comparar compras | proveedor | mes+mes | no | comparar_proveedor_meses | proveedor, mes1, mes2 |
| 19 | comparar compras | proveedor | anio+anio | no | comparar_proveedor_anios | proveedor, anios |
| 20 | comparar | proveedor+proveedor | mismo mes | si (<=5) | compras_proveedor_mes | proveedor(s), mes |
| 21 | comparar | proveedor+proveedor | mismo anio | si (<=5) | compras_proveedor_anio | proveedor(s), anio |
| 22 | comparar | proveedor | meses (lista) | si (<=6) | comparar_proveedor_meses | proveedor, mes1, mes2 (si hay 2) |
| 23 | comparar | proveedor | anios (lista) | si (<=4) | comparar_proveedor_anios | proveedor, anios |
| 24 | compras | proveedor | "este mes" | no | compras_proveedor_mes | proveedor, mes(actual) |
| 25 | compras | (ninguno) | "este mes" | no | compras_mes | mes(actual) |
| 26 | compras | proveedor | "este anio" | no | compras_proveedor_anio | proveedor, anio(actual) |
| 27 | compras | (ninguno) | "este anio" | no | compras_anio | anio(actual) |
| 28 | compras | proveedor | mes (YYYY-MM) | no | compras_proveedor_mes | proveedor, mes |
| 29 | compras | (ninguno) | mes (YYYY-MM) | no | compras_mes | mes |
| 30 | comparar compras | proveedor | mes(YYYY-MM)+mes(YYYY-MM) | no | comparar_proveedor_meses | proveedor, mes1, mes2 |
| 31 | comparar compras | proveedor | anio+anio | no | comparar_proveedor_anios | proveedor, anios |
| 32 | compras | proveedor | "noviembre 2025" | no | compras_proveedor_mes | proveedor, 2025-11 |
| 33 | compras | (ninguno) | "noviembre 2025" | no | compras_mes | 2025-11 |
| 34 | comparar compras | proveedor | "junio julio 2025" | no | comparar_proveedor_meses | proveedor, 2025-06, 2025-07 |
| 35 | comparar compras | proveedor | "noviembre diciembre 2025" | no | comparar_proveedor_meses | proveedor, 2025-11, 2025-12 |
| 36 | comparar compras | proveedor | "2024 2025" | no | comparar_proveedor_anios | proveedor, [2024,2025] |
| 37 | compras | proveedor | "2025" | no | compras_proveedor_anio | proveedor, 2025 |
| 38 | compras | proveedor | "enero 2026" | no | compras_proveedor_mes | proveedor, 2026-01 |
| 39 | compras | proveedor | "enero" (sin año) | no | compras_proveedor_mes | proveedor, mes(actual o pedir año) |
| 40 | compras | (ninguno) | "enero" (sin año) | no | compras_mes | mes(actual o pedir año) |
| 41 | comparar compras | proveedor | "enero febrero" (sin año) | no | comparar_proveedor_meses | proveedor, pedir año |
| 42 | compras | proveedor | rango meses | si | compras_proveedor_mes | proveedor, mes(s) |
| 43 | compras | proveedor | rango anios | si | compras_proveedor_anio | proveedor, anio(s) |
| 44 | compras | proveedor+proveedor | mes | si | compras_proveedor_mes | proveedor(s), mes |
| 45 | compras | proveedor+proveedor | anio | si | compras_proveedor_anio | proveedor(s), anio |
| 46 | comparar | proveedor | mes vs mes | no | comparar_proveedor_meses | proveedor, mes1, mes2 |
| 47 | comparar | proveedor | anio vs anio | no | comparar_proveedor_anios | proveedor, anios |
| 48 | stock | proveedor | (ninguno) | no | no_entendido | sugerir: "compras proveedor ..." |
| 49 | compras | articulo | (texto libre) | no | facturas_articulo | articulo |
| 50 | no | (ambiguo) | (ambiguo) | - | no_entendido | sugerencia |
"""

# =====================================================================
# CARGA LISTAS DESDE SUPABASE (cache) - PROVEEDORES / ARTÍCULOS
# =====================================================================

@st.cache_data(ttl=60 * 60)
def _cargar_listas_supabase() -> Dict[str, List[str]]:
    proveedores: List[str] = []
    articulos: List[str] = []

    try:
        # En tu repo suele existir supabase_client.py con "supabase"
        from supabase_client import supabase  # type: ignore

        if supabase is None:
            return {"proveedores": [], "articulos": []}

        # -------------------------
        # Proveedores: tabla proveedores, columna nombre (típico)
        # -------------------------
        col_prov_candidates = ["nombre", "Nombre", "NOMBRE"]
        prov_ok = False
        for col in col_prov_candidates:
            try:
                res = supabase.table("proveedores").select(col).execute()
                data = res.data or []
                proveedores = [r.get(col) for r in data if r.get(col)]
                proveedores = [str(x).lower().strip() for x in proveedores if str(x).strip()]
                prov_ok = True
                break
            except Exception:
                continue
        if not prov_ok:
            proveedores = []

        # -------------------------
        # Artículos: tabla articulos, columna descripción (puede variar)
        # (Por tu captura: "Descripción"/"Descripcion"/"descripcion")
        # -------------------------
        col_art_candidates = ["Descripción", "Descripcion", "descripcion", "DESCRIPCION", "DESCRIPCIÓN"]
        art_ok = False
        for col in col_art_candidates:
            try:
                res = supabase.table("articulos").select(col).execute()
                data = res.data or []
                articulos = [r.get(col) for r in data if r.get(col)]
                articulos = [str(x).lower().strip() for x in articulos if str(x).strip()]
                art_ok = True
                break
            except Exception:
                continue
        if not art_ok:
            articulos = []

    except Exception:
        return {"proveedores": [], "articulos": []}

    # Dedup
    proveedores = sorted(list(set(proveedores)))
    articulos = sorted(list(set(articulos)))

    return {"proveedores": proveedores, "articulos": articulos}


_LISTAS = _cargar_listas_supabase()
PROVEEDORES_KNOWN = set(_LISTAS.get("proveedores", []))
ARTICULOS_KNOWN = set(_LISTAS.get("articulos", []))

# =====================================================================
# HELPERS
# =====================================================================

def _normalizar_texto(s: str) -> str:
    return (s or "").lower().strip()


def _extraer_anios(texto: str) -> List[int]:
    anios = re.findall(r"(2023|2024|2025|2026)", texto)
    out = []
    for a in anios:
        try:
            out.append(int(a))
        except Exception:
            pass
    # unique manteniendo orden
    seen = set()
    out2 = []
    for x in out:
        if x not in seen:
            seen.add(x)
            out2.append(x)
    return out2


def _extraer_meses_nombres(texto: str) -> List[str]:
    meses = [m for m in MESES.keys() if m in texto]
    # unique manteniendo orden
    seen = set()
    out = []
    for m in meses:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _to_yyyymm(anio: int, mes_nombre: str) -> str:
    return f"{anio}-{MESES[mes_nombre]}"


def _detectar_proveedores(texto: str, max_items: int = MAX_PROVEEDORES) -> List[str]:
    encontrados = []
    for p in PROVEEDORES_KNOWN:
        if p and p in texto:
            encontrados.append(p)
    # ordenar por longitud desc para preferir matches largos
    encontrados = sorted(set(encontrados), key=lambda x: (-len(x), x))
    return encontrados[:max_items]


def _detectar_articulos(texto: str, max_items: int = MAX_ARTICULOS) -> List[str]:
    encontrados = []
    for a in ARTICULOS_KNOWN:
        if a and a in texto:
            encontrados.append(a)
    encontrados = sorted(set(encontrados), key=lambda x: (-len(x), x))
    return encontrados[:max_items]


# =====================================================================
# PROMPT DEL SISTEMA (OpenAI)
# =====================================================================

def _get_system_prompt() -> str:
    hoy = datetime.now()
    mes_actual = hoy.strftime("%Y-%m")
    anio_actual = hoy.year

    meses_nombres = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    mes_nombre = meses_nombres[hoy.month]

    return f"""
Eres un intérprete EXPERTO de lenguaje natural para un chatbot de compras/stock.

FECHA ACTUAL: {hoy.strftime("%Y-%m-%d")}
MES ACTUAL: {mes_nombre} {anio_actual} (YYYY-MM = {mes_actual})
AÑOS VÁLIDOS: 2023, 2024, 2025, 2026

OBJETIVO:
Devolver SOLO JSON válido con:
- tipo (string)
- parametros (dict)
- debug (string opcional)
- sugerencia (string opcional si no_entendido)

REGLAS DURAS:
- Mes SIEMPRE en formato YYYY-MM.
- "enero 2025" => 2025-01
- "este mes" => {mes_actual}
- "este año" => {anio_actual}
- Si aparecen 2 meses y 1 año con "comparar compras" => comparar_proveedor_meses con mes1 y mes2 (YYYY-MM).
- Si aparecen 2 años con "comparar compras" => comparar_proveedor_anios con anios [a1,a2].
- Si dudas => tipo no_entendido con sugerencia.

TABLA DE TIPOS (output):
{TABLA_TIPOS}

TABLA CANÓNICA (50 combinaciones permitidas):
{TABLA_CANONICA_50}

IMPORTANTE:
- Responde SOLO JSON (sin markdown, sin ```).
""".strip()


# =====================================================================
# FUNCIÓN PRINCIPAL
# =====================================================================

def interpretar_pregunta(pregunta: str) -> Dict:
    """
    Interpreta la pregunta del usuario y devuelve:
    {"tipo": "...", "parametros": {...}, "debug": "...", "sugerencia": "..."}
    """

    if not pregunta or not pregunta.strip():
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "Escribí una consulta.",
            "debug": "pregunta vacía",
        }

    texto_lower = _normalizar_texto(pregunta)

    # ----------------------------------------------------------
    # SALUDOS / CONVERSACIÓN (ANTES de OpenAI)
    # ----------------------------------------------------------
    saludos_simples = {
        "hola", "hola!", "hey", "hey!", "buenos dias", "buen día",
        "buenas tardes", "buenas noches", "buenas", "gracias", "chau", "adios"
    }
    if texto_lower in saludos_simples:
        return {"tipo": "conversacion", "parametros": {}, "debug": "saludo simple"}

    # Si empieza con saludo pero pide datos, NO lo cortamos
    # Ej: "hola ... compras roche noviembre 2025"
    palabras_datos = ["compra", "compras", "stock", "factura", "proveedor", "gasto", "familia", "comparar"]
    tiene_datos = any(p in texto_lower for p in palabras_datos)

    # ----------------------------------------------------------
    # DETECCIÓN LOCAL: proveedores / artículos desde Supabase
    # ----------------------------------------------------------
    proveedores_detectados = _detectar_proveedores(texto_lower)
    articulos_detectados = _detectar_articulos(texto_lower)

    # ----------------------------------------------------------
    # DETECCIÓN LOCAL: comparar compras proveedor mes vs mes
    # "comparar compras roche junio julio 2025"
    # ----------------------------------------------------------
    if "comparar" in texto_lower and "compra" in texto_lower:
        anios = _extraer_anios(texto_lower)
        meses_nombres = _extraer_meses_nombres(texto_lower)

        # preferimos 1 proveedor detectado
        proveedor = proveedores_detectados[0] if proveedores_detectados else None

        # comparar meses (mismo año)
        if proveedor and len(anios) >= 1 and len(meses_nombres) >= 2:
            anio = anios[0]
            if anio in ANIOS_VALIDOS:
                mes1 = _to_yyyymm(anio, meses_nombres[0])
                mes2 = _to_yyyymm(anio, meses_nombres[1])
                return {
                    "tipo": "comparar_proveedor_meses",
                    "parametros": {
                        "proveedor": proveedor,
                        "mes1": mes1,
                        "mes2": mes2,
                        "label1": f"{meses_nombres[0]} {anio}",
                        "label2": f"{meses_nombres[1]} {anio}",
                    },
                    "debug": "comparar proveedor meses (local)",
                }

        # comparar años (mismo proveedor)
        if proveedor and len(anios) >= 2:
            a1, a2 = anios[0], anios[1]
            if a1 in ANIOS_VALIDOS and a2 in ANIOS_VALIDOS:
                return {
                    "tipo": "comparar_proveedor_anios",
                    "parametros": {"proveedor": proveedor, "anios": [a1, a2]},
                    "debug": "comparar proveedor años (local)",
                }

    # ----------------------------------------------------------
    # DETECCIÓN LOCAL: compras proveedor mes (YYYY-MM)
    # "compras roche noviembre 2025"
    # ----------------------------------------------------------
    if "compra" in texto_lower or "compras" in texto_lower:
        anios = _extraer_anios(texto_lower)
        meses_nombres = _extraer_meses_nombres(texto_lower)

        proveedor = proveedores_detectados[0] if proveedores_detectados else None

        # proveedor + mes + año => compras_proveedor_mes
        if proveedor and len(anios) >= 1 and len(meses_nombres) >= 1:
            anio = anios[0]
            if anio in ANIOS_VALIDOS:
                mes = _to_yyyymm(anio, meses_nombres[0])
                return {
                    "tipo": "compras_proveedor_mes",
                    "parametros": {"proveedor": proveedor, "mes": mes},
                    "debug": "compras proveedor mes (local)",
                }

        # proveedor + año => compras_proveedor_anio
        if proveedor and len(anios) >= 1 and len(meses_nombres) == 0:
            anio = anios[0]
            if anio in ANIOS_VALIDOS:
                return {
                    "tipo": "compras_proveedor_anio",
                    "parametros": {"proveedor": proveedor, "anio": anio},
                    "debug": "compras proveedor año (local)",
                }

        # solo mes + año => compras_mes
        if not proveedor and len(anios) >= 1 and len(meses_nombres) >= 1:
            anio = anios[0]
            if anio in ANIOS_VALIDOS:
                mes = _to_yyyymm(anio, meses_nombres[0])
                return {
                    "tipo": "compras_mes",
                    "parametros": {"mes": mes},
                    "debug": "compras mes (local)",
                }

        # solo año => compras_anio
        if not proveedor and len(anios) >= 1 and len(meses_nombres) == 0:
            anio = anios[0]
            if anio in ANIOS_VALIDOS:
                return {
                    "tipo": "compras_anio",
                    "parametros": {"anio": anio},
                    "debug": "compras año (local)",
                }

    # ----------------------------------------------------------
    # DETECCIÓN LOCAL: stock articulo
    # ----------------------------------------------------------
    if "stock" in texto_lower:
        if articulos_detectados:
            return {
                "tipo": "stock_articulo",
                "parametros": {"articulo": articulos_detectados[0]},
                "debug": "stock articulo (local)",
            }
        return {"tipo": "stock_total", "parametros": {}, "debug": "stock total (local)"}

    # ----------------------------------------------------------
    # SI NO HAY OPENAI -> fallback básico
    # ----------------------------------------------------------
    if not client:
        return _fallback_basico(texto_lower)

    # ----------------------------------------------------------
    # OPENAI (solo si hace falta)
    # Le pasamos pistas de proveedor/artículo detectados (si hay)
    # ----------------------------------------------------------
    try:
        pistas = []
        if proveedores_detectados:
            pistas.append(f"PROVEEDOR_DETECTADO: {proveedores_detectados[0]}")
        if articulos_detectados:
            pistas.append(f"ARTICULO_DETECTADO: {articulos_detectados[0]}")
        pistas_txt = "\n".join(pistas).strip()

        user_content = pregunta
        if pistas_txt:
            user_content = f"{pregunta}\n\n{pistas_txt}"

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _get_system_prompt()},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=500,
            timeout=15,
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        content = content.strip()

        resultado = json.loads(content)

        if "tipo" not in resultado:
            resultado["tipo"] = "no_entendido"
        if "parametros" not in resultado:
            resultado["parametros"] = {}
        if "debug" not in resultado:
            resultado["debug"] = "openai"

        # ----------------------------------------------------------
        # NORMALIZACIÓN MÍNIMA: mes => YYYY-MM si viene raro
        # ----------------------------------------------------------
        tipo = resultado.get("tipo")
        params = resultado.get("parametros", {})

        # compras_proveedor_mes: asegurar YYYY-MM
        if tipo == "compras_proveedor_mes" and isinstance(params.get("mes"), str):
            m = re.search(r"(2023|2024|2025|2026)[-/ ]?(0[1-9]|1[0-2])", params["mes"])
            if m:
                params["mes"] = f"{m.group(1)}-{m.group(2)}"
                resultado["parametros"] = params

        # comparar_proveedor_meses: asegurar YYYY-MM
        if tipo == "comparar_proveedor_meses":
            for k in ["mes1", "mes2"]:
                if isinstance(params.get(k), str):
                    m = re.search(r"(2023|2024|2025|2026)[-/ ]?(0[1-9]|1[0-2])", params[k])
                    if m:
                        params[k] = f"{m.group(1)}-{m.group(2)}"
            resultado["parametros"] = params

        # si no_entendido -> sugerencia
        if resultado.get("tipo") == "no_entendido" and "sugerencia" not in resultado:
            resultado["sugerencia"] = (
                "Probá así:\n"
                "- compras 2025\n"
                "- compras roche noviembre 2025\n"
                "- comparar compras roche junio julio 2025\n"
                "- comparar compras roche 2024 2025"
            )

        return resultado

    except Exception as e:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "No pude interpretar. Probá: compras roche noviembre 2025",
            "debug": f"error openai: {str(e)[:80]}",
        }


def _fallback_basico(texto_lower: str) -> Dict:
    # Conversación
    if any(s in texto_lower for s in ["hola", "buenos", "gracias", "chau", "adios"]):
        return {"tipo": "conversacion", "parametros": {}, "debug": "fallback conversacion"}

    # Compras año
    m = re.search(r"(2023|2024|2025|2026)", texto_lower)
    if "compra" in texto_lower and m:
        return {"tipo": "compras_anio", "parametros": {"anio": int(m.group(1))}, "debug": "fallback compras_anio"}

    return {
        "tipo": "no_entendido",
        "parametros": {},
        "sugerencia": (
            "Probá así:\n"
            "- compras 2025\n"
            "- compras roche noviembre 2025\n"
            "- comparar compras roche junio julio 2025"
        ),
        "debug": "fallback no_entendido",
    }


# =====================================================================
# MAPEO TIPO → FUNCIÓN SQL (NO TOCAR SQL)
# OJO: acá solo declaramos lo que YA existe/usa tu app.
# Comparativas quedan como tipo válido aunque no estén mapeadas a SQL acá.
# =====================================================================

MAPEO_FUNCIONES = {
    "compras_anio": {
        "funcion": "get_compras_anio",
        "params": ["anio"],
        "resumen": "get_total_compras_anio",
    },
    "compras_proveedor_mes": {
        "funcion": "get_detalle_compras_proveedor_mes",
        "params": ["proveedor", "mes"],
    },
    "compras_proveedor_anio": {
        "funcion": "get_detalle_compras_proveedor_anio",
        "params": ["proveedor", "anio"],
        "resumen": "get_total_compras_proveedor_anio",
    },
    "compras_mes": {
        "funcion": "get_compras_por_mes_excel",
        "params": ["mes"],
    },
    "ultima_factura": {
        "funcion": "get_ultima_factura_inteligente",
        "params": ["patron"],
    },
    "facturas_articulo": {
        "funcion": "get_facturas_de_articulo",
        "params": ["articulo"],
    },
    "stock_total": {
        "funcion": "get_stock_total",
        "params": [],
    },
    "stock_articulo": {
        "funcion": "get_stock_articulo",
        "params": ["articulo"],
    },
}


def obtener_info_tipo(tipo: str) -> Optional[Dict]:
    """Obtiene la información de mapeo para un tipo"""
    return MAPEO_FUNCIONES.get(tipo)


def es_tipo_valido(tipo: str) -> bool:
    """Verifica si un tipo es válido"""
    tipos_especiales = [
        "conversacion",
        "conocimiento",
        "no_entendido",
        "comparar_proveedor_meses",
        "comparar_proveedor_anios",
    ]
    return tipo in MAPEO_FUNCIONES or tipo in tipos_especiales
