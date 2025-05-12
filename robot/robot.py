import json
import time
import random
import uuid
from controller.messages import parse_message, build_response
from utils import connect_rabbitmq

class Robot:
    def __init__(self, p_almacen=0.9, connection=None, channel=None):
        self.p_almacen = p_almacen
        self.id = str(uuid.uuid4())[:4]

        if connection is None or channel is None:
            self.conn, self.channel = connect_rabbitmq()
        else:
            self.conn = connection
            self.channel = channel

        self.robot_queue = '2311-06_robot_jobs'
        self.channel.queue_declare(queue=self.robot_queue, durable=False, auto_delete=True)
        self.channel.basic_consume(queue=self.robot_queue,
                                   on_message_callback=self.handle_task,
                                   auto_ack=True)

    def handle_task(self, ch, method, properties, body):
        msg = parse_message(body)
        order_id = msg.get("order_id")
        
        tipo = msg.get("type")
        if tipo != "MOVE":
            print(f"[ROBOT - {self.id}] Tipo de mensaje no soportado: {tipo}")
            return

        print(f"[ROBOT - {self.id}] Procesando pedido {order_id}...")

        


        # Simulamos la comprobación de stock
        productos = msg.get("productos")
        encontrados = True
        
        for producto in productos:
            time.sleep(random.randint(5, 10))
            if random.random()  < self.p_almacen:
                print(f"[ROBOT - {self.id}] Producto {producto} encontrado para pedido {order_id}")
            else:
                print(f"[ROBOT - {self.id}] Producto {producto} NO encontrado para pedido {order_id}")
                encontrados = False
                
        if encontrados:
            response = build_response("FOUND", order_id=order_id)
            print(f"[ROBOT - {self.id}] Todos los productos encontrados para pedido {order_id}")
        else:
            response = build_response("NOT_FOUND", order_id=order_id)
            print(f"[ROBOT - {self.id}] No todos los productos encontrados para pedido {order_id}")
                

        
        self.channel.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            body=json.dumps(response)
        )

    def start(self):
        print(f"[ROBOT - {self.id}] Esperando tareas...")
        self.channel.start_consuming()
