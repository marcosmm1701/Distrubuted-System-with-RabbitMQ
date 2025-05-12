from enum import Enum
from datetime import datetime

class PedidoEstado(Enum):
    PENDIENTE = "PENDIENTE"     # Estado inicial
    
    PROCESANDO = "PROCESANDO"     # Comprobando el stock de productos
    
    EN_ALMACEN = "EN_ALMACEN"   # Todos los productos están en el almacén
    SIN_STOCK = "SIN_STOCK"     # No hay stock de productos
    
    PREPARADO = "PREPARADO"     # Pedido preparado para ser enviado
    
    EN_REPARTO = "EN_REPARTO"
    
    ENTREGADO = "ENTREGADO"
    FALLIDO = "FALLIDO"
    
    CANCELADO = "CANCELADO"
    

    def can_cancel(self):
        return self in [PedidoEstado.PENDIENTE, PedidoEstado.PROCESANDO, PedidoEstado.EN_ALMACEN, PedidoEstado.SIN_STOCK, PedidoEstado.PREPARADO]


class Pedido:
    def __init__(self, order_id, cliente_id, productos_ids):
        self.order_id = order_id
        self.cliente_id = cliente_id
        self.productos = productos_ids
        self.estado = PedidoEstado.PENDIENTE
        self.fecha = datetime.now().isoformat()

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "cliente_id": self.cliente_id,
            "productos": self.productos,
            "estado": self.estado.value,
            "fecha": self.fecha
        }

    @staticmethod
    def from_dict(data):
        p = Pedido(
            data["order_id"],
            data["cliente_id"],
            data["productos"],
            data["fecha"]
        )
        p.estado = PedidoEstado(data["estado"])
        return p
    
    
    def print_pedido(self, detailed=False):
        """Imprime la información del pedido
        Args:
            detailed (bool): Si True muestra formato extendido
        """
        if detailed:
            print(f"\n[Pedido {self.order_id}]")
            print(f"  Cliente: {self.cliente_id}")
            print(f"  Estado: {self.estado.name}")
            print(f"  Productos: {', '.join(self.productos)}")
        else:
            print(f"{self.order_id} | {self.cliente_id} | {self.estado.name} | {len(self.productos)} productos")
