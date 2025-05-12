# Makefile para el proyecto saimazoom

PYTHON=python3

# Colores
GREEN=\033[0;32m
NC=\033[0m

# Directorios
SRC_DIR=.
TEST_DIR=tests

.PHONY: help run-controller run-client run-robot run-delivery test lint clean

help:
	@echo -e "$(GREEN)Comandos disponibles:$(NC)"
	@echo "  make run-controller     		-> Ejecuta el controlador"
	@echo "  make run-client-simulator  		-> Ejecuta el cliente de simulación"
	@echo "  make run-client-interactive 		-> Ejecuta el cliente interactivo"
	@echo "  make run-robot          		-> Ejecuta un robot"
	@echo "  make run-delivery       		-> Ejecuta un repartidor"
	@echo "  make test               		-> Ejecuta los tests unitarios"
	@echo "  make clean              		-> Limpia archivos temporales"

run-controller:
	@echo -e "$(GREEN)Lanzando controlador...$(NC)"
	$(PYTHON) -m controller.launch_controller

run-client-simulator:
	@echo -e "$(GREEN)Lanzando cliente...$(NC)"
	$(PYTHON) -m client.launch_client

run-client-interactive:
	@echo -e "$(GREEN)Lanzando cliente interactivo...$(NC)"
	$(PYTHON) -m client.commandline_client

run-robot:
	@echo -e "$(GREEN)Lanzando robot...$(NC)"
	$(PYTHON) -m robot.launch_robot

run-delivery:
	@echo -e "$(GREEN)Lanzando repartidor...$(NC)"
	$(PYTHON) -m delivery.launch_delivery

test:
	@echo -e "$(GREEN)Ejecutando tests...$(NC)"
	PYTHONPATH=$(SRC_DIR) $(PYTHON) -m unittest discover -s $(TEST_DIR)


clean:
	@echo -e "$(GREEN)Limpiando archivos temporales...$(NC)"
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pkl" -delete
