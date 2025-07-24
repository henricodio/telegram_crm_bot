# Handler para el submenú de Gestión Productos
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import supabase_admin as supabase
# Importar los estados desde states.py para mantener consistencia
from states import (
    SELECTING_ACTION,
    PRODUCT_SUBMENU,
    PRODUCT_FILTER_RESPONSE,
    VIEWING_PRODUCT
)

PRODUCT_KEYBOARD = [
    ["Añadir Producto", "Consulta Producto"],
    ["Volver al Menú Principal"]
]

# Opciones de filtro para productos
PRODUCT_FILTER_OPTIONS = {
    "sku": "Código/SKU",
    "category": "Categoría",
    "supplier_id": "Proveedor",
    "stock": "Disponibilidad"
}

async def mostrar_submenu_productos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra el submenú de gestión de productos."""
    keyboard = ReplyKeyboardMarkup(PRODUCT_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Gestión de Productos - Selecciona una opción:",
        reply_markup=keyboard
    )
    return PRODUCT_SUBMENU

async def anadir_producto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Flujo de alta de producto solicitando SKU obligatorio."""
    context.user_data['producto'] = {}
    await update.message.reply_text("Introduce el código o SKU numérico del producto:")
    context.user_data['awaiting_sku'] = True
    return PRODUCT_SUBMENU

# Añadir en el handler principal (bot.py) la gestión de estados para esperar el SKU y luego los demás campos.
# Aquí solo el fragmento relevante del handler:

async def recibir_sku(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sku = update.message.text.strip()
    if not sku.isdigit():
        await update.message.reply_text("El SKU debe ser un número. Inténtalo de nuevo:")
        return PRODUCT_SUBMENU
    context.user_data['producto']['sku'] = int(sku)
    context.user_data.pop('awaiting_sku', None)
    await update.message.reply_text("Introduce el nombre del producto:")
    context.user_data['awaiting_name'] = True
    return PRODUCT_SUBMENU

# El resto del flujo de alta debe seguir pidiendo los campos requeridos y finalmente insertar en Supabase:
# supabase.table("products").insert({ ...context.user_data['producto'], ...otros_campos }).execute()

# NOTA: Este fragmento debe integrarse con el ConversationHandler principal para el flujo completo.


async def consulta_producto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra las opciones de filtro para los productos."""
    buttons = [
        [InlineKeyboardButton(text, callback_data=f"product_filter_{key}")]
        for key, text in PRODUCT_FILTER_OPTIONS.items()
    ]
    buttons.append([InlineKeyboardButton("Cancelar", callback_data="cancel_filter")])
    
    keyboard = InlineKeyboardMarkup(buttons)
    
    await update.message.reply_text(
        "¿Cómo quieres filtrar los productos?",
        reply_markup=keyboard
    )
    return PRODUCT_FILTER_RESPONSE

async def callback_filtro_producto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la selección de un filtro de producto desde un InlineKeyboard."""
    query = update.callback_query
    await query.answer()

    filter_type = query.data.replace("product_filter_", "")

    if filter_type == "stock":
        buttons = [
            [InlineKeyboardButton("Con stock", callback_data="product_value_stock_true")],
            [InlineKeyboardButton("Sin stock", callback_data="product_value_stock_false")]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Selecciona la disponibilidad:", reply_markup=keyboard)
        return PRODUCT_FILTER_RESPONSE

    try:
        response = supabase.table("products").select(filter_type).execute()
        if response.data:
            items = sorted({str(p[filter_type]) for p in response.data if p.get(filter_type) and str(p[filter_type]).strip()})
            buttons = [
                [InlineKeyboardButton(item, callback_data=f"product_value_{filter_type}_{item}")]
                for item in items
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            await query.edit_message_text(f"Selecciona una opción para {PRODUCT_FILTER_OPTIONS[filter_type]}:", reply_markup=keyboard)
            return PRODUCT_FILTER_RESPONSE
        else:
            await query.edit_message_text("No se encontraron opciones para este filtro.")
            return await mostrar_submenu_productos(update, context)
    except Exception as e:
        print(f"Error al obtener filtros de productos: {e}")
        await query.edit_message_text("Error al consultar las opciones de filtro.")
        return await mostrar_submenu_productos(update, context)

async def mostrar_productos_filtrados(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra los productos que coinciden con el filtro seleccionado."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    filter_type = parts[2]
    filter_value = "_".join(parts[3:])

    try:
        if filter_type == 'stock':
            filter_value_bool = filter_value == 'true'
            if filter_value_bool:
                response = supabase.table("products").select("*").gt('stock', 0).execute()
            else:
                response = supabase.table("products").select("*").eq('stock', 0).execute()
        else:
            response = supabase.table("products").select("*").eq(filter_type, filter_value).execute()

        if response.data:
            context.user_data['filtered_products'] = response.data
            message = "Productos encontrados:\n\n"
            for i, product in enumerate(response.data):
                message += f"{i + 1}. [SKU: {product.get('sku','-')}] {product['name']} (Stock: {product['stock']})\n"
            
            message += "\nSelecciona un número para ver detalles o escribe 'cancelar'."
            await query.edit_message_text(message)
            return VIEWING_PRODUCT
        else:
            await query.edit_message_text("No se encontraron productos con ese criterio.")
            return await mostrar_submenu_productos(update, context)

    except Exception as e:
        print(f"Error al mostrar productos filtrados: {e}")
        await query.edit_message_text("Ocurrió un error al buscar los productos.")
        return await mostrar_submenu_productos(update, context)

async def ver_detalle_producto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra los detalles de un producto seleccionado y las acciones disponibles."""
    selected_index_str = update.message.text
    if not selected_index_str.isdigit():
        await update.message.reply_text("Por favor, introduce un número válido.")
        return VIEWING_PRODUCT

    selected_index = int(selected_index_str) - 1
    filtered_products = context.user_data.get('filtered_products', [])

    if 0 <= selected_index < len(filtered_products):
        product = filtered_products[selected_index]
        context.user_data['selected_product_id'] = product['id']

        message = f"*Detalles del Producto*\n\n"
        message += f"*SKU:* {product.get('sku', 'N/A')}\n"
        message += f"*Nombre:* {product.get('name', 'N/A')}\n"
        message += f"*Descripción:* {product.get('description', 'N/A')}\n"
        message += f"*Categoría:* {product.get('category', 'N/A')}\n"
        message += f"*Precio:* ${product.get('price', 0):.2f}\n"
        message += f"*Stock:* {product.get('stock', 0)}\n"
        
        keyboard = [
            ["Modificar Producto", "Eliminar Producto"],
            ["Volver a la lista"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        if product.get('image_url'):
            await update.message.reply_photo(
                photo=product['image_url'],
                caption=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        return PRODUCT_SUBMENU # Estado para esperar acción sobre el producto
    else:
        await update.message.reply_text("Selección no válida. Inténtalo de nuevo.")
        return VIEWING_PRODUCT

async def modificar_producto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Placeholder para la función de modificar un producto."""
    await update.message.reply_text("Funcionalidad para modificar producto (pendiente de implementación).")
    return await mostrar_submenu_productos(update, context)

async def eliminar_producto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Placeholder para la función de eliminar un producto."""
    await update.message.reply_text("Funcionalidad para eliminar producto (pendiente de implementación).")
    return await mostrar_submenu_productos(update, context)
