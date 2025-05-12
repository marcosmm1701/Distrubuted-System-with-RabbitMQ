import json
from unittest.mock import Mock
from robot.robot import Robot
from controller.messages import build_response
import unittest

class TestRobotUnit(unittest.TestCase):
    def setup_found(self):
        """Configurar entorno para simular que el producto siempre se encuentra (FOUND)."""
        self.mock_channel = Mock()
        self.mock_connection = Mock()
        self.robot = Robot(p_almacen=1.0, connection=self.mock_connection, channel=self.mock_channel)

        self.order_id = "test123"
        self.productos = ["id363", "id78347", "id9734"]
        self.msg = build_response("MOVE", order_id=self.order_id, productos=self.productos)
        self.body = json.dumps(self.msg).encode()

        self.mock_properties = Mock()
        self.mock_properties.reply_to = "test_reply_queue"

    def setup_not_found(self):
        """Configurar entorno para simular que el producto nunca se encuentra (NOT_FOUND)."""
        self.mock_channel = Mock()
        self.mock_connection = Mock()
        self.robot = Robot(p_almacen=0.0, connection=self.mock_connection, channel=self.mock_channel)

        self.order_id = "test123"
        self.productos = ["id363", "id78347", "id9734"]
        self.msg = build_response("MOVE", order_id=self.order_id, productos=self.productos)
        self.body = json.dumps(self.msg).encode()

        self.mock_properties = Mock()
        self.mock_properties.reply_to = "test_reply_queue"

    def test_robot_task_found(self):
        print("\nIniciando test: Producto encontrado...")
        self.setup_found()

        self.robot.handle_task(self.mock_channel, None, self.mock_properties, self.body)

        assert self.mock_channel.basic_publish.called, "Error: ¡El robot no publicó ninguna respuesta!"
        args, kwargs = self.mock_channel.basic_publish.call_args
        response = kwargs['body']

        if isinstance(response, bytes):
            response = response.decode()

        response_json = json.loads(response)
        print(f"[TEST] Mensaje publicado: {response_json}")

        assert response_json["order_id"] == self.order_id, "El order_id de la respuesta no es correcto."
        assert response_json["type"] == "FOUND", f"Se esperaba 'FOUND', pero se recibió {response_json['type']}."

        print("✔️   Test exitoso: Producto encontrado.")

    def test_robot_task_not_found(self):
        print("\nIniciando test: Producto NO encontrado...")
        self.setup_not_found()

        self.robot.handle_task(self.mock_channel, None, self.mock_properties, self.body)

        assert self.mock_channel.basic_publish.called, "Error: ¡El robot no publicó ninguna respuesta!"
        args, kwargs = self.mock_channel.basic_publish.call_args
        response = kwargs['body']

        if isinstance(response, bytes):
            response = response.decode()

        response_json = json.loads(response)
        print(f"[TEST] Mensaje publicado: {response_json}")

        assert response_json["order_id"] == self.order_id, "El order_id de la respuesta no es correcto."
        assert response_json["type"] == "NOT_FOUND", f"Se esperaba 'NOT_FOUND', pero se recibió {response_json['type']}."

        print("✔️   Test exitoso: Producto NO encontrado.\n")

# Ejecutar tests
if __name__ == '__main__':
    test = TestRobotUnit()
    test.test_robot_task_found()
    test.test_robot_task_not_found()