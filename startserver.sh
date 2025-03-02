#!/bin/bash

# Script para iniciar todos os serviços.
# Ativa o ambiente virtual, inicia os workers do Celery, o servidor Apache e executa os comandos de gerenciamento do Django.
# Também inicia o serviço PostgreSQL caso ele não esteja em execução.

echo "Ativando o virtual environment..."
source ~/pfe/env/bin/activate

# Descomente se precisar iniciar o PostgreSQL
# echo "Iniciando o PostgreSQL..."
# systemctl start postgresql.service
# systemctl enable postgresql.service

echo "Preparando o arquivo de log..."
touch pfe.log
chown ubuntu.ubuntu pfe.log
chmod a+w pfe.log

echo "Iniciando o Celery..."
celery worker -A pfe -l info &
celery beat -A pfe -l info &
#rabbitmqctl purge_queue celery

echo "Preparando o Django..."
python3 manage.py axes_reset
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --no-input

echo "Iniciando o servidor Apache..."
systemctl start apache2
#python3 manage.py runserver 0.0.0.0:80 &

echo "Todos os serviços iniciados."
#tail -f /var/log/apache2/error.log
#tail -f /var/log/apache2/access.log
