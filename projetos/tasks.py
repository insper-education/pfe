#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

import datetime
from celery import task

from .messages import email
from .models import Configuracao, Aviso

@task
def envia_aviso():
    """Gera um aviso por e-mail."""
    configuracao = Configuracao.objects.all().first()
    delta = (datetime.date.today() - configuracao.t0).days
    avisos = Aviso.objects.filter(delta=delta)
    for aviso in avisos:
        subject = 'Aviso: '+aviso.titulo
        recipient_list = ['pfeinsper@gmail.com', 'lpsoares@insper.edu.br',]
        if aviso.mensagem:
            message = aviso.mensagem
        else:
            message = "Mensagem não definida."
        verify = email(subject, recipient_list, message)
        if verify != 1:
            #print("Algum problema de conexão, contacte: lpsoares@insper.edu.br")
            pass
