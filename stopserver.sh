#!/bin/bash

# Script para parar todos os serviços relacionados ao projeto.
# Interrompe os workers do Celery, o servidor de desenvolvimento do Django e o servidor Apache.
# Também interrompe o serviço PostgreSQL caso ele esteja em execução.


echo "Parando o Celery..."
sudo pkill -9 -f 'celery worker'
sudo pkill -9 -f 'celery beat'
while pgrep -f 'celery' > /dev/null; do
    echo "Esperando os processos do Celery terminarem..."
    sleep 1
done
sudo kill -9 $(pgrep -f celery)  # Supostamente já foram mortos, mas por garantia

#echo "Parando Django..."
#sudo pkill -f 'manage.py runserver'
#sudo kill -9 $(pgrep -f manage.py)  # Alternativa

echo "Stopping Apache server..."
sudo systemctl stop apache2

# Descomente se precisar parar o PostgreSQL
# echo "Parando PostgreSQL..."
# sudo systemctl stop postgresql.service

echo "Todos os serviços parados."