import json
from unittest.mock import Mock, patch
from controller.messages import build_response
from delivery.delivery import Repartidor
import unittest

class TestDeliveryUnit(unittest.TestCase):
    def setUp(self):
        self.mock_channel = Mock()
        self.mock_connection = Mock()

        # Crear Repartidor con mocks
        self.repartidor = Repartidor(p_entrega=0.5, connection=self.mock_connection, channel=self.mock_channel)

        self.order_id = "pedido123"
        self.msg = build_response("DELIVER", order_id=self.order_id)  # Cambiado a 'DELIVER'
        self.body = json.dumps(self.msg).encode()

        self.mock_properties = Mock()
        self.mock_properties.reply_to = "reply_queue_test"

    def check_published_message(self, expected_type, expected_intento=None):
        assert self.mock_channel.basic_publish.called, "Error: No se publicó ninguna respuesta."
        args, kwargs = self.mock_channel.basic_publish.call_args
        response = kwargs['body']

        if isinstance(response, bytes):
            response = response.decode()

        response_json = json.loads(response)
        assert response_json["order_id"] == self.order_id, "El order_id no coincide."
        assert response_json["type"] == expected_type, f"Esperaba '{expected_type}' pero recibió '{response_json['type']}'"

        if expected_type == "DELIVERED":
            assert response_json["intento"] == expected_intento, f"Esperaba intento {expected_intento}, obtuvo {response_json['intento']}"

        print(f"[TEST] Mensaje publicado: {response_json}")
        return response_json

    def test_entrega_exitosa_en_intento_1(self):
        print("\nIniciando test: Entrega exitosa en intento 1")
        with patch("random.random", side_effect=[0.1]), patch("time.sleep", return_value=None):
            self.repartidor.handle_task(self.mock_channel, None, self.mock_properties, self.body)
            self.check_published_message("DELIVERED", expected_intento=1)
            print("✔️   Entrega exitosa en intento 1.\n")

    def test_entrega_exitosa_en_intento_2(self):
        print("\nIniciando test: Entrega exitosa en intento 2")
        with patch("random.random", side_effect=[0.8, 0.2]), patch("time.sleep", return_value=None):
            self.repartidor.handle_task(self.mock_channel, None, self.mock_properties, self.body)
            self.check_published_message("DELIVERED", expected_intento=2)
            print("✔️   Entrega exitosa en intento 2.\n")

    def test_entrega_exitosa_en_intento_3(self):
        print("\nIniciando test: Entrega exitosa en intento 3")
        with patch("random.random", side_effect=[0.8, 0.9, 0.3]), patch("time.sleep", return_value=None):
            self.repartidor.handle_task(self.mock_channel, None, self.mock_properties, self.body)
            self.check_published_message("DELIVERED", expected_intento=3)
            print("✔️   Entrega exitosa en intento 3.\n")

    def test_entrega_fallida(self):
        print("\nIniciando test: Entrega fallida tras 3 intentos")
        with patch("random.random", side_effect=[0.99, 0.95, 0.98]), patch("time.sleep", return_value=None):
            self.repartidor.handle_task(self.mock_channel, None, self.mock_properties, self.body)
            self.check_published_message("DELIVERY_FAILED")
            print("✔️   Entrega fallida tras 3 intentos.\n")

# Ejecutar los tests
if __name__ == '__main__':
    test = TestDeliveryUnit()
    test.test_entrega_exitosa_en_intento_1()
    test.test_entrega_exitosa_en_intento_2()
    test.test_entrega_exitosa_en_intento_3()
    test.test_entrega_fallida()