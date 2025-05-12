from delivery.delivery import Repartidor
from utils import cargar_configuracion

if __name__ == "__main__":
    conf = cargar_configuracion()
    p_entrega = conf.get("probabilidad_entrega")
    repartidor = Repartidor(p_entrega=0.3)
    try:
        repartidor.start()
    except KeyboardInterrupt:
        print("\n[REPARTIDOR] Saliendo...")

