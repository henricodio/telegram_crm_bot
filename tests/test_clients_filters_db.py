import pytest
import uuid
from config import supabase_admin as supabase

def setup_module(module):
    # Crear datos de prueba reutilizables
    global tenant_id, clientes
    tenant_id = str(uuid.uuid4())
    clientes = [
        {"client_name": "Cliente Uno", "city": "Madrid", "route": "Centro", "category": "A", "tenant_id": tenant_id},
        {"client_name": "Cliente Dos", "city": "Madrid", "route": "Norte", "category": "B", "tenant_id": tenant_id},
        {"client_name": "Cliente Tres", "city": "Barcelona", "route": "Centro", "category": "A", "tenant_id": tenant_id},
    ]
    # Insertar clientes
    response = supabase.table("companies").insert(clientes).execute()
    assert not getattr(response, 'error', None), f"Error insertando clientes: {response.error}"
    for i, c in enumerate(response.data):
        clientes[i]["id"] = c["id"]

def teardown_module(module):
    # Borrar todos los clientes de prueba
    ids = [c["id"] for c in clientes]
    supabase.table("companies").delete().in_("id", ids).execute()

def test_filtrar_por_ciudad():
    response = supabase.table("companies").select("*").eq("city", "Madrid").eq("tenant_id", tenant_id).execute()
    nombres = [c["client_name"] for c in response.data]
    assert set(nombres) == {"Cliente Uno", "Cliente Dos"}

def test_filtrar_por_ruta():
    response = supabase.table("companies").select("*").eq("route", "Centro").eq("tenant_id", tenant_id).execute()
    nombres = [c["client_name"] for c in response.data]
    assert set(nombres) == {"Cliente Uno", "Cliente Tres"}

def test_filtrar_por_categoria():
    response = supabase.table("companies").select("*").eq("category", "A").eq("tenant_id", tenant_id).execute()
    nombres = [c["client_name"] for c in response.data]
    assert set(nombres) == {"Cliente Uno", "Cliente Tres"}
