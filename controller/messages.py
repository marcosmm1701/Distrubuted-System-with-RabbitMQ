import json

def parse_message(body):     #body: contenido del mensaje recibido desde RabbitMQ, se envia como bytes
    if isinstance(body, bytes):
        body = body.decode()    # pasamos de bytes a string
    return json.loads(body)   # pasamos de string a diccionario (json)

def build_response(tipo, **kwargs):   #tipo: tipo de mensaje que queremos enviar ("REGISTER", "MOVED", "ERROR")
    msg = {"type": tipo}              #kwargs: argumentos adicionales
    msg.update(kwargs)
    return msg
