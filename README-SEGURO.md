# 🔐 Chatbot con Supabase - VERSIÓN SEGURA

Integración de chatbot con Supabase usando **variables de entorno** para proteger tus credenciales.

---

## 🚨 IMPORTANTE - SEGURIDAD

### ✅ Qué incluye esta versión:
- ✅ Credenciales en archivo `.env` (NO se suben a GitHub)
- ✅ Archivo `.gitignore` configurado
- ✅ Plantilla `.env.example` para compartir
- ✅ Código actualizado para leer variables de entorno

### ❌ Nunca hagas esto:
- ❌ NO subas el archivo `.env` a GitHub
- ❌ NO compartas tus credenciales en código público
- ❌ NO hagas commit del archivo `.env`

---

## 📦 Instalación

### Para JavaScript/Node.js

```bash
# 1. Instalar dependencias
npm install

# 2. Crear archivo .env con tus credenciales
cp .env.example .env

# 3. Editar .env con tus datos reales
# (Ya viene configurado con tus credenciales)
```

### Para Python

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear archivo .env con tus credenciales
cp .env.example .env

# 3. Editar .env con tus datos reales
# (Ya viene configurado con tus credenciales)
```

---

## 🗄️ Configurar Base de Datos

### 1. Ejecutar el SQL en Supabase

1. Ve a tu proyecto: https://supabase.com/dashboard
2. Abre **SQL Editor** (menú lateral)
3. Copia y pega el contenido de `supabase-schema.sql`
4. Haz clic en **RUN**
5. Verifica que las tablas se crearon correctamente

### 2. Verificar Tablas Creadas

Las tablas que deben existir:
- ✅ `usuarios`
- ✅ `mensajes`
- ✅ `contextos`
- ✅ `conocimiento`

---

## 💻 Uso del Código

### JavaScript/Node.js

```javascript
// Importar funciones
const { 
  guardarMensaje, 
  obtenerHistorial, 
  gestionarUsuario 
} = require('./chatbot-supabase-seguro.js');

// Usar las funciones
async function main() {
  const userId = 'user123';
  
  // Registrar usuario
  await gestionarUsuario(userId, 'Juan Pérez', { 
    email: 'juan@example.com' 
  });
  
  // Guardar conversación
  await guardarMensaje(userId, '¿Cuál es tu horario?', false);
  await guardarMensaje(userId, 'De 9am a 6pm', true);
  
  // Ver historial
  const historial = await obtenerHistorial(userId);
  console.log(historial);
}

main();
```

### Python

```python
from chatbot_supabase_seguro import ChatbotSupabase

# Crear instancia
chatbot = ChatbotSupabase()

# Usar las funciones
user_id = 'user123'

# Registrar usuario
chatbot.gestionar_usuario(user_id, 'Juan Pérez', email='juan@example.com')

# Guardar conversación
chatbot.guardar_mensaje(user_id, '¿Cuál es tu horario?', False)
chatbot.guardar_mensaje(user_id, 'De 9am a 6pm', True)

# Ver historial
historial = chatbot.obtener_historial(user_id)
print(historial)
```

---

## 🔌 Integraciones

### WhatsApp (JavaScript)

```javascript
const { Client } = require('whatsapp-web.js');
const { guardarMensaje, gestionarUsuario } = require('./chatbot-supabase-seguro.js');

const client = new Client();

client.on('message', async msg => {
  const userId = msg.from;
  
  // Registrar usuario si es nuevo
  await gestionarUsuario(userId, msg._data.notifyName || 'Usuario');
  
  // Guardar mensaje del usuario
  await guardarMensaje(userId, msg.body, false);
  
  // Tu lógica de respuesta aquí
  const respuesta = "¡Hola! ¿En qué puedo ayudarte?";
  
  // Guardar respuesta del bot
  await guardarMensaje(userId, respuesta, true);
  
  msg.reply(respuesta);
});

client.initialize();
```

### Telegram (Python)

```python
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from chatbot_supabase_seguro import ChatbotSupabase

chatbot = ChatbotSupabase()

async def handle_message(update: Update, context):
    user_id = str(update.effective_user.id)
    mensaje = update.message.text
    
    # Registrar usuario
    chatbot.gestionar_usuario(
        user_id, 
        update.effective_user.first_name
    )
    
    # Guardar mensaje
    chatbot.guardar_mensaje(user_id, mensaje, False)
    
    # Tu lógica aquí
    respuesta = "¡Hola! ¿Cómo puedo ayudarte?"
    
    # Guardar respuesta
    chatbot.guardar_mensaje(user_id, respuesta, True)
    
    await update.message.reply_text(respuesta)

# Configurar bot
app = Application.builder().token("TU_TOKEN_AQUI").build()
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.run_polling()
```

### API REST con Flask

```python
from flask import Flask, request, jsonify
from chatbot_supabase_seguro import ChatbotSupabase

app = Flask(__name__)
chatbot = ChatbotSupabase()

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    user_id = data.get('user_id')
    mensaje = data.get('mensaje')
    
    # Guardar mensaje
    chatbot.guardar_mensaje(user_id, mensaje, False)
    
    # Procesar respuesta
    respuesta = "Gracias por tu mensaje"
    
    # Guardar respuesta
    chatbot.guardar_mensaje(user_id, respuesta, True)
    
    return jsonify({'respuesta': respuesta})

if __name__ == '__main__':
    app.run(port=5000)
```

---

## 📁 Estructura de Archivos

```
tu-proyecto/
│
├── .env                          # ⚠️ CREDENCIALES (NO subir a GitHub)
├── .env.example                  # ✅ Plantilla sin credenciales
├── .gitignore                    # ✅ Protege archivos sensibles
│
├── chatbot-supabase-seguro.js    # Código JavaScript
├── chatbot-supabase-seguro.py    # Código Python
│
├── package.json                  # Dependencias Node.js
├── requirements.txt              # Dependencias Python
│
├── supabase-schema.sql           # Estructura de la BD
└── README.md                     # Esta guía
```

---

## 🔒 Seguridad - Checklist

Antes de compartir o subir tu código:

- [ ] ✅ Archivo `.env` está en `.gitignore`
- [ ] ✅ NO hay credenciales hardcodeadas en el código
- [ ] ✅ Archivo `.env.example` no contiene credenciales reales
- [ ] ✅ Has hecho commit del `.gitignore`
- [ ] ✅ Verificaste que `.env` no esté en tu repositorio

### Verificar si .env está en git:

```bash
# Ver archivos trackeados
git ls-files | grep .env

# Si aparece .env, eliminarlo del historial:
git rm --cached .env
git commit -m "Remove .env from tracking"
```

---

## 🌐 Despliegue

### Variables de entorno en producción:

#### Heroku
```bash
heroku config:set SUPABASE_URL=https://ytmpjhdjecocoitptvjn.supabase.co
heroku config:set SUPABASE_ANON_KEY=tu_key_aqui
```

#### Vercel
```bash
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
```

#### Netlify
Agregar en: **Site settings > Build & deploy > Environment variables**

#### Railway / Render
Agregar en la sección de **Environment Variables** del dashboard

---

## 🆘 Solución de Problemas

### Error: "Falta SUPABASE_URL o SUPABASE_ANON_KEY"

**Solución:**
1. Verifica que existe el archivo `.env`
2. Verifica que `.env` tiene las variables correctas
3. En Node.js, verifica que instalaste `dotenv`
4. En Python, verifica que instalaste `python-dotenv`

### Error: "relation does not exist"

**Solución:**
1. Ejecuta el archivo `supabase-schema.sql` en Supabase
2. Verifica que las tablas existen en el **Table Editor**

### Las variables de entorno no se cargan

**JavaScript:**
```javascript
// Al inicio del archivo
require('dotenv').config();
console.log(process.env.SUPABASE_URL); // Debe mostrar la URL
```

**Python:**
```python
from dotenv import load_dotenv
load_dotenv()
print(os.getenv("SUPABASE_URL"))  # Debe mostrar la URL
```

---

## 📚 Recursos

- [Documentación Supabase](https://supabase.com/docs)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript)
- [Variables de entorno en Node.js](https://www.npmjs.com/package/dotenv)
- [Variables de entorno en Python](https://pypi.org/project/python-dotenv/)

---

## 🎯 Próximos Pasos

1. ✅ Verifica que `.env` está en `.gitignore`
2. ✅ Ejecuta el SQL en Supabase
3. ✅ Instala las dependencias
4. ✅ Prueba el código de ejemplo
5. ✅ Integra con tu plataforma de chatbot

---

## 🔐 Recuerda

> **Nunca compartas tu archivo `.env`**  
> **Nunca hagas commit de credenciales**  
> **Usa siempre `.gitignore`**

---

¡Tu chatbot está listo y **seguro**! 🎉🔒
