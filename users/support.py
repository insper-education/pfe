#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 2 de Outubro de 2020
"""

import datetime
import unicodedata
from django.utils import timezone
from django.shortcuts import get_object_or_404

from projetos.models import Configuracao, Certificado, Avaliacao2, Evento, Projeto, Documento, Conexao
from .models import Aluno
from estudantes.models import Relato, Pares

from administracao.support import get_limite_propostas


def adianta_semestre(ano, semestre):
    """Adiciona um semestre no par ano, semestre."""
    if semestre == 1:
        semestre = 2
    else:
        ano += 1
        semestre = 1

    return ano, semestre


def retrocede_semestre(ano, semestre):
    """Adiciona um semestre no par ano, semestre."""
    if semestre == 2:
        semestre = 1
    else:
        ano -= 1
        semestre = 2

    return ano, semestre

def adianta_semestre_conf(configiuracao):
    """Adiciona um semestre puxando ano e semestre da configuração."""
    ano = configiuracao.ano
    semestre = configiuracao.semestre
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

    if estudante.anoPFE is None or estudante.semestrePFE is None:
        return True
    
    if estudante.anoPFE < ano:
        return True
    
    if estudante.anoPFE == ano and semestre == 1:
        if estudante.semestrePFE == 2:
            return timezone.now().date() > get_limite_propostas(configuracao)
    
    if estudante.anoPFE == ano and semestre == 2:
        return True

    if estudante.anoPFE == ano+1:
        if estudante.semestrePFE == 1:
            return timezone.now().date() > get_limite_propostas(configuracao)

    return False

# Para avaliação de pares
def configuracao_pares_vencida(estudante, sigla, prazo=10):
    """Retorna verdade se ainda em tempo de estudante fazer avaliação de pares."""
    configuracao = Configuracao.objects.get()

    ano = configuracao.ano
    semestre = configuracao.semestre

    if estudante is not None and estudante.anoPFE is not None and estudante.semestrePFE is not None:
        if estudante.anoPFE < ano:
            return True, None, None
        elif estudante.anoPFE == ano and semestre == 2 and estudante.semestrePFE == 1:
            return True, None, None
    
    hoje = datetime.date.today()
    delta = datetime.timedelta(days=prazo)
    evento = Evento.objects.filter(tipo_evento__sigla=sigla, startDate__gte=hoje, startDate__lt=hoje+delta).last()

    if not evento:
        return True, None, None
    
    inicio = evento.startDate-delta
    fim = evento.startDate
    return False, inicio, fim

def get_edicoes(tipo, anual=False):
    """Função usada para recuperar todas as edições de 2018.2 até hoje."""
    edicoes = []
    semestre_tmp = 2
    ano_tmp = 2018

    configuracao = get_object_or_404(Configuracao)
    atual = configuracao.ano

    while True:
        existe = False
        if tipo == Certificado:
            if tipo.objects.filter(projeto__ano=ano_tmp, projeto__semestre=semestre_tmp).exists():
                existe = True
        elif tipo == Aluno:
            if tipo.objects.filter(anoPFE=ano_tmp, semestrePFE=semestre_tmp).exists():
                existe = True
        elif tipo == Avaliacao2:
            if tipo.objects.filter(projeto__ano=ano_tmp, projeto__semestre=semestre_tmp).exists():
                existe = True
        elif tipo == Documento:
            if tipo.objects.filter(projeto__ano=ano_tmp, projeto__semestre=semestre_tmp).exists():
                existe = True
        elif tipo == Conexao:
            if tipo.objects.filter(projeto__ano=ano_tmp, projeto__semestre=semestre_tmp).exists():
                existe = True
        elif tipo == Relato:  # Relato no sistema do Capstone só começaram a ser feitos em 2022.1
            if ano_tmp < 2022:
                ano_tmp = 2022
                semestre_tmp = 1
            if Projeto.objects.filter(ano=ano_tmp, semestre=semestre_tmp).exists():
                existe = True
        elif tipo == Pares:  # Relato no sistema do Capstone só começaram a ser feitos em 2022.1
            if ano_tmp < 2023:
                ano_tmp = 2023
                semestre_tmp = 1
            if Projeto.objects.filter(ano=ano_tmp, semestre=semestre_tmp).exists():
                existe = True
        else:
            if tipo.objects.filter(ano=ano_tmp, semestre=semestre_tmp).exists():
                existe = True

        if anual and semestre_tmp == 1:
            edicoes.append(str(ano_tmp)+".1/2")

        if existe:
            ano = ano_tmp
            semestre = semestre_tmp
            edicoes.append(str(ano)+"."+str(semestre))
        else:
            if ano_tmp > atual:
                break

        if semestre_tmp == 1:
            semestre_tmp = 2
        else:
            ano_tmp += 1
            semestre_tmp = 1

    return (edicoes, ano, semestre)


def normalize_string(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')


def ordena_nomes(queryset):
    # Ajusta nomes e ordena eles
    if not queryset:
        return []
    users = list(queryset)
    for user in users:
        user.normalized_first_name = normalize_string(user.first_name)
        user.normalized_last_name = normalize_string(user.last_name)
    return sorted(users, key=lambda u: (u.normalized_first_name, u.normalized_last_name))
