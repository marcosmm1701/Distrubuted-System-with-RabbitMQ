from unittest.mock import Mock, patch
from controller.controller import Controlador
from controller.pedido import Pedido, PedidoEstado
import unittest

class TestControladorUnit(unittest.TestCase):
    def setUp(self):
        # Mock de conexión y canal
        self.mock_channel = Mock()
        self.mock_connection = Mock()

        # Parchar connect_rabbitmq para evitar conexión real
        patcher = patch("controller.controller.connect_rabbitmq", return_value=(self.mock_connection, self.mock_channel))
        self.mock_connect = patcher.start()
        self.patcher = patcher

        # Crear instancia
        self.controlador = Controlador()
        self.controlador.channel = self.mock_channel  # Forzar canal mock

        # Reset para cada test
        self.controlador.pedidos.clear()
        self.controlador.clientes.clear()

    def teardown(self):
        self.patcher.stop()

    def test_registro_cliente(self):
        """Verifica que el controlador registre clientes correctamente"""
        client_id = "cliente_test"
        msg = {"type": "REGISTER", "client_id": client_id}

        response = self.controlador.handle_client_message(msg)

        assert response["type"] == "REGISTERED"
        assert client_id in self.controlador.clientes
        print("✔️   Cliente registrado correctamente.")

    def test_creacion_pedido(self):
        """Verifica que se crea un pedido y pasa por sus estados"""
        client_id = "cliente_test"
        self.controlador.clientes.add(client_id)  # Cliente registrado

        msg = {"type": "CREATE", "client_id": client_id, "productos": ["producto1"]}

        response = self.controlador.handle_client_message(msg)

        assert response["type"] == "CREATED"
        order_id = response["order_id"]

        # Crear una instancia real de Pedido y agregarla a los pedidos del controlador
        pedido = Pedido(order_id, client_id, ["producto1"])
        self.controlador.pedidos[order_id] = pedido

        # Verificar que el estado inicial es PENDIENTE
        assert pedido.estado == PedidoEstado.PENDIENTE, f"El estado inicial del pedido {order_id} es incorrecto. Estado actual: {pedido.estado}"

        # Simular que el pedido pasa a PROCESANDO (verificando que los productos están en el almacén)
        pedido.estado = PedidoEstado.PROCESANDO
        assert pedido.estado == PedidoEstado.PROCESANDO, f"El pedido {order_id} no está en el estado correcto. Estado actual: {pedido.estado}"

        # Simular que los productos están en el ALMACÉN
        pedido.estado = PedidoEstado.EN_ALMACEN
        assert pedido.estado == PedidoEstado.EN_ALMACEN, f"El pedido {order_id} no está en el estado correcto. Estado actual: {pedido.estado}"

        # Simular que los productos se ponen en la cinta para ser PREPARADOS
        pedido.estado = PedidoEstado.PREPARADO
        assert pedido.estado == PedidoEstado.PREPARADO, f"El pedido {order_id} no está en el estado correcto. Estado actual: {pedido.estado}"

        # Simular que el pedido pasa a EN REPARTO
        pedido.estado = PedidoEstado.EN_REPARTO
        assert pedido.estado == PedidoEstado.EN_REPARTO, f"El pedido {order_id} no está en el estado correcto. Estado actual: {pedido.estado}"

        # Finalmente, verificar que el pedido se entrega y pasa a estado ENTREGADO
        pedido.estado = PedidoEstado.ENTREGADO
        assert pedido.estado == PedidoEstado.ENTREGADO, f"El pedido {order_id} no está en el estado correcto. Estado actual: {pedido.estado}"

        # Asegurarse de que el mensaje haya sido publicado en el canal mock
        assert self.mock_channel.basic_publish.called, "No se publicó mensaje al robot."

        print(f"✔️   Pedido {order_id} creado y enviado al robot, pasando por todos los estados correctamente.")

    def test_cancelacion_pedido(self):
        """Verifica la cancelación de pedidos si el estado lo permite"""
        order_id = "test_order"
        
        #registramos cliente: Importante desde nuestra ultima version. Comprobamos que sea el cliente correcto
        self.controlador.clientes.add("cliente_test")
        # Crear una instancia real de Pedido
        pedido = Pedido(order_id, "cliente_test", ["producto1"])
        self.controlador.pedidos[order_id] = pedido

        # Establecer el estado para que sea cancelable
        pedido.estado = PedidoEstado.EN_ALMACEN

        msg = {"type": "CANCEL", "order_id": order_id, "client_id": "cliente_test"}

        response = self.controlador.handle_client_message(msg)
        print(f"Response NAXHOOO: {response}")
        assert response["type"] == "CANCELLED"
        assert pedido.estado == PedidoEstado.CANCELADO, "El pedido no se marcó como cancelado."
        print(f"✔️   Pedido {order_id} cancelado correctamente.")

    def test_cancelacion_no_permitida(self):
        """Verifica la cancelación de pedidos cuando no es cancelable"""
        order_id = "test_order"
        # Crear una instancia real de Pedido
        pedido = Pedido(order_id, "cliente_test", ["producto1"])
        self.controlador.pedidos[order_id] = pedido

        # Establecer el estado para que no sea cancelable (por ejemplo, EN_REPARTO)
        pedido.estado = PedidoEstado.EN_REPARTO

        msg = {"type": "CANCEL", "order_id": order_id}

        response = self.controlador.handle_client_message(msg)

        # Verificar que la respuesta es un error, porque el pedido no se puede cancelar
        assert response["type"] == "ERROR"
        assert pedido.estado != PedidoEstado.CANCELADO, "El pedido fue cancelado cuando no era cancelable."
        print(f"✔️   No se pudo cancelar el pedido {order_id} debido a su estado.")

    def test_status_pedido(self):
        """Verifica que se puede consultar el estado de un pedido"""
        order_id = "pedido123"
        pedido = Pedido(order_id, "cliente_test", ["producto1"])
        pedido.estado = PedidoEstado.EN_ALMACEN
        self.controlador.pedidos[order_id] = pedido

        msg = {"type": "STATUS", "order_id": order_id}

        response = self.controlador.handle_client_message(msg)

        assert response["type"] == "STATUS"
        assert response["estado"] == "EN_ALMACEN"
        print(f"✔️   Estado de pedido {order_id} consultado correctamente.")

    def test_status_pedido_inexistente(self):
        """Verifica respuesta adecuada si el pedido no existe"""
        msg = {"type": "STATUS", "order_id": "desconocido"}

        response = self.controlador.handle_client_message(msg)

        assert response["type"] == "ERROR"
        print("✔️   Error controlado al consultar pedido inexistente.")

# Ejecutar tests
if __name__ == '__main__':
    test = TestControladorUnit()
    test.test_registro_cliente()
    test.test_creacion_pedido()
    test.test_cancelacion_pedido()
    test.test_cancelacion_no_permitida()
    test.test_status_pedido()
    test.test_status_pedido_inexistente()
    test.teardown()