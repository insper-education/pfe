#!/bin/bash

# Script para reiniciar o servidor.
# Este script irá parar o serviços, baixar o código mais recente do Git e iniciar os serviços novamente.

source ~/pfe/env/bin/activate

if [ -z "$USER" ]; then
    if [ "$1" != "$(cat chave.txt)" ]; then
        echo "Chave inválida."
        exit 1
    fi
fi

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

if [ $? -ne 0 ]; then
    echo "Erro ao parar serviços."
    exit 1
fi

echo "Configurando diretório seguro para o Git..."
git config --add safe.directory /home/ubuntu/pfe

echo "Puxando últimas atualizações do Git..."
GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no" git pull https://github.com/insper-education/pfe.git

if [ $? -ne 0 ]; then
    echo "Erro ao atualizar."
    exit 1
fi

echo "Iniciando os serviços..."
echo "Preparando o arquivo de log..."
touch pfe.log
chown ubuntu.ubuntu pfe.log
chmod a+w pfe.log

echo "Iniciando o Celery..."
celery worker -A pfe -l info &
celery beat -A pfe -l info &

echo "Preparando o Django..."
python3 manage.py axes_reset
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --no-input

echo "Reiniciando o servidor Apache..."
systemctl restart apache2

if [ $? -ne 0 ]; then
    echo "Erro ao iniciar serviços."
    exit 1
fi

echo "Serviços reiniciados."