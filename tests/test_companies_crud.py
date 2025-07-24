import os
import pytest
from supabase import create_client, Client
import uuid

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

@pytest.fixture(scope="module")
def supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def test_crud_companies(supabase):
    # --- CREATE ---
    test_id = str(uuid.uuid4())
    data = {
        "id": test_id,
        "client_name": "Test Cliente CRUD",
        "address": "Calle Test 123",
        "phone": "123456789",
        "route": "Test Route",
        "city": "Test City",
        "contact_person": "Tester",
        "tenant_id": "00000000-0000-0000-0000-000000000001",
    }
    insert_resp = supabase.table("companies").insert(data).execute()
    assert insert_resp.status_code in (200, 201)
    
    # --- READ ---
    read_resp = supabase.table("companies").select("*").eq("id", test_id).execute()
    assert read_resp.status_code == 200
    assert len(read_resp.data) == 1
    assert read_resp.data[0]["client_name"] == "Test Cliente CRUD"
    
    # --- UPDATE ---
    update_resp = supabase.table("companies").update({"client_name": "Cliente CRUD Modificado"}).eq("id", test_id).execute()
    assert update_resp.status_code == 200
    
    # --- READ UPDATED ---
    read_updated = supabase.table("companies").select("*").eq("id", test_id).execute()
    assert read_updated.data[0]["client_name"] == "Cliente CRUD Modificado"
    
    # --- DELETE ---
    delete_resp = supabase.table("companies").delete().eq("id", test_id).execute()
    assert delete_resp.status_code == 200
    
    # --- VERIFY DELETE ---
    read_deleted = supabase.table("companies").select("*").eq("id", test_id).execute()
    assert len(read_deleted.data) == 0
