import logging
import os
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
from telegram.error import NetworkError, Forbidden

# --- Configuración de Logging Mejorada ---
log_level = logging.DEBUG if os.environ.get("DEBUG", "false").lower() == "true" else logging.INFO
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log_level,
    handlers=[logging.StreamHandler()]  # Envía logs a la salida estándar para que Render los capture
)
logger = logging.getLogger(__name__)

# Silenciar logs de librerías externas en producción
if log_level == logging.INFO:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# Se importan los handlers y la configuración
import config
from handlers import client_handler, product_handler, sale_handler, auth_handler, admin_handler
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

# === FUNCIONES DEL MENÚ PRINCIPAL Y NAVEGACIÓN ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Función de inicio. Saluda al usuario y muestra el menú principal.
    Inicia la conversación.
    """
    user = update.effective_user
    tenant_id = context.user_data.get('tenant_id')
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


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Endpoint de health check para Render."""
    await update.message.reply_text("Bot funcionando correctamente ✅")

# === Punto de entrada de la aplicación ===

def main() -> None:
    """Arranca el bot y registra los handlers principales."""
    if not config.supabase_admin:
        logger.critical("El cliente de Supabase no se pudo inicializar. Abortando.")
        return

    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    

    # Estados de la conversación y sus manejadores
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [
                MessageHandler(filters.Regex(r'^Registrarse$'), auth_handler.register_first_name),
                MessageHandler(filters.Regex(r'^Iniciar sesión$'), auth_handler.login_email),
                MessageHandler(filters.Regex(r'^Restablecer contraseña$'), auth_handler.start_password_reset),
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
            # Estados de respuesta
            CLIENT_FILTER_RESPONSE: [CallbackQueryHandler(client_handler.mostrar_clientes_filtrados)],
            PRODUCT_FILTER_RESPONSE: [
                CallbackQueryHandler(product_handler.callback_filtro_producto, pattern='^product_filter_'),
                CallbackQueryHandler(product_handler.mostrar_productos_filtrados, pattern='^product_value_'),
            ],
            VIEWING_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_handler.ver_detalle_producto)],
        },
        fallbacks=[
            CommandHandler('cancel', end_conversation),
            MessageHandler(filters.Regex(r'^Cancelar$'), end_conversation),
        ],
        conversation_timeout=600
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CommandHandler("listusernames", admin_handler.list_usernames))
    application.add_handler(CommandHandler("testcrud", client_handler.test_crud_supabase_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_command))
    application.add_error_handler(error_handler)

    port = int(os.environ.get("PORT", 8443))
    logger.info(f"Iniciando servidor webhook en el puerto {port}")

    # El método run_webhook es bloqueante y se encarga de configurar y arrancar el webhook
    url_path = "webhook"
    webhook_url = f"{config.WEBHOOK_URL}/{url_path}"

    logger.info(f"Configurando y iniciando webhook en la URL: {webhook_url}")

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=url_path,
        webhook_url=webhook_url,
        secret_token=config.WEBHOOK_SECRET_TOKEN,
        drop_pending_updates=True
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Loggea los errores y envía un mensaje al usuario."""
    logger.error("Excepción al manejar una actualización:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        text = "Ocurrió un error inesperado. Por favor, intenta de nuevo más tarde o contacta al administrador."
        if isinstance(context.error, NetworkError):
            text = "Error de red. Por favor, verifica tu conexión e intenta de nuevo."
        elif isinstance(context.error, Forbidden):
            logger.warning("El bot no está autorizado (Forbidden). Probablemente fue bloqueado por el usuario.")
            return
        await update.effective_message.reply_text(text)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("El bot se ha detenido correctamente.")
    except Exception as e:
        logger.critical(f"Error crítico al iniciar el bot: {e}", exc_info=True)
