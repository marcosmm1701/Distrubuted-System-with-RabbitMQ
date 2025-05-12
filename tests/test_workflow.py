import pika
import json
import unittest
import time

class TestControllerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        cls.rabbitmq_host = 'localhost'
        cls.client_queue = '2311-06_client_requests'
        cls.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=cls.rabbitmq_host, port=5673))
        cls.channel = cls.connection.channel()

    def setUp(self):
        """Preparación antes de cada test"""
        self.response_queue = f'test_responses_{int(time.time())}'
        self.channel.queue_declare(queue=self.response_queue, auto_delete=True)
        self.last_response = None
        self.consumer_tag = self.channel.basic_consume(
            queue=self.response_queue,
            on_message_callback=self._store_response,
            auto_ack=True)

    def tearDown(self):
        """Limpieza después de cada test"""
        self.channel.basic_cancel(self.consumer_tag)
        self.channel.queue_delete(queue=self.response_queue)

    @classmethod
    def tearDownClass(cls):
        """Cierra la conexión una vez al terminar"""
        cls.connection.close()

    # ========== TESTS ==========

    def test_client_registration(self):
        """Prueba el registro de un cliente"""
        test_client_id = f"client_{int(time.time())}"
        self._register_client(test_client_id)

    def test_order_creation(self):
        """Prueba creación de un pedido tras el registro"""
        client_id = f"order_client_{int(time.time())}"
        self._register_client(client_id)
        order_id = self._create_order(client_id)
        self.assertIsNotNone(order_id)

    def test_order_status(self):
        """Prueba consultar el estado de un pedido"""
        client_id = f"status_client_{int(time.time())}"
        self._register_client(client_id)
        order_id = self._create_order(client_id)

        self._send_message({
            "type": "STATUS",
            "order_id": order_id,
            "reply_to": self.response_queue
        })
        response = self._wait_for_response()
        print(f"Response (order_status): {response}")
        self.assertEqual(response.get("type"), "STATUS")
        self.assertEqual(response.get("order_id"), order_id)
        self.assertEqual(response.get("estado"), "PROCESANDO")

    def test_order_cancellation(self):
        """Prueba cancelar un pedido antes de ser procesado"""
        client_id = f"cancel_client_{int(time.time())}"
        self._register_client(client_id)
        order_id = self._create_order(client_id)

        self._send_message({
            "type": "CANCEL",
            "order_id": order_id,
            "client_id": client_id,
            "reply_to": self.response_queue
        })
        cancel_response = self._wait_for_response()
        print(f"Response (cancel): {cancel_response}")
        self.assertEqual(cancel_response.get("type"), "CANCELLED")
        self.assertEqual(cancel_response.get("order_id"), order_id)

        # Confirmamos estado final CANCELADO
        self._send_message({
            "type": "STATUS",
            "order_id": order_id,
            "reply_to": self.response_queue
        })
        status_response = self._wait_for_response()
        print(f"Response (status after cancel): {status_response}")
        self.assertEqual(status_response.get("estado"), "CANCELADO")
        
        
        
    def test_list_orders_for_registered_client(self):
        """Prueba listar pedidos de un cliente con pedidos"""
        client_id = f"list_client_{int(time.time())}"
        self._register_client(client_id)

        # Crear varios pedidos
        for _ in range(3):
            self._create_order(client_id)
            time.sleep(1)  # aseguramos orden temporal

        # Pedimos el listado
        self._send_message({
            "type": "LIST",
            "client_id": client_id,
            "reply_to": self.response_queue
        })
        response = self._wait_for_response()
        print(f"Response (list with orders): {response}")
        self.assertEqual(response.get("type"), "LIST")
        self.assertTrue("pedidos" in response)
        self.assertEqual(len(response["pedidos"]), 3)
        # Verificar orden descendente por fecha
        fechas = [pedido["fecha"] for pedido in response["pedidos"]]
        self.assertEqual(fechas, sorted(fechas, reverse=True))

    def test_list_orders_for_client_without_orders(self):
        """Prueba listar pedidos de un cliente que no ha hecho pedidos"""
        client_id = f"empty_list_client_{int(time.time())}"
        self._register_client(client_id)

        self._send_message({
            "type": "LIST",
            "client_id": client_id,
            "reply_to": self.response_queue
        })
        response = self._wait_for_response()
        print(f"Response (list without orders): {response}")
        self.assertEqual(response.get("type"), "EMPTY")
        #self.assertEqual(response.get("order_id"), client_id)

    def test_list_orders_unregistered_client(self):
        """Prueba listar pedidos de un cliente no registrado"""
        unregistered_id = f"fake_{int(time.time())}"

        self._send_message({
            "type": "LIST",
            "client_id": unregistered_id,
            "reply_to": self.response_queue
        })
        response = self._wait_for_response()
        print(f"Response (list unregistered): {response}")
        self.assertEqual(response.get("type"), "ERROR")
        self.assertTrue("error" in response)
        
        

    # ========== FUNCIONES AUXILIARES ==========

    def _register_client(self, client_id):
        self._send_message({
            "type": "REGISTER",
            "client_id": client_id,
            "reply_to": self.response_queue
        })
        response = self._wait_for_response()
        self.assertEqual(response.get("type"), "REGISTERED")
        self.assertEqual(response.get("client_id"), client_id)

    def _create_order(self, client_id):
        self._send_message({
            "type": "CREATE",
            "client_id": client_id,
            "productos": ["producto1", "producto2"],
            "reply_to": self.response_queue
        })
        response = self._wait_for_response()
        self.assertEqual(response.get("type"), "CREATED")
        return response.get("order_id")

    def _send_message(self, msg):
        self.channel.basic_publish(
            exchange='',
            routing_key=self.client_queue,
            body=json.dumps(msg)
        )

    def _store_response(self, ch, method, properties, body):
        self.last_response = json.loads(body.decode())

    def _wait_for_response(self, timeout=30):
        start_time = time.time()
        while not self.last_response and (time.time() - start_time) < timeout:
            self.connection.process_data_events()
            time.sleep(0.1)

        if not self.last_response:
            self.fail("Timeout esperando respuesta")

        response = self.last_response
        self.last_response = None
        return response

if __name__ == '__main__':
    unittest.main()
