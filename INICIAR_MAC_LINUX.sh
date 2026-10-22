#!/bin/sh
set -eu
cd "$(dirname "$0")"
test -f data/operaciones_simuladas.csv || { echo 'Falta data/operaciones_simuladas.csv'; exit 1; }
docker compose up --build -d
docker compose ps
echo 'Abre http://127.0.0.1:8501 cuando el contenedor esté healthy.'
