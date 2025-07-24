# Handler para el submenú de Gestión Clientes
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import asyncio

# Se importa la configuración y los estados desde los módulos correspondientes
from config import supabase_admin as supabase
from states import SELECTING_ACTION, CLIENT_SUBMENU, CLIENT_FILTER_RESPONSE, VIEWING_CLIENT, PRODUCT_FILTER_RESPONSE, PRODUCT_SUBMENU, SALE_SUBMENU

logger = logging.getLogger(__name__)

# --- Funciones Auxiliares ---

def limpiar_contexto(context: ContextTypes.DEFAULT_TYPE, keep_keys=('tenant_id',)) -> None:
    """Limpia context.user_data, manteniendo claves esenciales."""
    for key in list(context.user_data.keys()):
        if key not in keep_keys:
            context.user_data.pop(key)

# --- Handlers del Submenú de Clientes ---

async def mostrar_submenu_clientes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra el submenú de clientes y establece el estado correspondiente."""
    keyboard = [
        ["Consulta Cliente"],
        ["Filtrar por Ruta", "Filtrar por Categoría", "Filtrar por Ciudad"],
        ["Añadir Cliente", "Modificar Cliente", "Eliminar Cliente"], # Funciones a implementar
        ["Volver al Menú Principal"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Gestión de Clientes - Selecciona una opción:",
        reply_markup=reply_markup
    )
    return CLIENT_SUBMENU

async def consulta_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la opción 'Consulta Cliente', que ahora es un alias para el submenú."""
    # Esta función puede ser un punto de entrada para una búsqueda directa en el futuro.
    await update.message.reply_text("Por favor, elige un método de filtrado para encontrar al cliente.")
    return await mostrar_submenu_clientes(update, context)

# --- Lógica de Filtros ---

async def _filtrar_por_campo(update: Update, context: ContextTypes.DEFAULT_TYPE, campo: str) -> int:
    """Función genérica para filtrar clientes por un campo (route, category, city)."""
    tenant_id = context.user_data.get('tenant_id')
    if not tenant_id:
        await update.message.reply_text("Error: No estás autenticado. Por favor, inicia sesión.")
        return SELECTING_ACTION

    try:
        def consulta():
            return supabase.table("companies").select(campo).eq("tenant_id", tenant_id).execute()
        
        response = await asyncio.to_thread(consulta)
        valores = sorted({c[campo] for c in response.data if c.get(campo) and str(c[campo]).strip()})
        
        if not valores:
            await update.message.reply_text(f"No hay valores para '{campo}' registrados.")
            return CLIENT_SUBMENU

        keyboard = [[InlineKeyboardButton(str(v), callback_data=f"client_{campo}_{v}")] for v in valores]
        keyboard.append([InlineKeyboardButton("↩️ Volver", callback_data="client_back_submenu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        context.user_data['current_filter_type'] = campo
        await update.message.reply_text(f"Selecciona un valor para filtrar por {campo}:", reply_markup=reply_markup)
        return CLIENT_FILTER_RESPONSE

    except Exception as e:
        logger.error(f"Error al filtrar por {campo}: {e}")
        await update.message.reply_text("Ocurrió un error al recuperar los filtros.")
        return CLIENT_SUBMENU

async def filtrar_por_route(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _filtrar_por_campo(update, context, 'route')

async def filtrar_por_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _filtrar_por_campo(update, context, 'category')

async def filtrar_por_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _filtrar_por_campo(update, context, 'city')


async def mostrar_clientes_filtrados(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback que se activa al pulsar un botón de filtro inline."""
    query = update.callback_query
    await query.answer()
    
    # Manejar el botón de volver
    if query.data == "client_back_submenu":
        await query.edit_message_text("Volviendo al submenú de clientes...")
        # Necesitamos un update.message para enviar el siguiente menú con ReplyKeyboard
        if update.effective_message:
            # Corregido: pasar el objeto Update completo, no Message
            await mostrar_submenu_clientes(update, context)
        return CLIENT_SUBMENU

    try:
        _, campo, valor = query.data.split('_', 2)
    except ValueError:
        await query.edit_message_text("Error en el callback. Inténtalo de nuevo.")
        return CLIENT_SUBMENU

    tenant_id = context.user_data.get('tenant_id')
    if not tenant_id:
        await query.edit_message_text("Sesión expirada. Por favor, vuelve a iniciar sesión.")
        return SELECTING_ACTION

    try:
        def consulta():
            return supabase.table("companies").select("id, client_name, city").eq("tenant_id", tenant_id).eq(campo, valor).execute()
        
        response = await asyncio.to_thread(consulta)
        clientes = response.data

        if not clientes:
            await query.edit_message_text(f"No se encontraron clientes para {campo} = '{valor}'.")
            return CLIENT_SUBMENU

        limpiar_contexto(context)
        # Guardamos los clientes para el siguiente paso
        context.user_data['clientes_filtrados'] = {c['client_name']: c['id'] for c in clientes}

        keyboard = [[c['client_name']] for c in clientes]
        keyboard.append(["Volver al Submenú de Clientes"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await query.edit_message_text(f"Clientes encontrados para {campo} '{valor}'. Selecciona uno para ver sus acciones:")
        # Enviamos un nuevo mensaje porque no se puede cambiar de Inline a Reply keyboard
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Elige un cliente:", reply_markup=reply_markup)
        
        return VIEWING_CLIENT # Estado para esperar la selección del cliente

    except Exception as e:
        logger.error(f"Error al mostrar clientes filtrados: {e}")
        await query.edit_message_text("Ocurrió un error al obtener los clientes.")
        return CLIENT_SUBMENU


async def acciones_cliente_seleccionado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra las acciones disponibles para un cliente seleccionado."""
    texto = update.message.text
    clientes_filtrados = context.user_data.get('clientes_filtrados', {})

    # Manejo de botones de navegación
    if texto == "Volver al Submenú de Clientes":
        return await mostrar_submenu_clientes(update, context)
    if texto == "Volver al Menú Principal":
        from bot import start
        return await start(update, context)

    if texto not in clientes_filtrados:
        await update.message.reply_text("Por favor, selecciona un cliente de la lista.")
        return VIEWING_CLIENT

    cliente_id = clientes_filtrados[texto]
    context.user_data['cliente_seleccionado_id'] = cliente_id
    context.user_data['cliente_seleccionado_nombre'] = texto

    keyboard = [
        ["Ver Ficha Completa", "Crear Venta"],
        ["Modificar Cliente", "Eliminar Cliente"],
        ["Volver al Submenú de Clientes"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(f"Acciones para {texto}:", reply_markup=reply_markup)

    # Aquí se podría definir un nuevo estado, por ejemplo, ACTION_ON_CLIENT
    # Por ahora, lo devolvemos al submenú de clientes para simplificar.
    return CLIENT_SUBMENU


# --- Handler para ver ficha completa del cliente ---

# === FLUJO DE ELIMINAR CLIENTE ===

# === FLUJO DE MODIFICAR CLIENTE ===

async def modificar_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cliente_id = context.user_data.get('cliente_seleccionado_id')
    cliente_nombre = context.user_data.get('cliente_seleccionado_nombre', 'el cliente seleccionado')
    if not cliente_id:
        await update.message.reply_text("Primero selecciona un cliente para modificar.")
        return CLIENT_SUBMENU
    context.user_data['awaiting_mod_field'] = True
    keyboard = [["Nombre", "Ciudad"], ["Ruta", "Categoría"], ["Contacto", "Teléfono"], ["Dirección"], ["Cancelar"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        f"¿Qué campo deseas modificar de *{cliente_nombre}*?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CLIENT_SUBMENU

async def recibir_campo_a_modificar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('awaiting_mod_field'):
        return await mostrar_submenu_clientes(update, context)
    campo = update.message.text.strip().lower()
    campos_validos = {
        "nombre": "client_name",
        "ciudad": "city",
        "ruta": "route",
        "categoría": "category",
        "contacto": "contact_person",
        "teléfono": "phone",
        "dirección": "address"
    }
    if campo == "cancelar":
        context.user_data.pop('awaiting_mod_field', None)
        await update.message.reply_text("Modificación cancelada.")
        return await mostrar_submenu_clientes(update, context)
    if campo not in campos_validos:
        await update.message.reply_text("Campo no válido. Elige una opción del teclado.")
        return CLIENT_SUBMENU
    context.user_data['mod_field_name'] = campos_validos[campo]
    context.user_data['mod_field_label'] = campo
    context.user_data.pop('awaiting_mod_field', None)
    context.user_data['awaiting_mod_value'] = True
    await update.message.reply_text(f"Introduce el nuevo valor para *{campo}*:", parse_mode="Markdown")
    return CLIENT_SUBMENU

async def recibir_nuevo_valor_campo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('awaiting_mod_value'):
        return await mostrar_submenu_clientes(update, context)
    valor = update.message.text.strip()
    campo = context.user_data.get('mod_field_label')
    if valor.lower() in ["cancelar", "volver"]:
        context.user_data.pop('awaiting_mod_value', None)
        context.user_data.pop('mod_field_name', None)
        context.user_data.pop('mod_field_label', None)
        await update.message.reply_text("Modificación cancelada.")
        return await mostrar_submenu_clientes(update, context)
    # Validaciones básicas
    if campo == "teléfono" and not valor.isdigit():
        await update.message.reply_text("El teléfono debe ser numérico. Intenta de nuevo:")
        return CLIENT_SUBMENU
    if not valor:
        await update.message.reply_text("El valor no puede estar vacío. Intenta de nuevo:")
        return CLIENT_SUBMENU
    context.user_data['mod_field_value'] = valor
    context.user_data.pop('awaiting_mod_value', None)
    context.user_data['awaiting_mod_confirm'] = True
    await update.message.reply_text(
        f"¿Confirmas actualizar *{campo}* a: {valor}? (Sí/No)",
        parse_mode="Markdown"
    )
    return CLIENT_SUBMENU

async def confirmar_modificacion_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('awaiting_mod_confirm'):
        return await mostrar_submenu_clientes(update, context)
    value = update.message.text.strip().lower()
    if value in ["sí", "si", "s"]:
        cliente_id = context.user_data.get('cliente_seleccionado_id')
        field = context.user_data.get('mod_field_name')
        nuevo_valor = context.user_data.get('mod_field_value')
        def actualiza():
            return supabase.table("companies").update({field: nuevo_valor}).eq("id", cliente_id).execute()
        response = await asyncio.to_thread(actualiza)
        if getattr(response, 'error', None):
            await update.message.reply_text(f"Error al modificar el cliente: {response.error}")
        else:
            await update.message.reply_text("✅ Cliente modificado correctamente.")
        # Limpiar contexto
        context.user_data.pop('awaiting_mod_confirm', None)
        context.user_data.pop('mod_field_name', None)
        context.user_data.pop('mod_field_label', None)
        context.user_data.pop('mod_field_value', None)
        return await mostrar_submenu_clientes(update, context)
    else:
        await update.message.reply_text("Modificación cancelada. No se cambió ningún dato.")
        context.user_data.pop('awaiting_mod_confirm', None)
        context.user_data.pop('mod_field_name', None)
        context.user_data.pop('mod_field_label', None)
        context.user_data.pop('mod_field_value', None)
        return await mostrar_submenu_clientes(update, context)


async def eliminar_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cliente_id = context.user_data.get('cliente_seleccionado_id')
    cliente_nombre = context.user_data.get('cliente_seleccionado_nombre', 'el cliente seleccionado')
    if not cliente_id:
        await update.message.reply_text("Primero selecciona un cliente para eliminar.")
        return CLIENT_SUBMENU

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_eliminar"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_eliminar"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⚠️ ¿Estás seguro de que deseas eliminar a *{cliente_nombre}*? Esta acción no se puede deshacer.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return CLIENT_SUBMENU

async def confirmar_eliminar_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "confirmar_eliminar":
        client_id = context.user_data.get('cliente_seleccionado_id')
        tenant_id = context.user_data.get('tenant_id')

        # --- LOGS DE DEPURACIÓN ---
        logger.info(f"Intentando eliminar cliente. ID: {client_id}, Tenant ID: {tenant_id}")

        if not client_id or not tenant_id:
            logger.error("Error: client_id o tenant_id no encontrados en el contexto para la eliminación.")
            await query.edit_message_text("Error: No se pudo identificar al cliente. Operación cancelada.")
            return await mostrar_submenu_clientes(update, context)

        def elimina():
            return supabase.table("companies").delete().eq("id", client_id).eq("tenant_id", tenant_id).execute()

        response = await asyncio.to_thread(elimina)

        # --- LOGS DE DEPURACIÓN ---
        logger.info(f"Respuesta de Supabase al eliminar: {response}")

        if getattr(response, 'error', None):
            await query.edit_message_text(f"Error al eliminar el cliente: {response.error}")
        elif not response.data:
            await query.edit_message_text("El cliente no pudo ser eliminado. Verifique los permisos o si el cliente aún existe.")
        else:
            await query.edit_message_text("✅ Cliente eliminado correctamente.")

        # Limpiar contexto y volver
        context.user_data.pop('cliente_seleccionado_id', None)
        return await mostrar_submenu_clientes(update, context)

    elif query.data == "cancelar_eliminar":
        await query.edit_message_text("Eliminación cancelada.")
        return await mostrar_submenu_clientes(update, context)

    return CLIENT_SUBMENU


# === TEST CRUD SUPABASE (solo para depuración interna) ===

async def test_crud_supabase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from handlers.admin_handler import ADMIN_IDS
    user_id = update.effective_user.id
    if str(user_id) not in ADMIN_IDS:
        await update.message.reply_text("No tienes permisos para ejecutar este comando.")
        return
    await update.message.reply_text("Iniciando test CRUD sobre Supabase (tabla companies)...")
    try:
        import io
        import sys
        log = io.StringIO()
        sys_stdout = sys.stdout
        sys.stdout = log
        await test_crud_companies()
        sys.stdout = sys_stdout
        log_value = log.getvalue()
        await update.message.reply_text(f"Resultado del test CRUD:\n\n{log_value}")
    except Exception as e:
        await update.message.reply_text(f"Error al ejecutar el test CRUD: {e}")


async def test_crud_companies():
    import uuid
    print("--- INICIANDO TEST CRUD COMPANIES ---")
    tenant_id = "1b42cbd4-cb32-4890-80d3-f4bed3141ee7"  # Ajusta si es necesario
    nombre = f"Test Cliente {uuid.uuid4().hex[:6]}"
    # CREATE
    def crea():
        return supabase.table("companies").insert({
            "client_name": nombre,
            "city": "TestCity",
            "route": "TestRoute",
            "category": "TestCat",
            "contact_person": "TestContact",
            "phone": "123456789",
            "address": "TestAddress",
            "tenant_id": tenant_id
        }).execute()
    resp_create = await asyncio.to_thread(crea)
    print("CREATE:", resp_create.data)
    if not resp_create.data:
        print("ERROR EN CREATE")
        return
    company_id = resp_create.data[0]["id"]
    # READ
    def lee():
        return supabase.table("companies").select("*").eq("id", company_id).eq("tenant_id", tenant_id).single().execute()
    resp_read = await asyncio.to_thread(lee)
    print("READ:", resp_read.data)
    # UPDATE
    def actualiza():
        return supabase.table("companies")\
            .update({"city": "CiudadActualizada"})\
            .eq("id", company_id)\
            .eq("tenant_id", tenant_id)\
            .execute()
    resp_update = await asyncio.to_thread(actualiza)
    print("UPDATE:", resp_update.data)
    # DELETE
    def elimina():
        return supabase.table("companies")\
            .delete()\
            .eq("id", company_id)\
            .eq("tenant_id", tenant_id)\
            .execute()
    resp_delete = await asyncio.to_thread(elimina)
    print("DELETE:", resp_delete.data)
    print("--- FIN TEST CRUD ---")

# === FLUJO DE ALTA DE CLIENTE ===

async def anadir_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['nuevo_cliente'] = {}
    await update.message.reply_text("Introduce el *nombre* del cliente:", parse_mode="Markdown")
    context.user_data['awaiting_field'] = 'nombre'
    return CLIENT_SUBMENU

async def recibir_dato_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    field = context.user_data.get('awaiting_field')
    value = update.message.text.strip()
    if value.lower() in ["cancelar", "volver"]:
        context.user_data.pop('nuevo_cliente', None)
        context.user_data.pop('awaiting_field', None)
        await update.message.reply_text("Alta de cliente cancelada.")
        return await mostrar_submenu_clientes(update, context)
    if field == 'nombre':
        if not value:
            await update.message.reply_text("El nombre no puede estar vacío. Intenta de nuevo:")
            return CLIENT_SUBMENU
        context.user_data['nuevo_cliente']['client_name'] = value
        context.user_data['awaiting_field'] = 'ciudad'
        await update.message.reply_text("Introduce la *ciudad* del cliente:", parse_mode="Markdown")
        return CLIENT_SUBMENU
    if field == 'ciudad':
        if not value:
            await update.message.reply_text("La ciudad no puede estar vacía. Intenta de nuevo:")
            return CLIENT_SUBMENU
        context.user_data['nuevo_cliente']['city'] = value
        context.user_data['awaiting_field'] = 'ruta'
        await update.message.reply_text("Introduce la *ruta* del cliente:", parse_mode="Markdown")
        return CLIENT_SUBMENU
    if field == 'ruta':
        if not value:
            await update.message.reply_text("La ruta no puede estar vacía. Intenta de nuevo:")
            return CLIENT_SUBMENU
        context.user_data['nuevo_cliente']['route'] = value
        context.user_data['awaiting_field'] = 'categoría'
        await update.message.reply_text("Introduce la *categoría* del cliente:", parse_mode="Markdown")
        return CLIENT_SUBMENU
    if field == 'categoría':
        if not value:
            await update.message.reply_text("La categoría no puede estar vacía. Intenta de nuevo:")
            return CLIENT_SUBMENU
        context.user_data['nuevo_cliente']['category'] = value
        context.user_data['awaiting_field'] = 'contacto'
        await update.message.reply_text("Introduce la *persona de contacto* del cliente:", parse_mode="Markdown")
        return CLIENT_SUBMENU
    if field == 'contacto':
        if not value:
            await update.message.reply_text("El contacto no puede estar vacío. Intenta de nuevo:")
            return CLIENT_SUBMENU
        context.user_data['nuevo_cliente']['contact_person'] = value
        context.user_data['awaiting_field'] = 'teléfono'
        await update.message.reply_text("Introduce el *teléfono* del cliente:", parse_mode="Markdown")
        return CLIENT_SUBMENU
    if field == 'teléfono':
        if not value.isdigit():
            await update.message.reply_text("El teléfono debe ser numérico. Intenta de nuevo:")
            return CLIENT_SUBMENU
        context.user_data['nuevo_cliente']['phone'] = value
        context.user_data['awaiting_field'] = 'dirección'
        await update.message.reply_text("Introduce la *dirección* del cliente:", parse_mode="Markdown")
        return CLIENT_SUBMENU
    if field == 'dirección':
        if not value:
            await update.message.reply_text("La dirección no puede estar vacía. Intenta de nuevo:")
            return CLIENT_SUBMENU
        context.user_data['nuevo_cliente']['address'] = value
        # Confirmación
        cliente = context.user_data['nuevo_cliente']
        resumen = f"""*Resumen del nuevo cliente:*
Nombre: {cliente['client_name']}
Ciudad: {cliente['city']}
Ruta: {cliente['route']}
Categoría: {cliente['category']}
Contacto: {cliente['contact_person']}
Teléfono: {cliente['phone']}
Dirección: {cliente['address']}

¿Confirmar alta? (Sí/No)"""
        context.user_data['awaiting_field'] = 'confirmacion'
        await update.message.reply_text(resumen, parse_mode="Markdown")
        return CLIENT_SUBMENU
    if field == 'confirmacion':
        if value.lower() in ['sí', 'si', 's']:
            cliente = context.user_data['nuevo_cliente']
            cliente['tenant_id'] = context.user_data.get('tenant_id')
            def inserta():
                return supabase.table("companies").insert(cliente).execute()
            response = await asyncio.to_thread(inserta)
            if getattr(response, 'error', None):
                await update.message.reply_text(f"Error al guardar el cliente: {response.error}")
                context.user_data.pop('nuevo_cliente', None)
                context.user_data.pop('awaiting_field', None)
                return await mostrar_submenu_clientes(update, context)
            await update.message.reply_text("✅ Cliente añadido correctamente.")
        else:
            await update.message.reply_text("Alta cancelada. No se guardó ningún cliente.")
        context.user_data.pop('nuevo_cliente', None)
        context.user_data.pop('awaiting_field', None)
        return await mostrar_submenu_clientes(update, context)
    # Si por algún motivo se pierde el estado
    await update.message.reply_text("Error en el flujo. Volviendo al submenú de clientes.")
    context.user_data.pop('nuevo_cliente', None)
    context.user_data.pop('awaiting_field', None)
    return await mostrar_submenu_clientes(update, context)


async def ver_ficha_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cliente_id = context.user_data.get('cliente_seleccionado_id')
    if not cliente_id:
        await update.message.reply_text("No hay cliente seleccionado.")
        return CLIENT_SUBMENU
    def consulta():
        return supabase.table("companies").select("*").eq("id", cliente_id).single().execute()
    response = await asyncio.to_thread(consulta)
    cliente = response.data
    if not cliente:
        await update.message.reply_text("No se encontró la ficha del cliente.")
        return CLIENT_SUBMENU
    ficha = f"📄 *Ficha del Cliente*\n\n"
    ficha += f"Nombre: {cliente.get('client_name', '-')}\n"
    ficha += f"Ciudad: {cliente.get('city', '-')}\n"
    ficha += f"Ruta: {cliente.get('route', '-')}\n"
    ficha += f"Categoría: {cliente.get('category', '-')}\n"
    ficha += f"Contacto: {cliente.get('contact_person', '-')}\n"
    ficha += f"Teléfono: {cliente.get('phone', '-')}\n"
    ficha += f"Dirección: {cliente.get('address', '-')}\n"
    keyboard = [
        ["Volver al Submenú de Clientes"],
        ["Volver al Menú Principal"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(ficha, parse_mode="Markdown", reply_markup=reply_markup)
    return CLIENT_SUBMENU

async def mostrar_submenu_clientes(update, context):
    texto = "Gestión de Clientes - Selecciona una opción:"
    keyboard = [
        ["Filtrar por Ciudad", "Filtrar por Ruta", "Filtrar por Categoría"],
        ["Ver Todos los Clientes"],
        ["Volver al Menú Principal"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    # Determina el chat_id de forma segura
    chat_id = update.effective_chat.id

    # Si la función fue llamada desde un botón inline, primero eliminamos el mensaje anterior
    # para evitar confusión y luego enviamos el nuevo menú.
    if update.callback_query:
        await update.callback_query.answer()
        # Opcional: editar el mensaje para quitar los botones y evitar que se queden "colgados"
        try:
            await update.callback_query.edit_message_text(text="Volviendo al submenú de clientes...")
        except Exception as e:
            logger.info(f"No se pudo editar el mensaje, probablemente ya fue borrado: {e}")

    await context.bot.send_message(chat_id, texto, reply_markup=reply_markup)

    return CLIENT_SUBMENU

# --- Implementaciones pendientes ---
