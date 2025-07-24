import pytest
from unittest.mock import patch, MagicMock
import types

from handlers import client_handler

class DummyMessage:
    def __init__(self):
        self.replies = []
    async def reply_text(self, text, **kwargs):
        self.replies.append(text)

class DummyUpdate:
    def __init__(self):
        self.message = types.SimpleNamespace(reply_text=DummyMessage().reply_text)

class DummyContext:
    def __init__(self, tenant=None):
        self.user_data = {}
        if tenant:
            self.user_data["tenant_id"] = tenant

@pytest.mark.asyncio
async def test_filter_requires_tenant():
    upd = DummyUpdate()
    ctx = DummyContext()  # sin tenant_id
    await client_handler.filtrar_por_route(upd, ctx)
    # Debería haber respondido con error
    assert ctx.user_data.get("filtro_cliente") is None
