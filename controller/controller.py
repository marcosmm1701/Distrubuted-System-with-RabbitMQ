import pika
import json
import uuid
from controller.pedido import Pedido, PedidoEstado
from controller.storage import StorageManager
from controller.messages import build_response, parse_message
from utils import connect_rabbitmq, log

# Nombres de colas
QUEUE_CLIENTS = '2311-06_client_requests'                   # Recibir peticiones de clientes.
QUEUE_ROBOTS = '2311-06_robot_jobs'                         # Enviar trabajo a robots.
QUEUE_ROBOT_RESPONSES = '2311-06_robot_done'                # Recibir respuestas de robots.
QUEUE_DELIVERIES = '2311-06_delivery_jobs'                  # Enviar trabajo a repartidores.
QUEUE_DELIVERY_RESPONSES = '2311-06_delivery_done'          # Recibir respuestas de repartidores.

class Controlador:
    def __init__(self):
        self.pedidos = {}  # order_id -> Pedido
        self.clientes = set()  # IDs de clientes registrados
        self.storage = StorageManager('Persistencia_Sistema.pkl')
        self.load_state()

        self.conn, self.channel = connect_rabbitmq()

        # Declarar colas
        for queue in [QUEUE_CLIENTS, QUEUE_ROBOTS, QUEUE_ROBOT_RESPONSES,
                      QUEUE_DELIVERIES, QUEUE_DELIVERY_RESPONSES]:
            self.channel.queue_declare(queue=queue, durable=False, auto_delete=True)


    def load_state(self):
        estado = self.storage.load()
        if estado:
            self.pedidos = estado.get('pedidos', {})
            self.clientes = estado.get('clientes', set())


    def save_state(self):
        self.storage.save({
            'pedidos': self.pedidos,
            'clientes': self.clientes
        })




    def run(self):
        log("Controlador iniciado")
        try:
            self.listen_all()
        except KeyboardInterrupt:
            self.save_state()
            log("Controlador finalizado")


    def listen_all(self):
        def callback(ch, method, props, body):
            queue = method.routing_key
            msg = parse_message(body)
            
            log(f"Mensaje recibido en cola {queue}: {msg}")

            if queue == QUEUE_CLIENTS:
                respuesta = self.handle_client_message(msg)
                if respuesta and 'reply_to' in msg:
                    ch.basic_publish(exchange='', routing_key=msg['reply_to'], body=json.dumps(respuesta).encode())

            elif queue == QUEUE_ROBOT_RESPONSES:
                order_id = msg.get("order_id")
                if msg.get("type") == "FOUND":
                    success = True
                elif msg.get("type") == "NOT_FOUND":
                    success = False
                    
                if order_id in self.pedidos:
                    pedido = self.pedidos[order_id]
                    pedido.estado = PedidoEstado.EN_ALMACEN if success else PedidoEstado.SIN_STOCK
                    if success:
                        pedido.estado = PedidoEstado.PREPARADO
                        self.send_to_delivery(order_id)
                    self.save_state()

            elif queue == QUEUE_DELIVERY_RESPONSES:
                order_id = msg.get("order_id")
                
                if msg.get("type") == "DELIVERED":
                    estado = PedidoEstado.ENTREGADO
                elif msg.get("type") == "DELIVERY_FAILED":
                    estado = PedidoEstado.FALLIDO
                    
                if order_id in self.pedidos:
                    self.pedidos[order_id].estado = estado
                    self.save_state()


        # Un solo channel y consume múltiples colas
        self.channel.basic_consume(queue=QUEUE_CLIENTS, on_message_callback=callback, auto_ack=True)
        self.channel.basic_consume(queue=QUEUE_ROBOT_RESPONSES, on_message_callback=callback, auto_ack=True)
        self.channel.basic_consume(queue=QUEUE_DELIVERY_RESPONSES, on_message_callback=callback, auto_ack=True)
        
        log("Esperando mensajes en colas...")

        self.channel.start_consuming()



    def handle_client_message(self, msg):

        tipo = msg['type']
        cliente_id = msg.get("client_id")

        if tipo == "REGISTER":
            if cliente_id in self.clientes:
                return build_response("ERROR", error="Cliente ya registrado")
            
            log("Registrando cliente")
            self.clientes.add(cliente_id)
            self.save_state()
            return build_response("REGISTERED", client_id=cliente_id)

        elif tipo == "CREATE":
            log("Creando pedido")
            if cliente_id not in self.clientes:
                return build_response("ERROR", error="Cliente no registrado")

            order_id = str(uuid.uuid4())[:8]
            productos = msg.get("productos", [])

            pedido = Pedido(order_id, cliente_id, productos)
            self.pedidos[order_id] = pedido
            self.save_state()
            self.send_to_robot(order_id)
            log(f"Pedido creado")
            self.print_pedidos()
            return build_response("CREATED", order_id=order_id)

        elif tipo == "CANCEL":
            if cliente_id not in self.clientes:
                return build_response("ERROR", error="Cliente no registrado")
            
            log("Cancelando pedido")
            order_id = msg.get("order_id")
            pedido = self.pedidos.get(order_id)
            
            if pedido.cliente_id != cliente_id:
                return build_response("ERROR", error="Pedido no pertenece al cliente")

            if pedido and pedido.estado.can_cancel():
                pedido.estado = PedidoEstado.CANCELADO
                self.save_state()
                return build_response("CANCELLED", order_id=order_id)
            return build_response("ERROR", error="No se puede cancelar")

        elif tipo == "LIST":
            log("Listando pedidos")
            if cliente_id not in self.clientes:
                return build_response("ERROR", error="Cliente no registrado")

            pedidos_cliente = [pedido for pedido in self.pedidos.values() if pedido.cliente_id == cliente_id]
            if not pedidos_cliente:
                return build_response("EMPTY")

            pedidos_cliente.sort(key=lambda x: x.fecha, reverse=True)
            response = build_response("LIST", pedidos=[pedido.to_dict() for pedido in pedidos_cliente])
            return response
        
        elif tipo == "STATUS":
            order_id = msg.get("order_id")
            pedido = self.pedidos.get(order_id)
            if pedido:
                return build_response("STATUS", order_id=order_id, estado=pedido.estado.name)
            return build_response("ERROR", error="Pedido no encontrado")

    def send_to_robot(self, order_id):
        msg = build_response("MOVE", order_id=order_id, productos=self.pedidos[order_id].productos)
        self.channel.basic_publish(exchange='',
                                   routing_key=QUEUE_ROBOTS,
                                   body=json.dumps(msg).encode(),
                                   properties=pika.BasicProperties(
                                       reply_to=QUEUE_ROBOT_RESPONSES
                                   ))
        
        self.pedidos[order_id].estado = PedidoEstado.PROCESANDO
        self.save_state()

    def send_to_delivery(self, order_id):
        msg = build_response("DELIVER", order_id=order_id)
        self.channel.basic_publish(exchange='', routing_key=QUEUE_DELIVERIES,
                                   body=json.dumps(msg).encode(),
                                   properties=pika.BasicProperties(
                                       reply_to=QUEUE_DELIVERY_RESPONSES
                                   ))
        self.pedidos[order_id].estado = PedidoEstado.EN_REPARTO
        self.save_state()




    def print_pedidos(self, detailed=False, filter_estado=None):
        """Imprime todos los pedidos
        Args:
            detailed (bool): Modo detallado
            filter_estado (PedidoEstado): Filtra por estado
        """
        if not self.pedidos:
            print("\nNo hay pedidos registrados")
            return

        print(f"\n{'='*50}")
        print(f"{'LISTADO DE PEDIDOS':^50}")
        print(f"{f'(Filtro: {filter_estado.name}' if filter_estado else '':^50}")
        print(f"{'='*50}")

        for pedido in self.pedidos.values():
            if filter_estado and pedido.estado != filter_estado:
                continue
            pedido.print_pedido(detailed)

        print(f"\nTotal pedidos: {len(self.pedidos)}")
        if filter_estado:
            filtered_count = sum(1 for p in self.pedidos.values() if p.estado == filter_estado)
            print(f"Filtrados: {filtered_count}")
        print(f"{'='*50}")
