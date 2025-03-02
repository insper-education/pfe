#!/bin/bash

# Script para parar todos os serviços relacionados ao projeto.
# Interrompe os workers do Celery, o servidor de desenvolvimento do Django e o servidor Apache.
# Também interrompe o serviço PostgreSQL caso ele esteja em execução.


echo "Parando o Celery..."
pkill -9 -f 'celery worker'
pkill -9 -f 'celery beat'

timeout=10
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
    kill -9 $pids
fi

#echo "Parando Django..."
#pkill -f 'manage.py runserver'
#kill -9 $(pgrep -f manage.py)  # Alternativa

echo "Stopping Apache server..."
systemctl stop apache2

# Descomente se precisar parar o PostgreSQL
# echo "Parando PostgreSQL..."
# systemctl stop postgresql.service

echo "Todos os serviços parados."