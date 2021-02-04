#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 2 de Outubro de 2020
"""

from django.utils import timezone

from projetos.models import Configuracao, Certificado
from .models import Aluno


def adianta_semestre(ano, semestre):
    """ Adiciona um semestre no par ano, semestre."""

    if semestre == 1:
        semestre = 2
    else:
        ano += 1
        semestre = 1

    return ano, semestre


def configuracao_estudante_vencida(estudante):
    """Retorna verdade se ainda em tempo de estudante atualizar dados."""

    configuracao = Configuracao.objects.get()

    ano = configuracao.ano
    semestre = configuracao.semestre

    vencido = False
    if estudante.anoPFE < ano:
        vencido = True
    elif estudante.anoPFE == ano and semestre == 1:
        if estudante.semestrePFE == 2:
            vencido = timezone.now() > configuracao.prazo
    elif estudante.anoPFE == ano and semestre == 2:
        vencido = True
    elif estudante.anoPFE == ano+1:
        if estudante.semestrePFE == 1:
            vencido = timezone.now() > configuracao.prazo

    return vencido


def get_edicoes(tipo):
    """Função usada para recuperar todas as edições de 2018.2 até hoje."""

    edicoes = []
    semestre_tmp = 2
    ano_tmp = 2018
    while True:
        existe = False
        if tipo == Certificado:
            if tipo.objects.filter(projeto__ano=ano_tmp, projeto__semestre=semestre_tmp).exists():
                existe = True
        if tipo == Aluno:
            if tipo.objects.filter(anoPFE=ano_tmp, semestrePFE=semestre_tmp).exists():
                existe = True
        else:
            if tipo.objects.filter(ano=ano_tmp, semestre=semestre_tmp).exists():
                existe = True

        if existe:
            ano = ano_tmp
            semestre = semestre_tmp
            edicoes.append(str(ano)+"."+str(semestre))
        else:
            break
        if semestre_tmp == 1:
            semestre_tmp += 1
        else:
            ano_tmp += 1
            semestre_tmp = 1

    return (edicoes, ano, semestre)
