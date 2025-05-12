#!/bin/bash

# ---------------------------
# Lanzador de simulación real
# Uso: ./main_launcher.sh <num_robots> <num_repartidores>
# ---------------------------

ROBOTS=${2:-1}       # Número de robots (por defecto 1)
REPARTIDORES=${2:-1} # Número de repartidores (por defecto 1)

echo "Lanzando controlador con make..."
make run-controller &
PIDS=()
PIDS+=($!)

echo "Lanzando $ROBOTS robots con make..."
for ((i=1; i<=ROBOTS; i++)); do
    make run-robot &
    PIDS+=($!)
    echo "  → Robot $i iniciado"
    sleep 0.3
done

echo "Lanzando $REPARTIDORES repartidores con make..."
for ((i=1; i<=REPARTIDORES; i++)); do
    make run-delivery &
    PIDS+=($!)
    echo "  → Repartidor $i iniciado"
    sleep 0.3
done

echo ""
echo "✅ Todos los procesos están corriendo en segundo plano."

# Manejar Ctrl+C para matar todo
trap ctrl_c INT
function ctrl_c() {
    echo ""
    echo "🛑 Terminando todos los procesos..."
    for pid in "${PIDS[@]}"; do
        kill $pid 2>/dev/null
    done
    echo "✅ Todos los procesos fueron finalizados."
    exit 0
}

wait