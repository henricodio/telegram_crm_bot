# Punto de entrada principal del bot de Telegram.
# Código refactorizado para usar ConversationHandler, mejorando la gestión de estado y la legibilidad.
import logging
import os
from supabase import create_client, Client
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

# Se importan los handlers y la configuración
import config
from handlers import client_handler, product_handler, sale_handler, auth_handler, admin_handler, menu_handler
from handlers.auth_handler import (
    register_first_name, register_last_name, register_username, register_email, register_password, register_complete,
    login_email, login_password, login_complete,
    start_password_reset, request_reset_token, set_new_password, update_password_complete
)
from states import (
    SELECTING_ACTION,
    REGISTER_FIRST_NAME,
    REGISTER_LAST_NAME,
    REGISTER_USERNAME,
    REGISTER_EMAIL,
    SALE_SUBMENU_STATE,
    REGISTER_PASSWORD,
    LOGIN_EMAIL,
    LOGIN_PASSWORD,
    RESET_EMAIL,
    RESET_TOKEN,
    RESET_NEW_PASSWORD,
    CLIENT_SUBMENU,
    PRODUCT_SUBMENU,
    SALE_SUBMENU,
    CLIENT_FILTER_RESPONSE,
    PRODUCT_FILTER_RESPONSE,
    VIEWING_CLIENT,
    VIEWING_PRODUCT,
)
from config import supabase_admin

# --- Configuración de Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === FUNCIONES DEL MENÚ PRINCIPAL Y NAVEGACIÓN ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Función de inicio. Saluda al usuario y muestra el menú principal.
    Inicia la conversación.
    """
    user = update.effective_user
    tenant_id = context.user_data.get('tenant_id')
    
    # Si el usuario ya está autenticado, mostramos el menú principal
    if context.user_data.get('authenticated'):
        return await menu_handler.show_main_menu(update, context)
    
    # Si no está autenticado, mostramos el menú de inicio de sesión
    context.user_data.clear()
    if tenant_id:
        context.user_data['tenant_id'] = tenant_id

    texto = "¡Hola! 👋\n\nSoy tu asistente de gestión. Por favor, elige una opción para comenzar:"
    keyboard = [
        ["Registrarse", "Iniciar sesión"],
        ["Restablecer contraseña"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(texto, reply_markup=reply_markup)
    return SELECTING_ACTION

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cierra la sesión del usuario y finaliza la conversación."""
    context.user_data.clear()
    await update.message.reply_text(
        "Has cerrado la sesión. ¡Hasta pronto!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función genérica para finalizar cualquier conversación."""
    context.user_data.clear()
    await update.message.reply_text(
        "Acción cancelada. Volviendo al menú principal.",
        reply_markup=ReplyKeyboardRemove()
    )
    return await start(update, context)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja comandos o texto no reconocidos."""
    await update.message.reply_text(
        "Lo siento, no he entendido esa orden. Por favor, usa los botones del menú."
    )

# === Punto de entrada de la aplicación ===

def main():
    """Arranca el bot y registra los handlers principales."""
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # Compartir el cliente de Supabase con los handlers
    if supabase_admin:
        application.bot_data['supabase_client'] = supabase_admin
    else:
        logger.error("El bot no puede funcionar sin una conexión a Supabase. Saliendo.")
        return

    # --- Handlers de Conversación ---
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_ACTION: [
                MessageHandler(filters.Regex(r'^Registrarse$'), auth_handler.register_first_name),
                MessageHandler(filters.Regex(r'^Iniciar sesión$'), auth_handler.login_email),
                MessageHandler(filters.Regex(r'^Restablecer contraseña$'), auth_handler.start_password_reset),
                # Manejo del menú principal
                MessageHandler(filters.Regex(r'^👥 Gestión Clientes$'), client_handler.mostrar_submenu_clientes),
                MessageHandler(filters.Regex(r'^📦 Gestión Productos$'), product_handler.mostrar_submenu_productos),
                MessageHandler(filters.Regex(r'^💰 Gestión Ventas$'), sale_handler.mostrar_submenu_ventas),
                MessageHandler(filters.Regex(r'^⚙️ Configuración$'), menu_handler.show_main_menu),  # Temporal, implementar luego
            ],
            # Flujo de Registro
            REGISTER_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_first_name)],
            REGISTER_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_last_name)],
            REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
            # Flujo de Login
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
            # Flujo de reseteo de contraseña
            RESET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_reset_token)],
            RESET_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_password)],
            RESET_NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_password_complete)],
            # Submenús
            CLIENT_SUBMENU: [
                MessageHandler(filters.Regex(r'^Añadir Cliente$'), client_handler.anadir_cliente),
                MessageHandler(filters.Regex(r'^Consulta Cliente$'), client_handler.consulta_cliente),
                MessageHandler(filters.Regex(r'^Modificar Cliente$'), client_handler.modificar_cliente),
                MessageHandler(filters.Regex(r'^Eliminar Cliente$'), client_handler.eliminar_cliente),
            ],
            PRODUCT_SUBMENU: [
                MessageHandler(filters.Regex(r'^Añadir Producto$'), product_handler.anadir_producto),
                MessageHandler(filters.Regex(r'^Consulta Producto$'), product_handler.consulta_producto),
                MessageHandler(filters.Regex(r'^Modificar Producto$'), product_handler.modificar_producto),
                MessageHandler(filters.Regex(r'^Eliminar Producto$'), product_handler.eliminar_producto),
            ],
            SALE_SUBMENU_STATE: [
                MessageHandler(filters.Regex(r'^Añadir Venta$'), sale_handler.anadir_venta),
                MessageHandler(filters.Regex(r'^Consulta Venta$'), sale_handler.consulta_venta),
                MessageHandler(filters.Regex(r'^Modificar Venta$'), sale_handler.modificar_venta),
                MessageHandler(filters.Regex(r'^Eliminar Venta$'), sale_handler.eliminar_venta),
                MessageHandler(filters.Regex(r'^Volver Menú principal$'), menu_handler.show_main_menu),
            ],
            # Estados de respuesta
            CLIENT_FILTER_RESPONSE: [CallbackQueryHandler(client_handler.mostrar_clientes_filtrados)],
            PRODUCT_FILTER_RESPONSE: [
                 CallbackQueryHandler(product_handler.callback_filtro_producto, pattern='^product_filter_'),
                 CallbackQueryHandler(product_handler.mostrar_productos_filtrados, pattern='^product_value_'),
            ],
            VIEWING_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_handler.ver_detalle_producto)],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r'^🏠 Menú Principal$'), menu_handler.show_main_menu),
            MessageHandler(filters.Regex(r'^Volver al Menú Principal$'), menu_handler.show_main_menu),
            MessageHandler(filters.Regex(r'^Volver al Submenú de Clientes$'), client_handler.mostrar_submenu_clientes),
            MessageHandler(filters.Regex(r'^Volver al Submenú de Productos$'), product_handler.mostrar_submenu_productos),
            CommandHandler('cancel', end_conversation),
            MessageHandler(filters.Regex(r'^Cancelar$'), end_conversation),
            # Captura cualquier otro mensaje y lo redirige al menú principal
            MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler.handle_main_menu_selection),
        ],
        conversation_timeout=300
    )

    application.add_handler(conv_handler)
    
    # Handlers adicionales
    application.add_handler(CommandHandler("listusernames", admin_handler.list_usernames))
    application.add_handler(CommandHandler("testcrud", client_handler.test_crud_supabase_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_command))

    # --- Configuración y arranque del Webhook ---
    port = int(os.environ.get("PORT", 8443))
    webhook_url = f"{config.WEBHOOK_URL}/{config.TELEGRAM_TOKEN}"

    logger.info(f"Iniciando webhook en el puerto {port}")
    logger.info(f"URL del Webhook configurada: {webhook_url}")

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=config.TELEGRAM_TOKEN,
        webhook_url=webhook_url,
        secret_token=config.WEBHOOK_SECRET_TOKEN
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical("¡Error crítico en el bot!", exc_info=True)
