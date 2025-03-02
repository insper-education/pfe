#!/bin/bash

# Get the parameter
CHAVE=$1

# Read the content of file.chave.txt
CHAVE_FILE=$(cat chave.txt)

# Check if the parameter matches the content of file.chave.txt
if [ "$CHAVE" != "$CHAVE_FILE" ]; then
    echo "Chave inválida." >> lixo.txt
    exit 1
fi

USERNAME=$(whoami)
echo "Current user: $USERNAME" >> lixo.txt

USERNAME=$USER
echo "Current user2: $USERNAME" >> lixo.txt

echo "Parando todo os serviços..." >> lixo.txt
echo "parametros: $1" >> lixo.txt
