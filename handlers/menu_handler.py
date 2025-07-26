from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from states import CLIENT_SUBMENU, PRODUCT_SUBMENU, SALE_SUBMENU
import logging

logger = logging.getLogger(__name__)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal con las opciones disponibles."""
    keyboard = [
        ["👥 Gestión Clientes"],
        ["📦 Gestión Productos", "💰 Gestión Ventas"],
        ["⚙️ Configuración"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    if update.message:
        await update.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)
    
    return "SELECTING_ACTION"

async def handle_main_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección del menú principal y redirige al submenú correspondiente."""
    text = update.message.text.lower()
    
    if "clientes" in text:
        from handlers.client_handler import mostrar_submenu_clientes
        return await mostrar_submenu_clientes(update, context)
    elif "productos" in text:
        from handlers.product_handler import mostrar_submenu_productos
        return await mostrar_submenu_productos(update, context)
    elif "ventas" in text:
        from handlers.sale_handler import mostrar_submenu_ventas
        return await mostrar_submenu_ventas(update, context)
    elif "configuración" in text or "configuracion" in text:
        await update.message.reply_text("🔧 Configuración (en desarrollo)")
        return "SELECTING_ACTION"
    else:
        await update.message.reply_text("Opción no reconocida. Por favor, usa los botones del menú.")
        return "SELECTING_ACTION"
