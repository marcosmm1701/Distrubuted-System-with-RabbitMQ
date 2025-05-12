import pika
import uuid
import argparse
from client.cliente import Cliente, print_response

def print_help():
    print("""
Comandos disponibles:
  register                - Registrar un cliente.
  order <p1> <p2> ...     - Crear un pedido con productos.
  cancel <order_id>       - Cancelar un pedido por ID.
  query                   - Consultar tus pedidos.
  status <order_id>       - Consultar el estado de un pedido por ID.
  help                    - Mostrar esta ayuda.
  exit                    - Salir del cliente.
""")

def main():

    try:
        client_id = str(uuid.uuid4())[:8]
        cliente = Cliente(client_id, controller_queue='2311-06_client_requests')

        print("[INFO] Para ver el manual de uso escribe 'help'")

        while True:
            cmd = input(">> ").strip().lower()

            if cmd == "exit":
                break

            elif cmd == "register":
                print_response(cliente.register())

            elif cmd == "help":
                print_help()

            elif cmd.startswith("order"):
                parts = cmd.split()
                if len(parts) < 2:
                    print("Uso: order <producto1> <producto2> ...")
                else:
                    _, *products = parts
                    msg = cliente.make_order(products)
                    print_response(msg)

            elif cmd.startswith("cancel"):
                parts = cmd.split()
                if len(parts) != 2:
                    print("Uso: cancel <order_id>")
                else:
                    _, order_id = parts
                    print_response(cliente.cancel_order(order_id))

            elif cmd == "query":
                print_response(cliente.query_orders())

            elif cmd.startswith("status"):
                parts = cmd.split()
                if len(parts) != 2:
                    print("Uso: status <order_id>")
                else:
                    _, order_id = parts
                    print_response(cliente.order_status(order_id))
            else:
                print("Comando no reconocido. Escribe 'help' para ver la lista de comandos.")

    except Exception as e:
        print(f"[ERROR] {e}")
    except KeyboardInterrupt:
        print("\n[INFO] Interrupción del usuario. Cerrando cliente...")
    finally:
        try:
            cliente.connection.close()
            print("Conexión cerrada.")
        except:
            pass

if __name__ == "__main__":
    main()
