#!/bin/bash

# Script para parar todos os serviços relacionados ao projeto.
# Interrompe os workers do Celery, o servidor de desenvolvimento do Django e o servidor Apache.
# Também interrompe o serviço PostgreSQL caso ele esteja em execução.


echo "Parando o Celery..."
sudo pkill -f 'celery worker'
sudo pkill -f 'celery beat'
#sudo kill -9 $(pgrep -f celery)  # Alternativa

#echo "Parando Django..."
#sudo pkill -f 'manage.py runserver'
#sudo kill -9 $(pgrep -f manage.py)  # Alternativa

echo "Stopping Apache server..."
sudo systemctl stop apache2

# Descomente se precisar parar o PostgreSQL
# echo "Parando PostgreSQL..."
# sudo systemctl stop postgresql.service

echo "Todos os serviços parados."