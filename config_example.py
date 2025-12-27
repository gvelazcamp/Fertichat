# =====================================================================
# 🔧 CONFIGURACIÓN DE EJEMPLO - FERTI CHAT
# =====================================================================
# 
# INSTRUCCIONES:
# 1. Copiá este archivo y renombralo a "config.py"
# 2. Completá con tus credenciales reales
# 3. NO subas config.py a GitHub (ya está en .gitignore)
#
# =====================================================================

# =====================================================================
# 🗄️ BASE DE DATOS MySQL/MariaDB
# =====================================================================

DB_CONFIG = {
    "host": "tu-servidor.com",        # Ejemplo: "localhost" o "192.168.1.100"
    "port": 3306,                      # Puerto por defecto de MySQL
    "user": "tu_usuario",              # Usuario de la base de datos
    "password": "tu_contraseña",       # Contraseña del usuario
    "database": "nombre_base_datos",   # Nombre de la base de datos
    "charset": "utf8mb4",
    "collation": "utf8mb4_general_ci",
}

# =====================================================================
# 🤖 OPENAI API
# =====================================================================

import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # NO hardcodear

# Modelo a usar (opciones: "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo")
OPENAI_MODEL = "gpt-4o-mini"

# =====================================================================
# ⚙️ CONFIGURACIÓN DE LA APLICACIÓN
# =====================================================================

# Días para alertas de vencimiento de lotes
DIAS_ALERTA_VENCIMIENTO = 30

# Límite de registros por consulta
LIMITE_REGISTROS = 200

# =====================================================================
# 🌱 INFORMACIÓN DE LA EMPRESA
# =====================================================================

EMPRESA_NOMBRE = "Ferti Chat"
EMPRESA_LOGO = "🌱"  # Emoji o ruta a imagen
