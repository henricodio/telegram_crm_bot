# Handler para el submenú de Gestión Ventas
from config import supabase_admin as supabase
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from states import SALE_SUBMENU as SALE_SUBMENU_STATE

SALE_SUBMENU = [
    ["Añadir Venta"],
    ["Consulta Venta"],
    ["Modificar Venta"],
    ["Eliminar Venta"],
    ["Volver Menú principal"]
]

async def mostrar_submenu_ventas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(SALE_SUBMENU, resize_keyboard=True)
    await update.message.reply_text(
        "Gestión de Ventas - Selecciona una opción:",
        reply_markup=keyboard
    )
    return SALE_SUBMENU_STATE

# Stubs para acciones de ventas
async def anadir_venta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Funcionalidad para añadir venta (pendiente de implementación)")
    return None

async def consulta_venta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Funcionalidad para consultar venta (pendiente de implementación)")
    return None

async def modificar_venta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Funcionalidad para modificar venta (pendiente de implementación)")
    return None

async def eliminar_venta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Funcionalidad para eliminar venta (pendiente de implementación)")
    return None
