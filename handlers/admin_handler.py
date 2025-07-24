"""Handlers administrativos para el bot (solo uso interno).
Actualmente incluye /listusernames para depuración/administración.
"""

from telegram import Update
from telegram.ext import ContextTypes
import os
import logging
from config import supabase_admin as supabase, ADMIN_IDS

logger = logging.getLogger(__name__)

async def list_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía una lista de usernames disponibles. Solo admins."""
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("Comando exclusivo para administradores.")
        return

    prefix = context.args[0] if context.args else None

    def consulta():
        sel = supabase.table("users").select("username")
        if prefix:
            sel = sel.ilike("username", f"{prefix}%")
        return sel.execute()

    import asyncio
    response = await asyncio.to_thread(consulta)
    usernames = [u["username"] for u in response.data if u.get("username")]
    if not usernames:
        await update.message.reply_text("No se encontraron usernames.")
        return

    chunks = [usernames[i:i+50] for i in range(0, len(usernames), 50)]
    for ch in chunks:
        await update.message.reply_text("\n".join(ch))
