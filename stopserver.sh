#!/bin/bash

# Script para parar todos os serviços relacionados ao projeto.
# Interrompe os workers do Celery, o servidor de desenvolvimento do Django e o servidor Apache.
# Também interrompe o serviço PostgreSQL caso ele esteja em execução.


echo "Parando o Celery..."
CELERY_PATTERN='/home/ubuntu/pfe/env/bin/celery (worker|beat) -A pfe'
sudo pkill -TERM -u ubuntu -f "$CELERY_PATTERN" || true
for _ in $(seq 1 60); do
    sudo pgrep -u ubuntu -f "$CELERY_PATTERN" >/dev/null || break
    sleep 1
done
if sudo pgrep -u ubuntu -f "$CELERY_PATTERN" >/dev/null; then
    echo "Celery não encerrou em 60 segundos; forçando."
    sudo pkill -KILL -u ubuntu -f "$CELERY_PATTERN"
fi

timeout=30
elapsed=0
interval=1
while pgrep -f 'celery' > /dev/null; do
    if [ $elapsed -ge $timeout ]; then
        echo "Timeout para terminar os processos do Celery."
        break
    fi
    echo "Esperando os processos do Celery terminarem..."
    sleep $interval
    elapsed=$((elapsed + interval))
done
# Supostamente já foram mortos, mas por garantia
pids=$(pgrep -f 'celery')
if [ -n "$pids" ]; then
    sudo kill -9 $pids
fi

#echo "Parando Django..."
#sudo pkill -f 'manage.py runserver'
#sudo kill -9 $(pgrep -f manage.py)  # Alternativa

echo "Stopping Apache server..."
sudo systemctl stop apache2

# Descomente se precisar parar o PostgreSQL
# echo "Parando PostgreSQL..."
# sudo systemctl stop postgresql.service

echo "Todos os serviços parados."