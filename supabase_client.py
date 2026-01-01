import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # <-- ESTA ES LA CORRECCIÓN

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ ERROR: Faltan las credenciales de Supabase en las variables de entorno")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
