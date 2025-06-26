#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 25 de Junho de 2025
"""

import datetime

from .models import ObjetivosDeAprendizagem

def get_objetivos_atuais(ano=None, semestre=None):
    
    objetivos = ObjetivosDeAprendizagem.objects.all()

    if ano and semestre:
        mes = 3 if semestre == 1 else 9
        data = datetime.datetime(ano, mes, 1)
        objetivos = objetivos.filter(data_inicial__lt=data)
        objetivos = objetivos.filter(data_final__gt=data) | objetivos.filter(data_final__isnull=True)

    else:
        # Só os objetivos atualmente em uso
        hoje = datetime.date.today()
        objetivos = objetivos.filter(data_final__gt=hoje) | objetivos.filter(data_final__isnull=True)


    objetivos = objetivos.order_by("ordem")

    return objetivos
