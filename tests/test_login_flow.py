import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message
from telegram.ext import ContextTypes

from handlers import auth_handler
from states import LOGIN_EMAIL, LOGIN_PASSWORD, SELECTING_ACTION

@pytest.mark.asyncio
async def test_login_flow_email_then_password(monkeypatch):
    # Simula el update con el email
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.text = "testuser@example.com"
    context = MagicMock()
    context.user_data = {}

    # Llama al handler que pide el email
    next_state = await auth_handler.login_password(update, context)
    assert next_state == LOGIN_PASSWORD
    assert context.user_data["login_email"] == "testuser@example.com"

    # Simula el update con la contraseña
    update.message.text = "supersecret"
    # Mock de la respuesta de supabase.auth.sign_in_with_password
    class DummySession:
        access_token = "abc"
        user = MagicMock()
        user.id = "user-uuid"
    dummy_session_response = MagicMock()
    dummy_session_response.session = DummySession()
    monkeypatch.setattr(auth_handler.supabase.auth, "sign_in_with_password", lambda creds: dummy_session_response)
    # Mock de la consulta a la tabla users
    dummy_user_details = MagicMock()
    dummy_user_details.data = {"tenant_id": "tenant-123", "username": "henrico"}
    execute_mock = MagicMock(return_value=dummy_user_details)
    single_mock = MagicMock(return_value=MagicMock(execute=execute_mock))
    eq_mock = MagicMock(return_value=MagicMock(single=single_mock))
    select_mock = MagicMock(return_value=MagicMock(eq=eq_mock))
    table_mock = MagicMock(select=select_mock)
    monkeypatch.setattr(auth_handler.supabase, "table", lambda name: table_mock)

    # Llama al handler que procesa la contraseña
    next_state = await auth_handler.login_complete(update, context)
    assert next_state == SELECTING_ACTION
    assert context.user_data["tenant_id"] == "tenant-123"
