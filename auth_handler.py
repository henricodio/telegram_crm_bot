import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from config import supabase_admin, supabase_anon, TENANT_ID
from states import (REGISTER_USERNAME, REGISTER_EMAIL, REGISTER_PASSWORD, 
                    LOGIN_EMAIL, LOGIN_PASSWORD, SELECTING_ACTION)

logger = logging.getLogger(__name__)

# Aquí moveremos y crearemos las funciones de registro, login y reseteo de contraseña.
