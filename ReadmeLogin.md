# 🌱 Ferti Chat - Sistema de Gestión de Compras

## 📦 Archivos incluidos

| Archivo | Descripción |
|---------|-------------|
| `main.py` | Aplicación principal de Streamlit |
| `auth.py` | Módulo de autenticación |
| `login_page.py` | Página de login con estilos |
| `sql_queries.py` | Consultas a la base de datos |
| `intent_detector.py` | Detección de intenciones con IA |
| `config.py` | Configuración (ya lo tenés) |

---

## 🚀 Instalación

### 1. Copiá todos los archivos a tu carpeta del proyecto

### 2. Instalá las dependencias (si no las tenés):
```bash
pip install streamlit pandas openai plotly openpyxl
```

### 3. Ejecutá la aplicación:
```bash
streamlit run main.py
```

---

## 🔐 Sistema de Autenticación

### Primera vez:
1. Abrí la aplicación en el navegador
2. Vas a ver la pantalla de **Ferti Chat - Iniciar Sesión**
3. Hacé click en la pestaña **"📝 Registrarse"**
4. Completá el formulario con tu email y contraseña
5. Una vez registrado, iniciá sesión en **"🔐 Ingresar"**

### Cambiar contraseña:
1. En la pantalla de login, hacé click en **"🔑 Cambiar clave"**
2. Ingresá tu email, contraseña actual y nueva contraseña

### Base de datos de usuarios:
- Se crea automáticamente un archivo `users.db` (SQLite)
- Las contraseñas se guardan hasheadas (SHA-256 con salt)
- Podés ver los usuarios registrados abriendo `users.db` con cualquier visor de SQLite

---

## 🎨 Personalización

### Colores
Los colores del login están en `login_page.py`:
- Fondo: degradado azul `#1e3a5f → #3d7ab5`
- Botón: naranja/coral `#f97316 → #ea580c`
- Texto: azul oscuro `#1e3a5f`

### Logo
Podés cambiar el emoji 🌱 por tu logo en `login_page.py`:
```python
def show_logo():
    st.markdown("""
        <span class="logo-icon">🌱</span>  <!-- Cambiá acá -->
        <h1 class="logo-text">Ferti Chat</h1>
    """)
```

---

## 📱 Estructura de la app

```
┌─────────────────────────────────────┐
│  🌱 Ferti Chat - Iniciar Sesión     │
│                                     │
│  [📧 Email]                         │
│  [🔒 Contraseña]                    │
│                                     │
│  [     Ingresar     ]               │
│                                     │
│  Tabs: Ingresar | Registrarse | ... │
└─────────────────────────────────────┘
           ↓ (después de login)
┌─────────────────────────────────────┐
│ Sidebar:      │  Contenido:         │
│ 🌱 Ferti Chat │                     │
│ 👤 Usuario    │  🛒 Compras IA      │
│ 🏢 Empresa    │  📦 Stock IA        │
│ [Cerrar sesión]│  🔎 Buscador IA    │
└─────────────────────────────────────┘
```

---

## ⚠️ Notas importantes

1. **No borres `users.db`** - contiene los usuarios registrados
2. **Para resetear usuarios**, borrá `users.db` y se creará vacío
3. **El sistema es para producción** - las contraseñas están hasheadas

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'auth'"
- Asegurate de tener `auth.py` y `login_page.py` en la misma carpeta que `main.py`

### "La página se recarga infinitamente"
- Borrá el caché: `streamlit cache clear`
- Reiniciá el navegador

### "No puedo iniciar sesión"
- Verificá que el email esté escrito correctamente (minúsculas)
- La contraseña es case-sensitive

---

## 📞 Soporte

¿Problemas? Revisá el archivo `NO_TOCAR.md` en la carpeta `BACKUP_ESTABLE_27DIC/`

🌱 **Ferti Chat © 2024**
