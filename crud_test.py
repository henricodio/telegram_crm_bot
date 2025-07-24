import uuid
from datetime import datetime
from config import supabase_admin, TENANT_ID


def main():
    # Generar IDs únicos para no interferir con auth.users reales
    fake_id = str(uuid.uuid4())
    email = f"test_{fake_id[:8]}@mail.com"
    username = f"test_{fake_id[:8]}"

    print("\n➜ CREATE …")
    create_resp = supabase_admin.table("users").insert({
        "id": fake_id,
        "auth_user_id": fake_id,
        "username": username,
        "tenant_id": TENANT_ID,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    print(create_resp)

    print("\n➜ READ …")
    read_resp = supabase_admin.table("users").select("*").eq("id", fake_id).single().execute()
    print(read_resp.data)

    print("\n➜ UPDATE …")
    new_username = username + "_upd"
    update_resp = supabase_admin.table("users").update({"username": new_username}).eq("id", fake_id).execute()
    print(update_resp.data)

    print("\n➜ DELETE …")
    delete_resp = supabase_admin.table("users").delete().eq("id", fake_id).execute()
    print(delete_resp.data)

    print("\n✅ CRUD test completado sin errores.")


if __name__ == "__main__":
    main()
