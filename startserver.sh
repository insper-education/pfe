#!/bin/bash
set -e  # Para o script se qualquer comando falhar

# Configurações
VENV_PATH="$HOME/pfe/env"
LOG_FILE="logs/pfe.log"
DJANGO_USER="ubuntu"
PROJECT_PATH="$HOME/pfe"
MANAGE="$PROJECT_PATH/manage.py"

# Configurações do UFW (Firewall)
sudo ufw allow 443
sudo ufw allow 22
sudo ufw enable

# Script para iniciar todos os serviços.
# Ativa o ambiente virtual, inicia os workers do Celery, o servidor Apache e executa os comandos de gerenciamento do Django.
# Também inicia o serviço PostgreSQL caso ele não esteja em execução.

echo "Ativando o virtual environment..."
source "$VENV_PATH/bin/activate"

# Descomente se precisar iniciar o PostgreSQL
# echo "Iniciando o PostgreSQL..."
# sudo systemctl start postgresql.service
# sudo systemctl enable postgresql.service

echo "Preparando o arquivo de log..."
touch "$LOG_FILE"
sudo chown $DJANGO_USER:$DJANGO_USER "$LOG_FILE"
sudo chmod 640 "$LOG_FILE"


echo "Iniciando o Celery..."
sudo -u $DJANGO_USER celery worker -A pfe -l info >> "$LOG_FILE" 2>&1 &
sudo -u $DJANGO_USER celery beat -A pfe -l info >> "$LOG_FILE" 2>&1 &
#rabbitmqctl purge_queue celery

echo "Preparando o Django..."
sudo -u $DJANGO_USER python3 "$MANAGE" axes_reset
sudo -u $DJANGO_USER python3 "$MANAGE" makemigrations
sudo -u $DJANGO_USER python3 "$MANAGE" migrate
sudo -u $DJANGO_USER python3 "$MANAGE" collectstatic --no-input


echo "Iniciando o servidor Apache..."
sudo systemctl start apache2
#sudo python3 manage.py runserver 0.0.0.0:80 &

echo "Todos os serviços iniciados."
#tail -f /var/log/apache2/error.log
#tail -f /var/log/apache2/access.log
