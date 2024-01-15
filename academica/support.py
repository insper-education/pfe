#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Janeiro de 2024
"""

from datetime import date

from projetos.models import Documento, Evento

def filtra_composicoes(composicoes, ano, semestre):
    """Filtra composições."""
    composicoes = composicoes.exclude(data_final__year__lt=ano)
    composicoes = composicoes.exclude(data_inicial__year__gt=ano)
    
    if semestre == 1:
        composicoes = composicoes.exclude(data_inicial__year=ano, data_inicial__month__gt=6)
    else:
        composicoes = composicoes.exclude(data_final__year=ano, data_final__month__lt=8)

    return composicoes


def filtra_entregas(composicoes, projeto, user=None):
    entregas = []
    for comp in composicoes:

        if user and not comp.exame.grupo:
            documentos = Documento.objects.filter(tipo_documento=comp.tipo_documento, projeto=projeto, usuario=user)
        else:
            documentos = Documento.objects.filter(tipo_documento=comp.tipo_documento, projeto=projeto)
        
        if projeto.semestre == 1:
            evento = Evento.objects.filter(tipo_de_evento=comp.evento, endDate__year=projeto.ano, endDate__month__lt=7).last()
        else:          
            evento = Evento.objects.filter(tipo_de_evento=comp.evento, endDate__year=projeto.ano, endDate__month__gt=6).last()
        
        entregas.append([comp, documentos, evento])
        
    entregas = sorted(entregas, key=lambda t: (date.today() if t[2] is None else t[2].endDate))

    return entregas