#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 2 de Outubro de 2020
"""

import datetime
import unicodedata

from django.db.models import F
from django.utils import timezone
#from django.shortcuts import get_object_or_404

#from .models import Aluno

from administracao.support import get_limite_propostas

from estudantes.models import Relato, Pares

from projetos.models import Configuracao, Certificado, Avaliacao2, Evento, Documento, Conexao
#from projetos.models import Projeto



def adianta_semestre(ano, semestre):
    """Adiciona um semestre no par ano, semestre."""
    if semestre == 1:
        semestre = 2
    else:
        ano += 1
        semestre = 1

    return ano, semestre


def retrocede_semestre(ano, semestre):
    """Retrocede um semestre no par ano, semestre."""
    if semestre == 2:
        semestre = 1
    else:
        ano -= 1
        semestre = 2

    return ano, semestre

def adianta_semestre_conf(configuracao):
    """Adiciona um semestre puxando ano e semestre da configuração."""
    ano = configuracao.ano
    semestre = configuracao.semestre
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

    if estudante.ano is None or estudante.semestre is None:
        return True
    
    if estudante.ano < ano:
        return True
    
    if estudante.ano == ano and semestre == 1:
        if estudante.semestre == 2:
            return timezone.now().date() > get_limite_propostas(configuracao)
    
    if estudante.ano == ano and semestre == 2:
        return True

    if estudante.ano == ano+1:
        if estudante.semestre == 1:
            return timezone.now().date() > get_limite_propostas(configuracao)

    return False

# Para avaliação de pares
def configuracao_pares_vencida(estudante, sigla, prazo=10):
    """Retorna verdade se ainda em tempo de estudante fazer avaliação de pares."""
    configuracao = Configuracao.objects.get()

    ano = configuracao.ano
    semestre = configuracao.semestre

    if estudante is not None and estudante.ano is not None and estudante.semestre is not None:
        if estudante.ano < ano:
            return True, None, None
        elif estudante.ano == ano and semestre == 2 and estudante.semestre == 1:
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
    """Função usada para recuperar todas as edições conforme objeto desejado."""
    
    if tipo in [Certificado, Avaliacao2, Documento, Conexao]:
        pares = tipo.objects.values(ano=F("projeto__ano"), semestre=F("projeto__semestre"))
    elif tipo == Relato:
        pares = tipo.objects.values(ano=F("alocacao__projeto__ano"), semestre=F("alocacao__projeto__semestre"))
    elif tipo == Pares:
        pares = tipo.objects.values(ano=F("alocacao_de__projeto__ano"), semestre=F("alocacao_de__projeto__semestre"))
    else:
        pares = tipo.objects.values("ano", "semestre")

    edicoes = []
    ano, semestre = None, None
    for pair in pares.distinct("ano", "semestre"):
        ano = pair.get("ano")
        semestre = pair.get("semestre")
        if ano == None or semestre == None:
            continue
        if anual and semestre == 1:
            edicoes.append(f"{ano}.1/2")
        edicoes.append(f"{ano}.{semestre}")

    return edicoes, ano, semestre


def normalize_string(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def ordena_nomes(queryset):
    # Ajusta nomes e ordena eles
    if not queryset:
        return []
    users = list(queryset)
    for user in users:
        user.normalized_first_name = normalize_string(user.first_name)
        user.normalized_last_name = normalize_string(user.last_name)
    return sorted(users, key=lambda u: (u.normalized_first_name, u.normalized_last_name))
