import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno
load_dotenv(dotenv_path='../.env')

# Configuración de Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def seed_invoices():
    """Inserta 3 facturas de ejemplo con sus líneas de detalle."""
    try:
        print("Iniciando la inserción de datos de facturación...")

        # 1. Obtener datos existentes para consistencia
        print("Obteniendo clientes y productos existentes...")
        companies_resp = supabase.table("companies").select("id").execute()
        products_resp = supabase.table("products").select("id, price").execute()

        if not companies_resp.data or not products_resp.data:
            print("Error: No hay suficientes datos de clientes o productos para crear facturas.")
            return

        company_ids = [c['id'] for c in companies_resp.data]
        products = products_resp.data

        # 2. Crear 3 facturas
        invoice_statuses = ['Pendiente', 'Pagada', 'Borrador']
        for i in range(3):
            print(f"\nCreando factura {i+1}/3...")
            # Datos de la factura
            company_id = random.choice(company_ids)
            issue_date = datetime.now() - timedelta(days=random.randint(5, 30))
            due_date = issue_date + timedelta(days=30)
            status = invoice_statuses[i]
            invoice_number = f"FACT-{issue_date.year}-{i+1:04d}"

            # Insertar la cabecera de la factura (con total temporal)
            invoice_data = {
                'company_id': company_id,
                'invoice_number': invoice_number,
                'issue_date': issue_date.isoformat(),
                'due_date': due_date.isoformat(),
                'status': status,
                'total_amount': 0 # Se actualizará después
            }
            invoice_resp = supabase.table("invoices").insert(invoice_data).execute()
            invoice_id = invoice_resp.data[0]['id']
            print(f"  - Factura {invoice_number} creada con ID: {invoice_id}")

            # 3. Crear líneas de detalle para la factura
            total_amount = 0
            num_items = random.randint(2, 4)
            for j in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 5)
                unit_price = float(product['price'])
                subtotal = quantity * unit_price
                total_amount += subtotal

                item_data = {
                    'invoice_id': invoice_id,
                    'product_id': product['id'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'subtotal': subtotal
                }
                supabase.table("invoice_items").insert(item_data).execute()
                print(f"    - Añadido producto {product['id']} (x{quantity}) a la factura.")

            # 4. Actualizar el total de la factura
            supabase.table("invoices").update({'total_amount': total_amount}).eq('id', invoice_id).execute()
            print(f"  - Total de la factura actualizado a: {total_amount:.2f}")

        print("\n¡Inserción de datos completada con éxito!")

    except Exception as e:
        print(f"Ocurrió un error durante la inserción: {e}")

if __name__ == "__main__":
    seed_invoices()
