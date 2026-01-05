# =====================================================================
# IA_INTERPRETADOR.PY - VERSIÓN ESTABLE + SLOTS + COMPARATIVAS
# =====================================================================

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
client = OpenAI(api_key=OPENAI_API_KEY)

# =====================================================================
# CONSTANTES / REGLAS
# =====================================================================

ANIOS_VALIDOS = [2023, 2024, 2025, 2026]

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

MAX_PROVEEDORES = 5
MAX_ARTICULOS = 5
MAX_MESES = 6
MAX_ANIOS = 4

# =====================================================================
# TABLA DE ACCIONES CANÓNICAS (GUÍA – NO REGLA DURA)
# =====================================================================

ACCIONES_CANONICAS = [
    # COMPRAS
    ("compras", "proveedor", "mes"),
    ("compras", "proveedor", "anio"),
    ("compras", "articulo", "mes"),
    ("compras", "articulo", "anio"),
    ("compras", "mes", None),
    ("compras", "anio", None),

    # COMPARAR
    ("comparar", "proveedor+proveedor", "mes+mes"),
    ("comparar", "proveedor+proveedor", "anio+anio"),
    ("comparar", "articulo+articulo", "mes+mes"),
    ("comparar", "articulo+articulo", "anio+anio"),

    # STOCK
    ("stock", "articulo", None),
    ("stock", "proveedor", None),
    ("stock", None, None),

    # GASTOS
    ("gastos", "familia", "mes"),
    ("gastos", "familia", "anio"),
    ("gastos", "proveedor", "mes"),
    ("gastos", "proveedor", "anio"),

    # TOP / RANKING
    ("top", "proveedores", "anio"),
    ("top", "articulos", "anio"),

    # HISTORIALES
    ("historial", "articulo", None),
    ("historial", "proveedor", None),
]

# (la lista supera 20; la IA usa esto como CONTEXTO, no ejecución)

# =====================================================================
# CARGA OPCIONAL DE DICCIONARIOS DESDE SUPABASE (NO OBLIGATORIO)
# =====================================================================

@st.cache_data(ttl=3600)
def _cargar_proveedores() -> List[str]:
    """
    Intenta cargar proveedores desde Supabase.
    Si no existe supabase_client, devuelve lista vacía.
    """
    try:
        from supabase_client import supabase
        res = supabase.table("proveedores").select("nombre").execute()
        return [r["nombre"].lower() for r in res.data if r.get("nombre")]
    except Exception:
        return []

@st.cache_data(ttl=3600)
def _cargar_articulos() -> List[str]:
    """
    Intenta cargar artículos desde Supabase.
    """
    try:
        from supabase_client import supabase
        res = supabase.table("articulos").select("Descripcion").execute()
        return [r["Descripcion"].lower() for r in res.data if r.get("Descripcion")]
    except Exception:
        return []

# =====================================================================
# SLOT DETECTION (AYUDA A LA IA – NO REGLA)
# =====================================================================

def detectar_slots_basicos(texto: str) -> Dict:
    texto = texto.lower()

    acciones = []
    if "comparar" in texto:
        acciones.append("comparar")
    if "compra" in texto:
        acciones.append("compras")
    if "stock" in texto:
        acciones.append("stock")
    if "gasto" in texto:
        acciones.append("gastos")

    proveedores_db = _cargar_proveedores()
    articulos_db = _cargar_articulos()

    proveedores = [p for p in proveedores_db if p in texto][:MAX_PROVEEDORES]
    articulos = [a for a in articulos_db if a in texto][:MAX_ARTICULOS]

    anios = [int(a) for a in re.findall(r"(2023|2024|2025|2026)", texto)]

    meses = []
    for nombre, num in MESES.items():
        if nombre in texto and anios:
            meses.append(f"{anios[0]}-{num}")

    return {
        "acciones": acciones,
        "proveedores": proveedores,
        "articulos": articulos,
        "meses": meses[:MAX_MESES],
        "anios": anios[:MAX_ANIOS],
    }

# =====================================================================
# PROMPT DEL SISTEMA
# =====================================================================

def _get_system_prompt(slots: Dict) -> str:
    hoy = datetime.now()
    mes_actual = hoy.strftime("%Y-%m")

    return f"""
Eres un intérprete EXPERTO en lenguaje natural para un sistema de laboratorio.

REGLAS FIJAS:
- Meses SIEMPRE en formato YYYY-MM
- Años válidos: 2023 a 2026
- Proveedores y artículos deben detectarse si existen en BD
- No inventes datos

SEÑALES DETECTADAS (solo ayuda):
{json.dumps(slots, ensure_ascii=False)}

Si no puedes determinar algo con certeza:
- Devuelve tipo "no_entendido"
- Incluye una sugerencia de cómo preguntar

Devuelve SOLO JSON válido.
"""

# =====================================================================
# FUNCIÓN PRINCIPAL
# =====================================================================

def interpretar_pregunta(pregunta: str) -> Dict:

    if not pregunta or not pregunta.strip():
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "Escribí una consulta, por ejemplo: compras roche junio 2025",
            "debug": "pregunta vacía",
        }

    texto_lower = pregunta.lower().strip()

    # ----------------------------------------------------------
    # REGEX DIRECTO: COMPARAR COMPRAS PROVEEDOR MES VS MES
    # Ej: "comparar compras roche junio julio 2025"
    # ----------------------------------------------------------
    patron = re.search(
        r"comparar\s+compras?\s+([a-záéíóúñ]+)\s+"
        r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+"
        r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+"
        r"(2023|2024|2025|2026)",
        texto_lower,
    )

    if patron:
        proveedor = patron.group(1)
        mes1 = f"{patron.group(4)}-{MESES[patron.group(2)]}"
        mes2 = f"{patron.group(4)}-{MESES[patron.group(3)]}"

        return {
            "tipo": "comparar_proveedor_meses",
            "parametros": {
                "proveedor": proveedor,
                "mes1": mes1,
                "mes2": mes2,
            },
            "debug": "regex comparar proveedor meses",
        }

    # ----------------------------------------------------------
    # SLOT DETECTION (AYUDA)
    # ----------------------------------------------------------
    slots = detectar_slots_basicos(pregunta)

    # ----------------------------------------------------------
    # OPENAI
    # ----------------------------------------------------------
    if not OPENAI_API_KEY:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "Configurá la API Key de OpenAI",
            "debug": "sin api key",
        }

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _get_system_prompt(slots)},
                {"role": "user", "content": pregunta},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"```json|```", "", content).strip()
        resultado = json.loads(content)

        resultado.setdefault("parametros", {})
        resultado.setdefault("debug", "openai")

        return resultado

    except Exception as e:
        return {
            "tipo": "no_entendido",
            "parametros": {},
            "sugerencia": "Probá por ejemplo: comparar compras roche junio julio 2025",
            "debug": f"error: {str(e)[:80]}",
        }

# =====================================================================
# MAPEO A SQL (NO TOCADO)
# =====================================================================

MAPEO_FUNCIONES = {
    "compras_anio": {"funcion": "get_compras_anio", "params": ["anio"]},
    "compras_proveedor_mes": {"funcion": "get_detalle_compras_proveedor_mes", "params": ["proveedor", "mes"]},
    "compras_proveedor_anio": {"funcion": "get_detalle_compras_proveedor_anio", "params": ["proveedor", "anio"]},
    "compras_mes": {"funcion": "get_compras_por_mes_excel", "params": ["mes"]},
    "ultima_factura": {"funcion": "get_ultima_factura_inteligente", "params": ["patron"]},
    "facturas_articulo": {"funcion": "get_facturas_de_articulo", "params": ["articulo"]},
    "stock_total": {"funcion": "get_stock_total", "params": []},
    "stock_articulo": {"funcion": "get_stock_articulo", "params": ["articulo"]},
}

def obtener_info_tipo(tipo: str) -> Optional[Dict]:
    return MAPEO_FUNCIONES.get(tipo)

def es_tipo_valido(tipo: str) -> bool:
    return tipo in MAPEO_FUNCIONES or tipo in [
        "comparar_proveedor_meses",
        "comparar_proveedor_anios",
        "conversacion",
        "conocimiento",
        "no_entendido",
    ]
