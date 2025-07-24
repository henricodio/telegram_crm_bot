"""Script CLI para listar usernames almacenados en la tabla users.
Uso:
    python tools/list_usernames.py [prefijo]

Requiere variables de entorno SUPABASE_URL y SUPABASE_KEY o un archivo .env.
"""

import sys
from typing import List
from pathlib import Path
import os
from dotenv import load_dotenv
from supabase import create_client

# Cargar .env si existe
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / ".env")  # tipo: ignore[arg-type]

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    sys.exit("ERROR: SUPABASE_URL o SUPABASE_KEY no definidas.")

prefix = sys.argv[1] if len(sys.argv) > 1 else None

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

sel = supabase.table("users").select("username")
if prefix:
    sel = sel.ilike("username", f"{prefix}%")

response = sel.execute()
usernames: List[str] = [u["username"] for u in response.data if u.get("username")]

if not usernames:
    print("No se encontraron usernames.")
else:
    for name in usernames:
        print(name)
