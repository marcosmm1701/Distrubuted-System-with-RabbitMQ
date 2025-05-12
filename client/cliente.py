import pika
import json
import time
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from controller.messages import build_response, parse_message
from utils import connect_rabbitmq

class Cliente:
    def __init__(self, client_id: str, controller_queue: str):
        self.client_id = client_id
        self.controller_queue = controller_queue
        self.connection, self.channel = connect_rabbitmq()
        self.response_queue = self.channel.queue_declare(queue='', exclusive=True).method.queue
        self.pending_responses = {}
        self.channel.basic_consume(
            queue=self.response_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self, ch, method, props, body):
        response = parse_message(body)
    
        request_id = response.get('order_id') or response.get('client_id')
    
        if not request_id:
            # fallback: usar tipo de mensaje como clave si no hay ID
            request_id = response.get('type')
    
        if request_id:
            self.pending_responses[request_id] = response
        else:
            print(f"[WARNING] No se pudo identificar request_id para la respuesta: {response}")
    

    def send_message(self, msg_type: str, **kwargs):
        msg = build_response(msg_type, client_id=self.client_id, reply_to=self.response_queue, **kwargs)
        self.channel.basic_publish(
            exchange='',
            routing_key=self.controller_queue,
            properties=pika.BasicProperties(reply_to=self.response_queue),
            body=json.dumps(msg)
        )

    def wait_for_response(self, tipos=None, request_id=None, timeout=60):
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            self.connection.process_data_events()
            time.sleep(0.1)

            for request_id_key, response in list(self.pending_responses.items()):
                if tipos is not None:
                    if response.get('type') in tipos and (request_id is None or response.get('order_id') == request_id or response.get('client_id') == request_id):
                        self.pending_responses.pop(request_id_key)
                        return response
                else:
                    if request_id is None or response.get('order_id') == request_id or response.get('client_id') == request_id or request_id_key == response.get('type'):
                        self.pending_responses.pop(request_id_key)
                        return response

        raise TimeoutError(f"Timeout esperando respuesta de tipo {tipos} con request_id {request_id}")


    def register(self):
        self.send_message("REGISTER")
        return self.wait_for_response(request_id=self.client_id)

    def make_order(self, product_ids):
        self.send_message("CREATE", productos=product_ids)
        return self.wait_for_response(["CREATED", "ERROR"])

    def cancel_order(self, order_id):
        self.send_message("CANCEL", order_id=order_id)
        return self.wait_for_response(["CANCELLED", "ERROR"])

    def query_orders(self):
        self.send_message("LIST")
        return self.wait_for_response(["LIST", "ERROR", "EMPTY"])

    def order_status(self, order_id):
        self.send_message("STATUS", order_id=order_id)
        return self.wait_for_response("STATUS")
    
def print_response(response):
        print(f"[RESPUESTA] Tipo: {response.get('type')}")
        
        # Si la respuesta es de tipo 'LIST', entonces procesamos los pedidos
        if response.get('type') == 'LIST':
            pedidos = response.get('pedidos', [])
            if pedidos:
                print(f"[INFO] Se han encontrado {len(pedidos)} pedidos:")
                for pedido in pedidos:
                    print(f"\n  Pedido {pedido['order_id']}:")
                    print(f"    - Cliente ID: {pedido['cliente_id']}")
                    print(f"    - Productos: {', '.join(pedido['productos'])}")
                    print(f"    - Estado: {pedido['estado']}")
                    print(f"    - Fecha: {pedido['fecha']}\n")
            else:
                print("[INFO] No hay pedidos.")
        else:
            # Si la respuesta no es tipo 'LIST', mostramos el resto de la información
            for key, value in response.items():
                if key != 'type':  # Evitamos imprimir el tipo de respuesta aquí de nuevo
                    print(f"  {key.capitalize()}: {value}")