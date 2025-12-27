# =====================================================================
# 🔐 MÓDULO DE AUTENTICACIÓN - FERTI CHAT
# =====================================================================
# Sistema de login con auto-registro y notificación por email
# Fecha: 27 Diciembre 2024
# =====================================================================

import sqlite3
import hashlib
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Tuple

# Ruta de la base de datos
DB_PATH = "users.db"

# =====================================================================
# CONFIGURACIÓN DE EMAIL (SMTP)
# =====================================================================
# Configuración para enviar emails de bienvenida

SMTP_CONFIG = {
    "enabled": False,  # Cambiar a True y configurar para activar emails
    "server": "smtp.gmail.com",
    "port": 587,
    "email": "tu_email@gmail.com",
    "password": "",  # Contraseña de aplicación de Gmail
    "destinatario_copia": "tu_email@gmail.com"
}

# =====================================================================
# INICIALIZACIÓN DE BASE DE DATOS
# =====================================================================

def init_db():
    """Crea la tabla de usuarios si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT,
            empresa TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

# =====================================================================
# FUNCIONES DE HASH
# =====================================================================

def hash_password(password: str) -> str:
    """Genera hash SHA-256 de la contraseña con salt"""
    # Salt fijo para simplicidad (en producción usar salt único por usuario)
    salt = "ferti_chat_2024_salt"
    salted = f"{salt}{password}{salt}"
    return hashlib.sha256(salted.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verifica si la contraseña coincide con el hash"""
    return hash_password(password) == password_hash

# =====================================================================
# VALIDACIONES
# =====================================================================

def validate_email(email: str) -> Tuple[bool, str]:
    """Valida formato de email"""
    if not email:
        return False, "El email es requerido"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """Valida requisitos de contraseña"""
    if not password:
        return False, "La contraseña es requerida"
    
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    
    return True, ""

# =====================================================================
# OPERACIONES DE USUARIO
# =====================================================================

def register_user(email: str, password: str, nombre: str = "", empresa: str = "") -> Tuple[bool, str]:
    """
    Registra un nuevo usuario
    Returns: (éxito, mensaje)
    """
    # Validar email
    valid, msg = validate_email(email)
    if not valid:
        return False, msg
    
    # Validar contraseña
    valid, msg = validate_password(password)
    if not valid:
        return False, msg
    
    # Verificar si ya existe
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
    if cursor.fetchone():
        conn.close()
        return False, "Este email ya está registrado"
    
    # Crear usuario
    try:
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (email, password_hash, nombre, empresa)
            VALUES (?, ?, ?, ?)
        ''', (email.lower(), password_hash, nombre, empresa))
        
        conn.commit()
        conn.close()
        return True, "¡Registro exitoso! Ya podés iniciar sesión"
    
    except Exception as e:
        conn.close()
        return False, f"Error al registrar: {str(e)}"

def enviar_email_bienvenida(email_usuario: str, password: str) -> bool:
    """
    Envía email de bienvenida con las credenciales.
    Retorna True si se envió, False si falló.
    """
    if not SMTP_CONFIG.get("enabled"):
        print(f"📧 Email desactivado. Nuevo usuario: {email_usuario} / {password}")
        return False
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🦋 Bienvenido a Ferti Chat'
        msg['From'] = SMTP_CONFIG['email']
        msg['To'] = SMTP_CONFIG['destinatario_copia']
        
        # Contenido HTML
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background: #f8fafc; padding: 30px; border-radius: 10px;">
                <h2 style="color: #1f2937; text-align: center;">🦋 Ferti Chat</h2>
                <h3 style="color: #374151;">Nuevo usuario registrado</h3>
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Email:</strong> {email_usuario}</p>
                    <p><strong>Contraseña:</strong> {password}</p>
                    <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                <p style="color: #6b7280; font-size: 12px; text-align: center;">
                    Este email fue generado automáticamente por Ferti Chat
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        # Intentar enviar con diferentes métodos
        enviado = False
        
        # Método 1: STARTTLS (puerto 587)
        try:
            print(f"📧 Intentando enviar email via STARTTLS...")
            server = smtplib.SMTP(SMTP_CONFIG['server'], 587, timeout=10)
            server.starttls()
            server.login(SMTP_CONFIG['email'], SMTP_CONFIG['password'])
            server.sendmail(SMTP_CONFIG['email'], SMTP_CONFIG['destinatario_copia'], msg.as_string())
            server.quit()
            enviado = True
        except Exception as e1:
            print(f"⚠️ STARTTLS falló: {e1}")
            
            # Método 2: SSL directo (puerto 465)
            try:
                print(f"📧 Intentando enviar email via SSL...")
                server = smtplib.SMTP_SSL(SMTP_CONFIG['server'], 465, timeout=10)
                server.login(SMTP_CONFIG['email'], SMTP_CONFIG['password'])
                server.sendmail(SMTP_CONFIG['email'], SMTP_CONFIG['destinatario_copia'], msg.as_string())
                server.quit()
                enviado = True
            except Exception as e2:
                print(f"⚠️ SSL falló: {e2}")
                
                # Método 3: Sin encriptación (puerto 25)
                try:
                    print(f"📧 Intentando enviar email via puerto 25...")
                    server = smtplib.SMTP(SMTP_CONFIG['server'], 25, timeout=10)
                    server.login(SMTP_CONFIG['email'], SMTP_CONFIG['password'])
                    server.sendmail(SMTP_CONFIG['email'], SMTP_CONFIG['destinatario_copia'], msg.as_string())
                    server.quit()
                    enviado = True
                except Exception as e3:
                    print(f"⚠️ Puerto 25 falló: {e3}")
        
        if enviado:
            print(f"✅ Email enviado a {SMTP_CONFIG['destinatario_copia']}")
            return True
        else:
            print(f"❌ No se pudo enviar el email por ningún método")
            return False
        
    except Exception as e:
        print(f"❌ Error general enviando email: {e}")
        return False

def login_user(email: str, password: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Inicia sesión. Si el usuario no existe, lo crea automáticamente.
    Returns: (éxito, mensaje, datos_usuario)
    """
    if not email or not password:
        return False, "Email y contraseña son requeridos", None
    
    # Validar formato de email
    valid, msg = validate_email(email)
    if not valid:
        return False, msg, None
    
    # Validar contraseña mínima
    if len(password) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres", None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, email, password_hash, nombre, empresa, is_active
        FROM users WHERE email = ?
    ''', (email.lower(),))
    
    user = cursor.fetchone()
    
    # =========================================================
    # CASO 1: Usuario NO existe → CREAR automáticamente
    # =========================================================
    if not user:
        print(f"🆕 Nuevo usuario: {email}")
        
        # Crear usuario
        password_hash = hash_password(password)
        nombre = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, nombre, empresa)
            VALUES (?, ?, ?, ?)
        ''', (email.lower(), password_hash, nombre, "Fertilab"))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        # Actualizar último login
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.now(), user_id))
        conn.commit()
        conn.close()
        
        # Enviar email de notificación
        enviar_email_bienvenida(email, password)
        
        user_data = {
            'id': user_id,
            'email': email.lower(),
            'nombre': nombre,
            'empresa': "Fertilab"
        }
        
        return True, f"¡Bienvenido {nombre}! Tu cuenta fue creada.", user_data
    
    # =========================================================
    # CASO 2: Usuario EXISTE → Verificar contraseña
    # =========================================================
    user_id, user_email, password_hash, nombre, empresa, is_active = user
    
    if not is_active:
        conn.close()
        return False, "Cuenta desactivada", None
    
    if not verify_password(password, password_hash):
        conn.close()
        return False, "Contraseña incorrecta", None
    
    # Actualizar último login
    cursor.execute('''
        UPDATE users SET last_login = ? WHERE id = ?
    ''', (datetime.now(), user_id))
    
    conn.commit()
    conn.close()
    
    user_data = {
        'id': user_id,
        'email': user_email,
        'nombre': nombre or user_email.split('@')[0],
        'empresa': empresa
    }
    
    return True, "¡Bienvenido!", user_data

def change_password(email: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    """
    Cambia la contraseña del usuario
    Returns: (éxito, mensaje)
    """
    # Validar nueva contraseña
    valid, msg = validate_password(new_password)
    if not valid:
        return False, msg
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, password_hash FROM users WHERE email = ?
    ''', (email.lower(),))
    
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
    cursor.execute('''
        UPDATE users SET password_hash = ? WHERE id = ?
    ''', (new_hash, user_id))
    
    conn.commit()
    conn.close()
    
    return True, "¡Contraseña actualizada correctamente!"

def get_user_count() -> int:
    """Retorna cantidad de usuarios registrados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def crear_usuario(email: str, password: str, nombre: str = "", empresa: str = "Fertilab") -> Tuple[bool, str]:
    """
    Crea un nuevo usuario (para uso administrativo).
    Usar esto para agregar usuarios ya que no hay registro público.
    
    Ejemplo:
        from auth import crear_usuario
        crear_usuario("juan@fertilab.com", "clave123", "Juan Pérez")
    """
    return register_user(email, password, nombre, empresa)

def listar_usuarios() -> list:
    """Lista todos los usuarios registrados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, nombre, empresa, created_at, last_login FROM users WHERE is_active = 1")
    users = cursor.fetchall()
    conn.close()
    return users

# =====================================================================
# USUARIO POR DEFECTO
# =====================================================================
# Email: admin@fertilab.com
# Contraseña: admin123
# 
# ⚠️ IMPORTANTE: Cambiar la contraseña después del primer login
# =====================================================================

# Inicializar DB al importar
init_db()