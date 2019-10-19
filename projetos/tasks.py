# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 18 de Outubro de 2019

from celery import task 
# from celery import shared_task 
# from celery.task.schedules import crontab
# from celery.decorators import periodic_task
# from celery.utils.log import get_task_logger

import datetime

from .messages import email

from .models import Configuracao, Aviso

@task(name='envia_aviso') 
def envia_aviso():
    configuracao = Configuracao.objects.all().first()
    delta=(datetime.date.today() - configuracao.t0).days
    avisos = Aviso.objects.filter(delta=delta)
    for a in avisos:
        print(a.titulo)
        subject = 'Aviso: '+a.titulo
        recipient_list = ['pfeinsper@gmail.com','lpsoares@insper.edu.br',]
        message = "Enviando Mensagem aqui"
        x = email(subject,recipient_list,message)
        if(x!=1):
            print("Algum problema de conexão, contacte: lpsoares@insper.edu.br")
        

