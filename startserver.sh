#!/bin/bash

# Script para iniciar todos os serviços.
# Ativa o ambiente virtual, inicia os workers do Celery, o servidor Apache e executa os comandos de gerenciamento do Django.
# Também inicia o serviço PostgreSQL caso ele não esteja em execução.

echo "Ativando o virtual environment..."
source ~/pfe/env/bin/activate

# Descomente se precisar iniciar o PostgreSQL
# echo "Iniciando o PostgreSQL..."
# sudo systemctl start postgresql.service
# sudo systemctl enable postgresql.service

echo "Preparando o arquivo de log..."
touch pfe.log
sudo chown ubuntu.ubuntu pfe.log
sudo chmod a+w pfe.log

echo "Iniciando o Celery..."
celery -A pfe worker -l info &
celery -A pfe beat -l info &
#rabbitmqctl purge_queue celery

echo "Preparando o Django..."
sudo python3 manage.py axes_reset
sudo python3 manage.py makemigrations
sudo python3 manage.py migrate
sudo python3 manage.py collectstatic --no-input

echo "Iniciando o servidor Apache..."
sudo systemctl start apache2
#sudo python3 manage.py runserver 0.0.0.0:80 &

echo "Todos os serviços iniciados."
#tail -f /var/log/apache2/error.log
#tail -f /var/log/apache2/access.log
