from robot.robot import Robot
from utils import cargar_configuracion

if __name__ == "__main__":
    # Cargar configuración
    config = cargar_configuracion()
    p_almacen = config.get("probabilidad_almacen")
    robot = Robot(p_almacen)
    try:
        robot.start()
    except KeyboardInterrupt:
        print("\n[ROBOT] Saliendo...")

