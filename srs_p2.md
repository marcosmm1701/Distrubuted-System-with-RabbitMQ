# Índice
1. [Introdución](#introduccion)
2. [Definición del proyecto](#definicion)
3. [Conclusiones](#solucion)
3. [Conclusiones](#conclusiones)


# 1. Introducción
El objetivo de Saimazoom es el de crear un sistema para la gestión de pedidos online. Este sistema debe incluir a los actores:
* **Cliente**, que realiza y gestiona pedidos de productos.
* **Controlador** central, que gestiona todo el proceso.
* **Robots**, que se encargan de buscar los productos en el almacén y colocarlos en las cintas transportadoras.
* **Repartidores**, encargados de transportar el producto a la casa del cliente
* **Admin** encargados de gestionar la base de datos del controlador central

El sistema debe de gestionar las interacciones entre todos estos actores, para las comunicaciones correspondientes se empleará una cola de mensajes.


# 2. Definición del proyecto
El sistema Saimazoom, como conjunto, debe gestionar pedidos, en los que los **clientes** pueden solicitar un producto. Una vez recibido un pedido, el **controlador** debe avisar a un **robot**, que mueve dicho producto del almacén a la cinta transportadora. Una vez en la cinta transportadora, el controlador avisa a un **repartidor**, que lleva el producto a la casa del **cliente**. 
<!-- Las comunicaciones pertinentes entre estos elementos estarán gestionadas por un **controlador** central, que mantiene la comunicación entre los **clientes**, **robots** y **repartidores**. -->

## 2.1. Objetivos y funcionalidad
Los objetivos principales son: 
* La gestión de los pedidos de los **clientes**, que pueden hacer, ver  y cancelar pedidos.
* La gestión de los **robots**, que reciben ordenes de de transportar los productos del almacen a la cinta transportadora.
* La gestión de los **repartidores**, que reparten los productos que hay en la cinta transportadora a la casa de los clientes.
* La gestión del **controlador** central, que tiene que mantener un control de productos, **clientes**, **robots** y **repartidores**. Tiene que guardar también los pedidos, con sus estados, que dependen de la relación con el resto de actores.
* La comunicación entre el **controlador** y el resto de actores

Para cumplir estos objetivos es necesario desarrollar una serie de funcionalidades básicas:
1. Registro de **Cliente**: registro desde una petición de un **Cliente** con un identificador de **cliente** que tiene que ser único.
2. Registro de Pedido: registro en la base de datos del **controlador** central con un id de **cliente** y de producto, también le asigna un estado al pedido.
3. Recepción de pedidos de los **Clientes**: hay que recibir y guardar los pedidos a realizar que están asociados a un **Cliente** y a un producto.
4. Asignación de trabajo a los **Robots**: hay que asignar a los **robots** las tareas de transporte de productos correspondientes a pedidos.
5. Asignación de trabajo a los **Repartidores**: hay que asignar a los **repartidores** las tareas de transporte de productos correspondientes a pedidos.

## 2.2. Requisitos
Nos limitaremos a los requisitos funcionales, estos los podemos dividir en los siguientes apartados:

### 2.2.1. **Lógica de clientes**
**LoCl1**. Registro en la aplicación en el que se recibe confirmación  
**LoCl2**. Realizar un pedido, en el que se pide un producto  
**LoCl3**. Pedir una lista de los pedidos realizados en la que se incluya id del producto correspondiente al pedido y estado del pedido  
**LoCl4**. Pedir la cancelación de un pedido

# 3. Implementación
Nuestra implementación de Saimazoom se organiza en varios componentes principales, que son los responsables de realizar las tareas según los roles definidos en el proyecto.

1. **Controlador**:  
   El **Controlador** es el núcleo del sistema, encargado de coordinar todos los actores. La comunicación entre los distintos componentes (clientes, robots y repartidores) se realiza a través de colas de mensajes, garantizando la asincronía y la distribución de tareas. El controlador maneja los pedidos, los asigna a los robots y repartidores, y actualiza el estado de los pedidos en el sistema.

2. **Clientes**:  
   Los clientes pueden interactuar con el sistema mediante una interfaz de comando a traves de la terminal. El cliente puede registrarse, realizar pedidos, consultar el estado de sus pedidos, ver una lista de sus pedidos y cancelarlos si es necesario. Los pedidos son gestionados por el controlador y pasan por un proceso que involucra tanto a los robots como a los repartidores.

3. **Robots**:  
   Los robots tienen la tarea de trasladar los productos desde el almacén hasta la cinta transportadora. Una vez que el controlador asigna una tarea al robot, el robot se comunica con el controlador para informar si el producto fue encontrado y movido correctamente. Cada robot cuenta con un tiempo de espera aleatorio, que simula el tiempo de búsqueda del producto en el almacén. Si todos los prpoductos de un pedido se encuentran en el almacen, el pedidio pasará a estar en el estado EN_ALMACEN, mientras que si se encuentra alguno de los productos, pasará al estado SIN_STOCK.

4. **Repartidores**:  
   Los repartidores son los responsables de la entrega final de los productos a los clientes. Cuando el producto está en la cinta transportadora, el controlador asigna una tarea a un repartidor, quien debe intentar entregar el producto. Los repartidores tienen un número limitado de intentos para realizar la entrega, y en caso de fallar tres veces, el pedido se marca como FALLIDO. En caso de ser entregado, su estado pasará a ENTREGADO.

5. **Persistencia**:  
   Se utiliza el formato **Pickle** para almacenar de manera persistente los datos relacionados con los clientes, productos y pedidos. Esto permite mantener el estado del sistema incluso si se reinicia el mismo. El sistema recupera la información desde los archivos guardados y puede seguir operando sin pérdida de datos.

6. **Comunicación**:  
   El sistema utiliza **RabbitMQ** para la gestión de la cola de mensajes entre el controlador y los demás actores (clientes, robots, repartidores). Este sistema de colas garantiza que las tareas se realicen de manera asíncrona, optimizando el flujo de trabajo y mejorando la eficiencia.

# 4. Conclusiones
Nuestro sistema Saimazoom ha sido diseñado para gestionar el proceso de pedidos de productos de forma eficiente y escalable. La implementación utiliza tecnologías como **RabbitMQ** para la comunicación asíncrona entre los distintos actores del sistema y **Pickle** para la persistencia de datos.

Entre las ventajas del sistema, podemos destacar:

- **Escalabilidad**: La arquitectura basada en mensajes permite agregar más robots y repartidores sin afectar al rendimiento del sistema.
- **Flexibilidad**: El sistema puede adaptarse fácilmente a nuevos requerimientos, como la integración de más tipos de productos o cambios en los procesos de entrega.
- **Robustez**: La separación de responsabilidades entre el controlador, los robots, los repartidores y los clientes hace que el sistema sea modular y fácil de mantener.
- **Asincronía**: Gracias al uso de RabbitMQ, el sistema puede manejar múltiples tareas en paralelo, mejorando el rendimiento general y reduciendo el tiempo de espera para los usuarios.

# 4.1 Observaciones
En nuestra implementación, los clientes envían su propio client_id al registrarse en el servidor. Esta decisión se tomó por simplicidad y para facilitar la trazabilidad y reconexión de los componentes, ajustándose a los objetivos de la práctica.

Sin embargo, en un entorno real, lo recomendable sería que un middleware centralizado generase los identificadores, garantizando unicidad, seguridad y mayor escalabilidad del sistema.


# 4.2 Modo de ejecución
Para poder ejecutar todos los módulos de forma automática y con el número de robots y repartidores deseado, se ha implementado un script llamado main_launcher.sh, con el que se lanzará todo el sistema.

También se ha implementado un makefile para poder lanzar los módulos por separado, así como ejecutar todos los tests a la vez mediante el comando make test.
