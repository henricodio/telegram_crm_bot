# Manejadores para comandos generales o flujos adicionales del bot.

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

MENU_OPTIONS = [
    ["Gestión Clientes"],
    ["Gestión Productos"],
    ["Gestión Ventas"]
]

def mostrar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal al usuario con opciones."""
    keyboard = ReplyKeyboardMarkup(MENU_OPTIONS, resize_keyboard=True)
    update.message.reply_text(
        "Bienvenido a FAKTO CRM\nSelecciona un área de gestión:",
        reply_markup=keyboard
    )
