import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message

from handlers import auth_handler
from states import REGISTER_USERNAME, REGISTER_EMAIL, REGISTER_PASSWORD, SELECTING_ACTION

@pytest.mark.asyncio
async def test_register_flow_username_email_password(monkeypatch):
    # Simula el update con el username
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.text = "henrico"
    context = MagicMock()
    context.user_data = {}

    # Handler pide username
    next_state = await auth_handler.register_email(update, context)
    assert next_state == REGISTER_EMAIL
    assert context.user_data["register_username"] == "henrico"

    # Simula el update con el email
    update.message.text = "henrico@example.com"
    next_state = await auth_handler.register_password(update, context)
    assert next_state == REGISTER_PASSWORD
    assert context.user_data["register_email"] == "henrico@example.com"

    # Simula el update con la contraseña
    update.message.text = "supersecret"
    # Mock de la creación de usuario en Supabase Auth
    dummy_auth_user = MagicMock()
    dummy_auth_user.id = "user-uuid"
    dummy_user_response = MagicMock()
    dummy_user_response.user = dummy_auth_user
    monkeypatch.setattr(auth_handler.supabase.auth.admin, "create_user", lambda data: dummy_user_response)
    # Mock de la inserción en la tabla users
    insert_mock = MagicMock(return_value=MagicMock())
    table_mock = MagicMock(insert=insert_mock)
    monkeypatch.setattr(auth_handler.supabase, "table", lambda name: table_mock)

    # Handler de registro completo
    next_state = await auth_handler.register_complete(update, context)
    assert next_state == SELECTING_ACTION
