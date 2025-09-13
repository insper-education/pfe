#!/bin/bash
set -e  # Para o script se qualquer comando falhar

# Configurações
VENV_PATH="$HOME/pfe/env"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FOLDER="$SCRIPT_DIR/logs"

DJANGO_LOG="$LOG_FOLDER/django.log"
CELERY_WORKER_LOG="$LOG_FOLDER/celery_worker.log"
CELERY_BEAT_LOG="$LOG_FOLDER/celery_beat.log"

DJANGO_USER="ubuntu"
PROJECT_PATH="$HOME/pfe"
MANAGE="$PROJECT_PATH/manage.py"

# Configurações do UFW (Firewall) [rodar apenas na primeira vez]
# sudo ufw allow 443
# sudo ufw allow 22
# sudo ufw enable

# Script para iniciar todos os serviços.
# Ativa o ambiente virtual, inicia os workers do Celery, o servidor Apache e executa os comandos de gerenciamento do Django.
# Também inicia o serviço PostgreSQL caso ele não esteja em execução.

echo "Ativando o virtual environment..."
source "$VENV_PATH/bin/activate"

# Descomente se precisar iniciar o PostgreSQL
# echo "Iniciando o PostgreSQL..."
# sudo systemctl start postgresql.service
# sudo systemctl enable postgresql.service

echo "Preparando os arquivos de log..."
touch "$DJANGO_LOG" "$CELERY_WORKER_LOG" "$CELERY_BEAT_LOG"

sudo chown -R $DJANGO_USER:www-data "$LOG_FOLDER"
mkdir -p "$LOG_FOLDER"
sudo chmod 775 "$LOG_FOLDER"
sudo chown $DJANGO_USER:www-data "$DJANGO_LOG"
sudo chown $DJANGO_USER:www-data "$CELERY_WORKER_LOG"
sudo chown $DJANGO_USER:www-data "$CELERY_BEAT_LOG"
sudo chmod 664 "$DJANGO_LOG"
sudo chmod 664 "$CELERY_WORKER_LOG"
sudo chmod 664 "$CELERY_BEAT_LOG"
[ -L "$LOG_FOLDER/apache_error.log" ] || ln -s /var/log/apache2/error.log "$LOG_FOLDER/apache_error.log"
[ -L "$LOG_FOLDER/apache_access.log" ] || ln -s /var/log/apache2/access.log "$LOG_FOLDER/apache_access.log"


echo "Iniciando o Celery Worker..."
sudo -u $DJANGO_USER $VENV_PATH/bin/celery worker -A pfe -l info >> "$CELERY_WORKER_LOG" 2>&1 &
echo "Iniciando o Celery Beat..."
sudo -u $DJANGO_USER $VENV_PATH/bin/celery beat -A pfe -l info >> "$CELERY_BEAT_LOG" 2>&1 &
#rabbitmqctl purge_queue celery

echo "Preparando o Django..."
sudo -u $DJANGO_USER python3 "$MANAGE" axes_reset
sudo -u $DJANGO_USER python3 "$MANAGE" makemigrations
sudo -u $DJANGO_USER python3 "$MANAGE" migrate
sudo -u $DJANGO_USER python3 "$MANAGE" collectstatic --no-input


echo "Iniciando o servidor Apache..."
sudo a2enmod headers
sudo systemctl start apache2
#sudo python3 manage.py runserver 0.0.0.0:80 &

echo "Todos os serviços iniciados."
#tail -f /var/log/apache2/error.log
#tail -f /var/log/apache2/access.log
