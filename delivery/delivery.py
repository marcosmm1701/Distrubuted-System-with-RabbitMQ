import json
import time
import random
import uuid
from controller.messages import parse_message, build_response
from utils import connect_rabbitmq

class Repartidor:
    def __init__(self, p_entrega=0.3, connection=None, channel=None):
        self.p_entrega = p_entrega
        self.id = str(uuid.uuid4())[:4]
        if connection is None or channel is None:
            self.conn, self.channel = connect_rabbitmq()
        else:
            self.conn = connection
            self.channel = channel
        self.delivery_queue = '2311-06_delivery_jobs'
        self.channel.queue_declare(queue=self.delivery_queue, durable=False, auto_delete=True)
        self.channel.basic_consume(queue=self.delivery_queue,
                                   on_message_callback=self.handle_task,
                                   auto_ack=True)

    def handle_task(self, ch, method, properties, body):
        msg = parse_message(body)
        order_id = msg.get("order_id")
        
        tipo = msg.get("type")
        if tipo != "DELIVER":
            print(f"[REPARTIDOR - {self.id}] Tipo de mensaje no soportado: {tipo}")
            return

        print(f"[REPARTIDOR - {self.id}] Entregando pedido {order_id}...")

        for intento in range(1, 4):
            time.sleep(random.randint(10, 20))  # Simulamos intento de entrega

            if random.random() < self.p_entrega:
                response = build_response("DELIVERED", order_id=order_id, intento=intento)
                print(f"[REPARTIDOR - {self.id}] Pedido {order_id} entregado en intento {intento}")
                break
        else:
            response = build_response("DELIVERY_FAILED", order_id=order_id)
            print(f"[REPARTIDOR - {self.id}] Fallo la entrega del pedido {order_id} tras 3 intentos")

        self.channel.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            body=json.dumps(response)
        )

    def start(self):
        print(f"[REPARTIDOR - {self.id}] Esperando pedidos para repartir...")
        self.channel.start_consuming()      # Iniciamos el ciclo de espera de mensajes
