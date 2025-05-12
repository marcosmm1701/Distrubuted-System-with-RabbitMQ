import uuid
import time
from client.cliente import Cliente, print_response

def main():
    try:
        client_id = str(uuid.uuid4())[:8]
        cliente = Cliente(client_id, controller_queue='2311-06_client_requests')

        print("[INFO] Intentnado pedir sin estar registrado:")
        msg = cliente.make_order(["p1", "p2"])
        print_response(msg)

        print(f"[INFO] Cliente {client_id} registrado.")
        msg = cliente.register()
        print_response(msg)

        productos1 = ["p1", "p2"]
        productos2 = ["p3"]
        productos3 = ["p4", "p5", "p6"]

        print(f"[INFO] Realizando pedido con productos: {productos1}")
        msg = cliente.make_order(productos1)
        print_response(msg)

        print(f"[INFO] Realizando pedido con productos: {productos2}")
        msg = cliente.make_order(productos2)
        print_response(msg)

        print(f"[INFO] Realizando pedido con productos: {productos3}")
        msg = cliente.make_order(productos3)
        print_response(msg)

        print("[INFO] Consultando estado de los pedidos...")
        orders = cliente.query_orders()
        print_response(orders)

        pedidos = orders.get('pedidos', [])
        if not pedidos:
            print("[INFO] No hay pedidos para cancelar ni consultar estado.")
            return
        
        print("[INFO] Esperando a la realización de los pedidos (21s)...")
        time.sleep(21)

        print("[INFO] Consultando estado de los pedidos...")
        orders = cliente.query_orders()
        print_response(orders)
        
        print("[INFO] Intentando cancelar el primer pedido...")
        order_id_to_cancel = pedidos[0]['order_id']
        msg = cliente.cancel_order(order_id_to_cancel)
        print_response(msg)

        print("[INFO] Consultando estado del pedido después de la cancelación...")
        orders = cliente.order_status(order_id_to_cancel)
        print_response(orders)

        print("[INFO] Esperando a la realización de los pedidos nuevamente (60s)...")
        time.sleep(60)

        print("[INFO] Consultando estado de los pedidos después de la espera...")
        orders = cliente.query_orders()
        print_response(orders)
        print("[INFO] Fin de la ejecución del cliente.")

    except KeyboardInterrupt:
        print("\n[INFO] Ejecución interrumpida por el usuario.")
    except Exception as e:
        print(f"[ERROR] Ocurrió un error: {e}")
    finally:
        try:
            if cliente.connection and not cliente.connection.is_closed:
                cliente.connection.close()
                print("[INFO] Conexión cerrada.")
        except:
            pass


if __name__ == '__main__':
    main()