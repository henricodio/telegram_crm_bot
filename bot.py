# Punto de entrada principal del bot de Telegram.
# Código refactorizado para usar ConversationHandler, mejorando la gestión de estado y la legibilidad.

import logging
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

# Se importan los handlers de los diferentes módulos
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

# --- Configuración de Logging ---
# Es una buena práctica configurar el logging al principio del script.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Inicialización de Clientes (Supabase) ---



# === FUNCIONES DEL MENÚ PRINCIPAL Y NAVEGACIÓN ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Función de inicio. Saluda al usuario y muestra el menú principal.
    Inicia la conversación.
    """
    user = update.effective_user
    # Limpia cualquier dato de conversaciones anteriores al iniciar, pero conserva tenant_id si existe.
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

# === Punto de entrada de la aplicación ===

def main():
    """Arranca el bot y registra los handlers principales."""
    
    # Se recomienda usar `Application.builder()` para más flexibilidad.
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # --- Handlers de Conversación ---
    auth_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_ACTION: [
                MessageHandler(filters.Regex(r'^Registrarse$'), register_first_name),
                MessageHandler(filters.Regex(r'^Iniciar sesión$'), login_email),
                MessageHandler(filters.Regex(r'^Restablecer contraseña$'), start_password_reset),
                MessageHandler(filters.Regex(r'^Gestión de Clientes$'), client_handler.mostrar_submenu_clientes),
                MessageHandler(filters.Regex(r'^Gestión de Productos$'), product_handler.mostrar_submenu_productos),
                MessageHandler(filters.Regex(r'^Gestión de Ventas$'), sale_handler.mostrar_submenu_ventas),
                MessageHandler(filters.Regex(r'^Cerrar Sesión$'), logout),
            ],
            # Flujo de Registro
            REGISTER_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_last_name)],
                REGISTER_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
                REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_complete)],
                # Reutilizamos el flujo de reseteo dentro del mismo ConversationHandler para el botón
                RESET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_reset_token)],
                RESET_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_password)],
                RESET_NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_password_complete)],
            # Flujo de Login
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_complete)],
            CLIENT_SUBMENU: [
                MessageHandler(filters.Regex(r'^Consulta Cliente$'), client_handler.consulta_cliente),
                MessageHandler(filters.Regex(r'^Filtrar por Ruta$'), client_handler.filtrar_por_route),
                MessageHandler(filters.Regex(r'^Filtrar por Categoría$'), client_handler.filtrar_por_category),
                MessageHandler(filters.Regex(r'^Filtrar por Ciudad$'), client_handler.filtrar_por_city),
                MessageHandler(filters.Regex(r'^Ver Ficha Completa$'), client_handler.ver_ficha_cliente),
                MessageHandler(filters.Regex(r'^Añadir Cliente$'), client_handler.anadir_cliente),
                MessageHandler(filters.Regex(r'^Eliminar Cliente$'), client_handler.eliminar_cliente),
                MessageHandler(filters.Regex(r'^Modificar Cliente$'), client_handler.modificar_cliente),
                # Flujo de modificación
                MessageHandler(filters.Regex(r'^(Nombre|Ciudad|Ruta|Categoría|Contacto|Teléfono|Dirección|Cancelar)$'), client_handler.recibir_campo_a_modificar),
                MessageHandler(filters.Regex(r'^(Sí|Si|sí|si|S|s|No|no|N|n)$'), client_handler.confirmar_modificacion_cliente),
                MessageHandler(filters.TEXT & ~filters.COMMAND, client_handler.recibir_nuevo_valor_campo),
                # Handler para los botones de confirmación de borrado (inline)
                CallbackQueryHandler(client_handler.confirmar_eliminar_cliente, pattern='^(confirmar|cancelar)_eliminar$'),
                # Captura todos los pasos del alta de cliente
                MessageHandler(filters.TEXT & ~filters.COMMAND, client_handler.recibir_dato_cliente),
                # Cuando se muestra una lista de clientes, se pasa al estado VIEWING_CLIENT
                # para que el siguiente mensaje de texto se interprete como la selección de uno de ellos.
                # (Nota: El flujo de alta de cliente tiene prioridad sobre selección de cliente)
                #MessageHandler(filters.TEXT & ~filters.COMMAND, client_handler.acciones_cliente_seleccionado),
            ],
            # Estado para esperar la selección de un cliente tras filtrar
            VIEWING_CLIENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, client_handler.acciones_cliente_seleccionado),
            ],
            # Submenú de Productos: esperando acción específica de productos
            PRODUCT_SUBMENU: [
                MessageHandler(filters.Regex(r'^Añadir Producto$'), product_handler.anadir_producto),
                MessageHandler(filters.Regex(r'^Consulta Producto$'), product_handler.consulta_producto),
                MessageHandler(filters.Regex(r'^Modificar Producto$'), product_handler.modificar_producto),
                MessageHandler(filters.Regex(r'^Eliminar Producto$'), product_handler.eliminar_producto),
                MessageHandler(filters.Regex(r'^Volver a la lista$'), product_handler.consulta_producto),
            ],
            # Estado para manejar la respuesta a un filtro de cliente (cuando se usan botones inline)
            CLIENT_FILTER_RESPONSE: [
                CallbackQueryHandler(client_handler.mostrar_clientes_filtrados)
            ],
            # Estado para manejar la respuesta a un filtro de producto
            PRODUCT_FILTER_RESPONSE: [
                 CallbackQueryHandler(product_handler.callback_filtro_producto, pattern='^product_filter_'),
                 CallbackQueryHandler(product_handler.mostrar_productos_filtrados, pattern='^product_value_'),
            ],
            # Estado para ver los detalles de un producto y decidir qué hacer
            VIEWING_PRODUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, product_handler.ver_detalle_producto)
            ],
        },
        fallbacks=[
            # Handlers para volver a menús anteriores o cancelar.
            MessageHandler(filters.Regex(r'^Volver al Menú Principal$'), start),
            MessageHandler(filters.Regex(r'^Volver al Submenú de Clientes$'), client_handler.mostrar_submenu_clientes),
            MessageHandler(filters.Regex(r'^Volver al Submenú de Productos$'), product_handler.mostrar_submenu_productos),
            CommandHandler('cancel', end_conversation),
            MessageHandler(filters.Regex(r'^Cancelar$'), end_conversation),
        ],
        # Si se quiere que la conversación termine tras un tiempo de inactividad
        conversation_timeout=300 # 5 minutos
    )

    # Handler para el reseteo de contraseña
    reset_password_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("resetpassword", start_password_reset)],
        states={
            RESET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_reset_token)],
            RESET_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_password)],
            RESET_NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_password_complete)],
        },
        fallbacks=[CommandHandler("cancel", end_conversation)],
        conversation_timeout=300
    )

    application.add_handler(auth_conv_handler)
    application.add_handler(reset_password_conv_handler)
    
    # --- Handlers Adicionales (fuera de la conversación principal) ---
    # Comandos de administración que no deben formar parte del flujo normal.
    application.add_handler(CommandHandler("listusernames", admin_handler.list_usernames))
    application.add_handler(CommandHandler("testcrud", client_handler.test_crud_supabase_handler))

    # Un handler de fallback para cualquier mensaje no capturado por la conversación.
    # Debe tener una prioridad más baja (número más alto).
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_command))

    # Iniciar el bot en modo webhook para Render
    import os
    WEBHOOK_URL = "https://telegram-crm-bot.onrender.com"  # Asegúrate que sea tu URL correcta
    port = int(os.environ.get("PORT", 10000))  # Cambiado a 10000 para coincidir con tus logs
    logger.info(f"Bot iniciado en webhook: {WEBHOOK_URL} (puerto {port})")
    application.run_webhook(
        listen="0.0.0.0",
    port=port,
    url_path=config.TELEGRAM_TOKEN,  # Añade esta línea
    webhook_url=f"{WEBHOOK_URL}/{config.TELEGRAM_TOKEN}",
    secret_token='TU_SECRET_TOKEN'
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical("¡Error crítico en el bot! El proceso se detuvo de forma inesperada.", exc_info=True)
        print(f"Error crítico: {e}")
