from telegram import Update
from telegram.ext import ContextTypes
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from config import supabase_admin, supabase_anon, TENANT_ID
from states import (
    SELECTING_ACTION, REGISTER_FIRST_NAME, REGISTER_LAST_NAME, REGISTER_USERNAME, REGISTER_EMAIL, REGISTER_PASSWORD,
    LOGIN_EMAIL, LOGIN_PASSWORD, RESET_EMAIL, RESET_TOKEN, RESET_NEW_PASSWORD
)
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'

# === REGISTRO ===
async def register_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pregunta el nombre."""
    await update.message.reply_text("Registro: ¿Cuál es tu nombre?")
    return REGISTER_FIRST_NAME

async def register_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guarda nombre y pregunta apellido."""
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("¿Y tu apellido?")
    return REGISTER_LAST_NAME
async def register_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Guarda el apellido y pregunta username
    context.user_data['last_name'] = update.message.text
    await update.message.reply_text("Elige un nombre de usuario:")
    return REGISTER_USERNAME

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Guarda el username y pide email
    context.user_data['register_username'] = update.message.text
    await update.message.reply_text("Introduce tu email:")
    return REGISTER_EMAIL

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['register_email'] = update.message.text
    await update.message.reply_text("Elige una contraseña:")
    return REGISTER_PASSWORD

async def register_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    username = context.user_data.get('register_username')
    email = context.user_data.get('register_email')

    try:
        # PASO 1: Crear usuario en Supabase Auth (solo credenciales)
        # Se elimina el user_metadata para evitar activar triggers complejos.
        user_response = supabase_admin.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True # Lo activamos para que el flujo sea más seguro
        })
        
        auth_user = user_response.user
        if not auth_user:
            raise Exception("Supabase no devolvió un usuario después de la creación.")

        # PASO 2: Insertar el perfil en la tabla public.users manualmente
        # Ahora que tenemos un auth_user_id válido, creamos el perfil.
        insert_response = supabase_admin.table("users").insert({
            "id": auth_user.id,  # Usamos el mismo UUID para ambas tablas
            "auth_user_id": auth_user.id,
            "username": username,
            "first_name": context.user_data.get('first_name'),
            "last_name": context.user_data.get('last_name'),
            "tenant_id": TENANT_ID
        }).execute()

        await update.message.reply_text(
            "✅ ¡Registro casi completo! Te hemos enviado un email de confirmación. "
            "Por favor, haz clic en el enlace para activar tu cuenta y luego inicia sesión."
        )
        return SELECTING_ACTION

    except Exception as e:
        # Si el error contiene 'already been registered', damos un mensaje más claro.
        if 'already been registered' in str(e):
            error_message = "Este email ya ha sido registrado. Si eres tú, puedes iniciar sesión o usar /resetpassword."
            logger.warning(f"Intento de registro con email duplicado: {email}")
        else:
            error_message = f"Error en el registro: {e}"
            logger.error(f"Registro fallido para {email}: {e}")
        
        await update.message.reply_text(error_message)
        return REGISTER_USERNAME

# === LOGIN ===
async def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # MODO DESARROLLO: saltar login y entrar al menú principal
    await update.message.reply_text("🔓 Acceso directo habilitado para desarrollo. ¡Bienvenido al menú principal!")
    # Simulamos un login exitoso
    context.user_data['authenticated'] = True
    # Establecer un tenant_id de prueba para desarrollo
    context.user_data['tenant_id'] = '1b42cbd4-cb32-4890-80d3-f4bed3141ee7'  # Usando el mismo que en .env
    # Mostramos el menú principal
    from handlers.menu_handler import show_main_menu
    return await show_main_menu(update, context)

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['login_email'] = update.message.text
    await update.message.reply_text("Introduce tu contraseña:")
    return LOGIN_PASSWORD

async def login_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = context.user_data.get('login_email')
    password = update.message.text
    try:
        session_response = supabase_anon.auth.sign_in_with_password({"email": email, "password": password})
        session = session_response.session
        if not session:
            raise Exception("La sesión no pudo ser creada.")
        # Usar el token de la sesión para las siguientes llamadas
        client = supabase_anon
        client.postgrest.auth(session.access_token)
        user_id = session.user.id

        # Actualizar la fecha de último login
        supabase_admin.table("users").update({
            "last_login": datetime.now().isoformat()
        }).eq("auth_user_id", user_id).execute()

        # Obtener detalles del usuario para la sesión del bot
        user_details = client.table("users").select("tenant_id, username").eq("auth_user_id", user_id).single().execute()
        if not user_details.data:
            raise Exception("No se encontraron detalles del usuario en la tabla public.users.")
        context.user_data['tenant_id'] = user_details.data['tenant_id']
        username = user_details.data.get('username', email)
        await update.message.reply_text(f"✅ ¡Sesión iniciada correctamente para {username}!")
        logger.info(f"Login exitoso para el usuario con tenant_id: {user_details.data['tenant_id']}")
        return SELECTING_ACTION
    except Exception as e:
        logger.error(f"Login fallido para {email}: {e}")
        await update.message.reply_text(f"Error de autenticación. Verifica tus credenciales. Detalles: {e}")
        return LOGIN_EMAIL

# === RECUPERACIÓN DE CONTRASEÑA ===

async def start_password_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el flujo de recuperación de contraseña pidiendo el email."""
    await update.message.reply_text(
        "Por favor, introduce el email de la cuenta que quieres recuperar.",
        reply_markup=ReplyKeyboardRemove()
    )
    return RESET_EMAIL

async def request_reset_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el email, solicita el reseteo a Supabase y pide el token al usuario."""
    email = update.message.text
    context.user_data['reset_email'] = email
    try:
        # Solicitar a Supabase que envíe el email de reseteo
        supabase_anon.auth.reset_password_for_email(email)
        
        await update.message.reply_text(
            "Te hemos enviado un email con un enlace de recuperación. "
            "Por favor, copia y pega la URL completa aquí."
        )
        return RESET_TOKEN
    except Exception as e:
        logger.error(f"Error al solicitar reseteo para {email}: {e}")
        await update.message.reply_text("Hubo un error al procesar tu solicitud. Por favor, inténtalo de nuevo.")
        return ConversationHandler.END

async def set_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el token (URL), extrae el access_token y pide la nueva contraseña."""
    recovery_url = update.message.text
    try:
        # Extraer el access_token de la URL (viene en el fragmento #)
        fragment = recovery_url.split('#')[1]
        params = dict(item.split('=') for item in fragment.split('&'))
        access_token = params.get('access_token')
        refresh_token = params.get('refresh_token') # También guardamos el refresh token

        if not access_token:
            raise KeyError("El token de acceso no se encontró en la URL.")
        
        context.user_data['reset_access_token'] = access_token
        context.user_data['reset_refresh_token'] = refresh_token
        await update.message.reply_text("Gracias. Ahora, por favor, introduce tu nueva contraseña.")
        return RESET_NEW_PASSWORD
    except (IndexError, KeyError):
        await update.message.reply_text("La URL que pegaste no parece válida. Por favor, inténtalo de nuevo o cancela con /cancel.")
        return RESET_TOKEN

async def update_password_complete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe la nueva contraseña y la actualiza en Supabase usando el token."""
    new_password = update.message.text
    access_token = context.user_data.get('reset_access_token')

    if not access_token:
        await update.message.reply_text("Ha ocurrido un error, no se encontró el token de sesión. Inicia el proceso de nuevo con /resetpassword.")
        return ConversationHandler.END

    try:
        # 1. Iniciar sesión con el token para obtener una sesión válida
        session_response = supabase_anon.auth.set_session(access_token, context.user_data.get('reset_refresh_token', ''))
        if not session_response.user:
            raise Exception("No se pudo validar la sesión con el token proporcionado.")

        # 2. Actualizar la contraseña del usuario autenticado
        user_attributes = {"password": new_password}
        supabase_anon.auth.update_user(user_attributes)
        
        await update.message.reply_text("¡Tu contraseña ha sido actualizada con éxito! Ya puedes iniciar sesión.")
        
    except Exception as e:
        logger.error(f"Error al actualizar la contraseña: {e}")
        await update.message.reply_text("Hubo un error al actualizar tu contraseña. Por favor, intenta el proceso de nuevo con /resetpassword.")
        
    finally:
        context.user_data.clear()
        return ConversationHandler.END
