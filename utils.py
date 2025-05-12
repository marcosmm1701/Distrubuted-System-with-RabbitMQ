import uuid
import random
import time
import pika
from datetime import datetime
import json
import os


def generar_id():
    """Genera un UUID único para pedidos o clientes."""
    return str(uuid.uuid4())


def delay_segundos(min_s=1, max_s=2):
    """Simula una espera aleatoria entre min_s y max_s segundos."""
    tiempo = random.uniform(min_s, max_s)
    time.sleep(tiempo)
    return tiempo


def exito(probabilidad):
    """
    Simula un evento con éxito basado en una probabilidad (entre 0 y 1).
    Ejemplo: exito(0.7) -> 70% de probabilidades de éxito.
    """
    return random.random() < probabilidad


def log(mensaje, actor="SYSTEM"):
    """
    Imprime un log con marca de tiempo y el actor que lo emite.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{actor}] {mensaje}")


def connect_rabbitmq(host="localhost"):
    """
    Conecta con RabbitMQ y crea una cola si no existe.
    Devuelve conexión, canal y la cola declarada.
    """
    try: 
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost',
                                                                       port= 5673,
                                                                       ))
        log(f"Conectado a RabbitMQ en {host}")
        channel = connection.channel()
        #channel.queue_declare(queue=queue_name, durable=durable, auto_delete=auto_delete)
        return connection, channel

    except Exception as e:
        log(f"Error al conectar a RabbitMQ: {e}", actor="SYSTEM")
        raise
    
    
def cargar_configuracion(nombre_archivo='config.json'):
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_completa = os.path.join(ruta_actual, nombre_archivo)

    with open(ruta_completa, 'r') as f:
        config = json.load(f)
    return config
