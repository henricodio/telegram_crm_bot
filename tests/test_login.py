import pytest
import types
from unittest.mock import AsyncMock, patch, MagicMock
from telegram import Update
from telegram.ext import ContextTypes

# Importar la función a testear
from handlers import auth_handler

class DummyMessage:
    def __init__(self):
        self.replies = []
    async def reply_text(self, text, **kwargs):
        self.replies.append(text)

class DummyUpdate(Update):
    def __init__(self, text):
        super().__init__(update_id=12345, message=None)
        self.message = types.SimpleNamespace(text=text, reply_text=DummyMessage().reply_text)

class DummyContext:
    def __init__(self, args):
        self.args = args
        self.user_data = {}

@pytest.mark.asyncio
async def test_login_success():
    # Mock de respuesta Supabase
    mock_execute = MagicMock()
    mock_execute.data = [{"tenant_id": "tenant-abc", "username": "henrico"}]

    class MockSel:
        def eq(self, *args, **kwargs):
            return self
        def execute(self):
            return mock_execute
    mock_table = MagicMock(return_value=MockSel())

    with patch.object(auth_handler, "supabase") as mock_sb:
        mock_sb.table.return_value = MockSel()
        upd = DummyUpdate("/login henrico")
        ctx = DummyContext(["henrico"])
        await auth_handler.login(upd, ctx)
        assert ctx.user_data["tenant_id"] == "tenant-abc"

@pytest.mark.asyncio
async def test_login_fail():
    mock_execute = MagicMock()
    mock_execute.data = []
    class MockSel:
        def eq(self, *args, **kwargs):
            return self
        def execute(self):
            return mock_execute
    with patch.object(auth_handler, "supabase") as mock_sb:
        mock_sb.table.return_value = MockSel()
        upd = DummyUpdate("/login unknown")
        ctx = DummyContext(["unknown"])
        await auth_handler.login(upd, ctx)
        assert "tenant_id" not in ctx.user_data
