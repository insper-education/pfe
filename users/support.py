#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 2 de Outubro de 2020
"""

from django.utils import timezone

from projetos.models import Configuracao
#from .models import PFEUser, Aluno


def configuracao_estudante_vencida(estudante):
    """Retorna verdade se ainda em tempo de estudante atualizar dados."""

    configuracao = Configuracao.objects.get()

    ano = configuracao.ano
    semestre = configuracao.semestre

    vencido = False
    if estudante.anoPFE < ano:
        vencido = True
    elif estudante.anoPFE==ano and semestre==1:
        if estudante.semestrePFE==2:
            vencido = timezone.now() > configuracao.prazo
    elif estudante.anoPFE==ano and semestre==2:
        vencido = True
    elif estudante.anoPFE==ano+1:
        if estudante.semestrePFE==1:
            vencido = timezone.now() > configuracao.prazo

    return vencido

def adianta_semestre(ano, semestre):
    """ Adiciona um semestre no par ano, semestre."""

    if semestre == 1:
        semestre = 2
    else:
        ano += 1
        semestre = 1

    return ano, semestre
