# Configuración global del proyecto: tokens, constantes, variables de entorno, etc.

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno desde .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

TENANT_ID = os.getenv("TENANT_ID", "00000000-0000-0000-0000-000000000001")

# Carga la lista de IDs de administradores desde el entorno
ADMIN_IDS = set()
_admin_env = os.getenv("ADMIN_IDS", "").strip()
if _admin_env:
    try:
        ADMIN_IDS = {int(x) for x in _admin_env.split(',') if x.strip()}
    except ValueError:
        logger.warning("La variable ADMIN_IDS contiene valores no válidos.")

# Inicializa el cliente de Supabase para que sea importable desde otros módulos
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
supabase_anon: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
