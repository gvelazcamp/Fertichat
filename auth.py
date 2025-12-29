# =====================================================================
# 🔐 MÓDULO DE AUTENTICACIÓN - FERTI CHAT
# =====================================================================
# Sistema de login con usuarios predefinidos
# Solo los usuarios de la lista pueden acceder
# =====================================================================

import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Tuple

# Ruta de la base de datos
DB_PATH = "users.db"

# =====================================================================
# 👥 USUARIOS PREDEFINIDOS (SOLO ESTOS PUEDEN ENTRAR)
# =====================================================================
USUARIOS_PREDEFINIDOS = [
    {"usuario": "gvelazquez", "password": "123abc", "nombre": "G. Velazquez", "empresa": "Fertilab"},
    {"usuario": "dserveti", "password": "abc123", "nombre": "D. Serveti", "empresa": "Fertilab"},
    {"usuario": "jesteves", "password": "123abc", "nombre": "J. Esteves", "empresa": "Fertilab"},
    {"usuario": "sruiz", "password": "123abc", "nombre": "S. Ruiz", "empresa": "Fertilab"},
]

# =====================================================================
# INICIALIZACIÓN DE BASE DE DATOS
# =====================================================================

def init_db():
    """Crea la tabla de usuarios y carga los predefinidos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT,
            empresa TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    
    # Cargar usuarios predefinidos (si no existen)
    for u in USUARIOS_PREDEFINIDOS:
        cursor.execute("SELECT id FROM users WHERE usuario = ?", (u["usuario"].lower(),))
        if not cursor.fetchone():
            password_hash = hash_password(u["password"])
            cursor.execute('''
                INSERT INTO users (usuario, password_hash, nombre, empresa)
                VALUES (?, ?, ?, ?)
            ''', (u["usuario"].lower(), password_hash, u["nombre"], u["empresa"]))
            print(f"✅ Usuario creado: {u['usuario']}")
    
    conn.commit()
    conn.close()

# =====================================================================
# FUNCIONES DE HASH
# =====================================================================

def hash_password(password: str) -> str:
    """Genera hash SHA-256 de la contraseña"""
    salt = "ferti_chat_2024_salt"
    salted = f"{salt}{password}{salt}"
    return hashlib.sha256(salted.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verifica si la contraseña coincide con el hash"""
    return hash_password(password) == password_hash

# =====================================================================
# LOGIN (SOLO USUARIOS PREDEFINIDOS)
# =====================================================================

def login_user(usuario: str, password: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Inicia sesión. Solo funcionan usuarios predefinidos.
    Returns: (éxito, mensaje, datos_usuario)
    """
    if not usuario or not password:
        return False, "Usuario y contraseña son requeridos", None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, usuario, password_hash, nombre, empresa, is_active
        FROM users WHERE usuario = ?
    ''', (usuario.lower().strip(),))
    
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, "Usuario no autorizado", None
    
    user_id, user_usuario, password_hash, nombre, empresa, is_active = user
    
    if not is_active:
        conn.close()
        return False, "Cuenta desactivada", None
    
    if not verify_password(password, password_hash):
        conn.close()
        return False, "Contraseña incorrecta", None
    
    # Actualizar último login
    cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.now(), user_id))
    conn.commit()
    conn.close()
    
    user_data = {
        'id': user_id,
        'usuario': user_usuario,
        'email': f"{user_usuario}@fertilab.com",
        'nombre': nombre,
        'empresa': empresa
    }
    
    return True, f"¡Bienvenido {nombre}!", user_data

# =====================================================================
# CAMBIO DE CONTRASEÑA
# =====================================================================

def change_password(usuario: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    """
    Cambia la contraseña del usuario
    Returns: (éxito, mensaje)
    """
    if len(new_password) < 4:
        return False, "La nueva contraseña debe tener al menos 4 caracteres"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, password_hash FROM users WHERE usuario = ?', (usuario.lower(),))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, "Usuario no encontrado"
    
    user_id, password_hash = user
    
    if not verify_password(old_password, password_hash):
        conn.close()
        return False, "Contraseña actual incorrecta"
    
    # Actualizar contraseña
    new_hash = hash_password(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
    conn.commit()
    conn.close()
    
    return True, "¡Contraseña actualizada!"

# =====================================================================
# FUNCIONES AUXILIARES
# =====================================================================

def get_user_count() -> int:
    """Retorna cantidad de usuarios"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def listar_usuarios() -> list:
    """Lista todos los usuarios"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, usuario, nombre, empresa, last_login FROM users WHERE is_active = 1")
    users = cursor.fetchall()
    conn.close()
    return users

def reset_password(usuario: str, new_password: str) -> Tuple[bool, str]:
    """Reset de contraseña (uso admin)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE usuario = ?', (usuario.lower(),))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return False, "Usuario no encontrado"
    
    new_hash = hash_password(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user[0]))
    conn.commit()
    conn.close()
    
    return True, f"Contraseña de {usuario} reseteada"

# Inicializar DB al importar
init_db()
