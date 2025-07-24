# Definición de estados para las conversaciones
# Usar constantes en un archivo separado evita importaciones circulares.

# Estados globales para ConversationHandler
# Añade aquí todos los estados relevantes para navegación, registro y login
(
    SELECTING_ACTION,       # Menú principal: elegir entre login, registro, gestión, etc.
    REGISTER_FIRST_NAME,    # Registro: esperando nombre
    REGISTER_LAST_NAME,     # Registro: esperando apellido
    REGISTER_USERNAME,      # Registro: esperando username
    REGISTER_EMAIL,         # Registro: esperando email
    REGISTER_PASSWORD,      # Registro: esperando contraseña
    LOGIN_EMAIL,            # Login: esperando email
    LOGIN_PASSWORD,         # Login: esperando contraseña

    # Flujo de reseteo de contraseña
    RESET_EMAIL,            # Reseteo: esperando email
    RESET_TOKEN,            # Reseteo: esperando token
    RESET_NEW_PASSWORD,     # Reseteo: esperando nueva contraseña

    CLIENT_SUBMENU,         # Submenú clientes
    PRODUCT_SUBMENU,        # Submenú productos
    SALE_SUBMENU,           # Submenú ventas
    CLIENT_FILTER_RESPONSE, # Respuesta filtro clientes
    PRODUCT_FILTER_RESPONSE,# Respuesta filtro productos
    VIEWING_CLIENT,         # Viendo ficha cliente
    VIEWING_PRODUCT         # Viendo ficha producto
) = range(18)
