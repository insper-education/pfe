#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

import logging
import datetime

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from academica.models import Exame, Composicao

from academica.support2 import get_objetivos, get_descontos_alocacao
from academica.support5 import filtra_composicoes

from projetos.models import Reprovacao, Avaliacao2, Banca, Evento, Configuracao
from projetos.support3 import get_notas_alocacao


# Get an instance of a logger
logger = logging.getLogger("django")


def em_probation(alocacao):
    """Retorna se alocação está em probatório (mas não verifica se já reprovado, a menos que reprovado direto)."""
    reprovacao = Reprovacao.objects.filter(alocacao=alocacao).exists()
    if reprovacao:
        return False
    
    configuracao = get_object_or_404(Configuracao)
    if alocacao.projeto.ano != configuracao.ano or alocacao.projeto.semestre != configuracao.semestre:
        return False  # Só verifica probation para o semestre atual

    now = datetime.datetime.now()

    composicoes = filtra_composicoes(Composicao.objects.all(), alocacao.projeto.ano, alocacao.projeto.semestre)
    composicoes = composicoes.filter(exame__final=True, pesos__isnull=False).distinct().order_by("-exame__ordem")
    for composicao in composicoes:
        checa_b = True
        banca = None
        if composicao.exame.banca or composicao.exame.sigla == "P":  # Banca
            if composicao.exame.grupo:  # Grupo - Intermediária/Final
                banca = Banca.objects.filter(projeto=alocacao.projeto, composicao__exame__sigla=composicao.exame.sigla).last()
            else:  # Individual - Probation
                banca = Banca.objects.filter(alocacao=alocacao, composicao__exame__sigla=composicao.exame.sigla).last()
        try:
            exame=Exame.objects.get(sigla=composicao.exame.sigla)
            if composicao.exame.grupo:  # GRUPO
                paval = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=exame)
            else:  # INDIVIDUAL
                paval = Avaliacao2.objects.filter(alocacao=alocacao, exame=exame)

            if paval:
                val_objetivos = None
                if (composicao.exame.banca or composicao.exame.sigla == "P") and banca:  # Banca
                    prazo = 2 if composicao.exame.sigla == "P" else 24  # Horas para liberar notas de probation ou normais
                    valido = True  # Verifica se todos avaliaram a pelo menos PRAZO horas atrás

                    # Verifica se já passou o evento de encerramento e assim liberar notas
                    evento = Evento.get_evento(sigla="EE", ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
                    if evento:
                        # Após o evento de encerramento liberar todas as notas
                        if now.date() > evento.endDate:
                            checa_b = False

                    if checa_b:
                        for membro in banca.membros():
                            avaliacao = paval.filter(avaliador=membro).last()
                            if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=prazo)):
                                valido = False

                    if valido:
                        val_objetivos, _, _ = get_objetivos(paval, alocacao.projeto.ano, alocacao.projeto.semestre)

                else:
                    val_objetivos, _, _ = get_objetivos(paval, alocacao.projeto.ano, alocacao.projeto.semestre)

                if composicao.exame.sigla == "P":
                    if val_objetivos:
                        for obj in val_objetivos:
                            if val_objetivos[obj][0] < 5:
                                return True # Se tiver algum objetivo com nota menor que 5 mantem em probation
                        return False  # Se não tiver nenhum objetivo com nota menor que 5 tudo OK com probation

                if val_objetivos:
                    for obj in val_objetivos:
                        if val_objetivos[obj][0] < 5:
                            return True

        except Exame.DoesNotExist:
            raise ValidationError("<h2>Erro ao identificar tipos de avaliações!</h2>")

    return False


def probations(alocacoes, request=None):
    """Retorna se alguma das alocações está em probation (verifica se já reprovado)."""
    for alocacao in alocacoes:
        probatorio = get_media_alocacao_i(alocacao, request=request)["probation"]
        if probatorio:
            return True
    return False


def get_media_alocacao_i(alocacao, request=None):
    """Retorna média e peso final."""
    edicao = get_notas_alocacao(alocacao, request=request)

    nota_final = 0
    nota_individual = 0
    nota_grupo_inter = 0
    nota_grupo_final = 0
    nota_bancas = 0
    peso_final = 0
    peso_individual = 0
    peso_grupo_inter = 0
    peso_grupo_final = 0
    peso_bancas = 0
    nota_descontos = 0
    
    for aval in edicao:
        if aval["exame"].sigla is not None and aval["nota"] is not None and aval["peso"] is not None:
            peso_final += aval["peso"]
            nota_final += aval["nota"] * aval["peso"]
            if not aval["exame"].grupo:
                peso_individual += aval["peso"]
                nota_individual += aval["nota"] * aval["peso"]
            if aval["exame"].grupo and not aval["exame"].final:
                peso_grupo_inter += aval["peso"]
                nota_grupo_inter += aval["nota"] * aval["peso"]
            if aval["exame"].grupo and aval["exame"].final:
                peso_grupo_final += aval["peso"]
                nota_grupo_final += aval["nota"] * aval["peso"]
            if aval["exame"].banca and aval["exame"].sigla != "P":
                peso_bancas += aval["peso"]
                nota_bancas += aval["nota"] * aval["peso"]

    peso_final = round(peso_final, 2)

    individual = None
    if peso_individual > 0:
        individual = nota_individual/peso_individual

    # Recupera os descontos e aplica na nota final
    nota_descontos, _ = get_descontos_alocacao(alocacao)

    # Media parcial (com os pesos disponíveis) antes dos descontos
    media_parcial = nota_final / peso_final if peso_final > 0 else 0
    
    nota_final -= nota_descontos
    if nota_final < 0:
        nota_final = 0

    # Arredonda os valores finais para auxiliar do check de peso 100% e média 5.
    nota_final = round(nota_final, 6)
    peso_final = round(peso_final, 9)

    
    if alocacao.projeto.ano > 2021:  # A partir de 2022, a nota final é a menor das notas individuais
        if individual is not None and individual < 5:  # Caso a nota individual seja menor que 5, a nota final é a menor das notas
            if individual < nota_final:
                nota_final = individual

    # Se a nota final permite passar, mas o estudante estiver em probation, a nota não deveria ser visível para o estudante.
    if nota_final >= 5.0 and em_probation(alocacao):
        probation = True
    else:
        probation = False

    media_grupo = 0
    pesos_grupo = 0
    if peso_grupo_inter > 0:
        media_grupo += nota_grupo_inter
        pesos_grupo += peso_grupo_inter
    if peso_grupo_final > 0:
        media_grupo += nota_grupo_final
        pesos_grupo += peso_grupo_final
    if peso_bancas > 0:
        media_grupo += nota_bancas
        pesos_grupo += peso_bancas
    if pesos_grupo > 0:
        media_grupo /= pesos_grupo

    # Ver se teve nota de reprovação e ajustar (não colocar antes para não interferir nos outros cálculos)
    reprovacao = Reprovacao.objects.filter(alocacao=alocacao)
    if reprovacao:
        nota_final = reprovacao.last().nota
        peso_final = 1

    return {
        "media": nota_final,
        "pesos": peso_final,
        "peso_grupo_inter": peso_grupo_inter,
        "nota_grupo_inter": nota_grupo_inter,
        "peso_grupo_final": peso_grupo_final,
        "nota_grupo_final": nota_grupo_final,
        "peso_bancas": peso_bancas,
        "nota_bancas": nota_bancas,
        "individual": individual,
        "media_grupo": media_grupo,
        "probation": probation,
        "descontos": nota_descontos,
        "media_parcial": media_parcial,
    }
