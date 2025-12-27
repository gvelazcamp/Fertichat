# ====================================
# CONEXIÓN A SUPABASE PARA CHATBOT (SEGURO)
# ====================================

# 1. INSTALACIÓN
# pip install supabase python-dotenv

import os
from supabase import create_client, Client
from datetime import datetime
from typing import Optional, List, Dict
from dotenv import load_dotenv

# 2. CARGAR VARIABLES DE ENTORNO
load_dotenv()

# 3. CONFIGURACIÓN (desde variables de entorno)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Validar que existan las credenciales
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ ERROR: Falta SUPABASE_URL o SUPABASE_ANON_KEY en el archivo .env")

# Crear cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("✅ Conexión a Supabase establecida correctamente")

# ====================================
# CLASE PARA GESTIONAR CHATBOT
# ====================================

class ChatbotSupabase:
    def __init__(self):
        self.supabase = supabase
    
    def guardar_mensaje(self, user_id: str, mensaje: str, es_bot: bool = False) -> Optional[Dict]:
        """Guardar mensaje en la base de datos"""
        try:
            data = self.supabase.table('mensajes').insert({
                'user_id': user_id,
                'mensaje': mensaje,
                'es_bot': es_bot,
                'timestamp': datetime.now().isoformat()
            }).execute()
            
            print(f"✅ Mensaje guardado")
            return data.data
        except Exception as e:
            print(f"❌ Error al guardar mensaje: {e}")
            return None
    
    def obtener_historial(self, user_id: str, limite: int = 50) -> List[Dict]:
        """Obtener historial de conversación"""
        try:
            response = self.supabase.table('mensajes')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('timestamp', desc=True)\
                .limit(limite)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener historial: {e}")
            return []
    
    def gestionar_usuario(self, user_id: str, nombre: str, **kwargs) -> Optional[Dict]:
        """Crear o actualizar usuario"""
        try:
            datos_usuario = {
                'id': user_id,
                'nombre': nombre,
                'ultimo_acceso': datetime.now().isoformat(),
                **kwargs
            }
            
            data = self.supabase.table('usuarios').upsert(datos_usuario).execute()
            print(f"✅ Usuario gestionado")
            return data.data
        except Exception as e:
            print(f"❌ Error al gestionar usuario: {e}")
            return None
    
    def guardar_contexto(self, user_id: str, contexto: Dict) -> Optional[Dict]:
        """Guardar contexto de la conversación"""
        try:
            data = self.supabase.table('contextos').upsert({
                'user_id': user_id,
                'contexto': contexto,
                'actualizado': datetime.now().isoformat()
            }).execute()
            
            return data.data
        except Exception as e:
            print(f"❌ Error al guardar contexto: {e}")
            return None
    
    def obtener_contexto(self, user_id: str) -> Optional[Dict]:
        """Obtener contexto de la conversación"""
        try:
            response = self.supabase.table('contextos')\
                .select('contexto')\
                .eq('user_id', user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0].get('contexto')
            return None
        except Exception as e:
            print(f"❌ Error al obtener contexto: {e}")
            return None
    
    def buscar_en_base_datos(self, query: str) -> List[Dict]:
        """Buscar en base de conocimiento"""
        try:
            response = self.supabase.table('conocimiento')\
                .select('*')\
                .text_search('contenido', query)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            return []
    
    def eliminar_historial(self, user_id: str) -> bool:
        """Eliminar historial de un usuario"""
        try:
            self.supabase.table('mensajes')\
                .delete()\
                .eq('user_id', user_id)\
                .execute()
            
            print(f"✅ Historial eliminado para usuario {user_id}")
            return True
        except Exception as e:
            print(f"❌ Error al eliminar historial: {e}")
            return False

# ====================================
# EJEMPLO DE USO
# ====================================

def ejemplo_uso():
    print("\n🤖 Iniciando ejemplo de uso...\n")
    
    # Crear instancia del chatbot
    chatbot = ChatbotSupabase()
    
    user_id = f"user_{int(datetime.now().timestamp())}"
    
    # 1. Registrar usuario
    print("1️⃣ Registrando usuario...")
    chatbot.gestionar_usuario(
        user_id, 
        "Usuario Demo",
        email="demo@example.com"
    )
    
    # 2. Guardar mensaje del usuario
    print("2️⃣ Guardando mensajes...")
    chatbot.guardar_mensaje(user_id, "¿Cuál es el horario de atención?", False)
    
    # 3. Guardar respuesta del bot
    chatbot.guardar_mensaje(user_id, "Nuestro horario es de 9am a 6pm", True)
    
    # 4. Obtener historial
    print("3️⃣ Obteniendo historial...")
    historial = chatbot.obtener_historial(user_id, 10)
    print(f"📝 Historial: {historial}")
    
    # 5. Guardar contexto
    print("4️⃣ Guardando contexto...")
    chatbot.guardar_contexto(user_id, {
        "tema": "horarios",
        "intencion": "consulta"
    })
    
    # 6. Recuperar contexto
    print("5️⃣ Recuperando contexto...")
    contexto = chatbot.obtener_contexto(user_id)
    print(f"📌 Contexto: {contexto}")
    
    print("\n✨ Ejemplo completado!\n")

# ====================================
# EJEMPLO CON FLASK (API REST)
# ====================================

"""
# Instalar: pip install flask

from flask import Flask, request, jsonify

app = Flask(__name__)
chatbot = ChatbotSupabase()

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    user_id = data.get('user_id')
    mensaje = data.get('mensaje')
    
    # Guardar mensaje del usuario
    chatbot.guardar_mensaje(user_id, mensaje, False)
    
    # Tu lógica del chatbot aquí
    respuesta = "Gracias por tu mensaje"
    
    # Guardar respuesta del bot
    chatbot.guardar_mensaje(user_id, respuesta, True)
    
    return jsonify({'respuesta': respuesta})

@app.route('/historial/<user_id>', methods=['GET'])
def obtener_historial_endpoint(user_id):
    historial = chatbot.obtener_historial(user_id)
    return jsonify({'historial': historial})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
"""

if __name__ == "__main__":
    # Descomentar para probar:
    ejemplo_uso()
