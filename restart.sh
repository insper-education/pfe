#!/bin/bash

# Script para reiniciar o servidor.
# Este script irá parar o serviços, baixar o código mais recente do Git e iniciar os serviços novamente.


echo "Parando todo os serviços..."
./stopserver.sh

if [ $? -ne 0 ]; then
    echo "Erro ao parar serviços."
    exit 1
fi

echo "Puxando últimas atualizações do Git..."
git pull

if [ $? -ne 0 ]; then
    echo "Erro ao atualizar."
    exit 1
fi

echo "Iniciando os serviços..."
./startserver.sh

if [ $? -ne 0 ]; then
    echo "Erro ao iniciar serviços."
    exit 1
fi

echo "Serviços reiniciados."