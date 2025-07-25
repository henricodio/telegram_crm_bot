import pytest
import uuid
from config import supabase_admin as supabase

def test_crud_client():
    # 1. Crear cliente
    tenant_id = str(uuid.uuid4())
    cliente = {
        "client_name": "Test Cliente",
        "city": "Test City",
        "route": "Test Route",
        "category": "Test Category",
        "contact_person": "Tester",
        "phone": "123456789",
        "address": "Test Address",
        "tenant_id": tenant_id
    }
    response = supabase.table("companies").insert(cliente).execute()
    assert not getattr(response, 'error', None), f"Error insertando cliente: {response.error}"
    cliente_id = response.data[0]["id"]

    # 2. Leer cliente
    response = supabase.table("companies").select("*").eq("id", cliente_id).single().execute()
    assert response.data["client_name"] == "Test Cliente"
    assert response.data["tenant_id"] == tenant_id

    # 3. Modificar cliente
    response = supabase.table("companies").update({"client_name": "Cliente Modificado"}).eq("id", cliente_id).execute()
    assert not getattr(response, 'error', None), f"Error modificando cliente: {response.error}"

    response = supabase.table("companies").select("*").eq("id", cliente_id).single().execute()
    assert response.data["client_name"] == "Cliente Modificado"

    # 4. Eliminar cliente
    response = supabase.table("companies").delete().eq("id", cliente_id).execute()
    assert not getattr(response, 'error', None), f"Error eliminando cliente: {response.error}"

    # 5. Confirmar eliminación
    response = supabase.table("companies").select("*").eq("id", cliente_id).execute()
    assert not response.data, "El cliente no fue eliminado correctamente"