#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

import logging
import datetime

from django.core.exceptions import ValidationError

from academica.models import Exame
from academica.support2 import get_objetivos, get_descontos_alocacao

from projetos.models import Reprovacao, Avaliacao2, Banca, Evento
from projetos.support3 import get_notas_alocacao


# Get an instance of a logger
logger = logging.getLogger("django")


def em_probation(alocacao):
    """Retorna se alocação está em probation (mas não verifica se já reprovado, a menos que reprovado direto)."""
    reprovacao = Reprovacao.objects.filter(alocacao=alocacao).exists()
    if reprovacao:
        return False
    
    now = datetime.datetime.now()

    # Sigla, Nome, Grupo, Nota/Check, Banca
    pavaliacoes = [
        ("P", "Probation", False, True, "P"),
        ### CHECK SE JA FECHOU BANCA DE PROBATION PRIMEIRO ####
        ("RFG", "Relatório Final de Grupo", True, True, None),
        ("RFI", "Relatório Final Individual", False, True, None),
        ("BF", "Banca Final", True, True, "BF"),
        ("AFI", "Avaliação Final Individual", False, True, None),
        ("AFG", "Avaliação Final de Grupo", True, True, None),
    ]

    for pa in pavaliacoes:
        checa_b = True
        banca = None
        if pa[4]:  # Banca
            if pa[2]:  # Grupo - Intermediária/Final
                banca = Banca.objects.filter(projeto=alocacao.projeto, composicao__exame__sigla=pa[4]).last()
            else:  # Individual - Probation
                banca = Banca.objects.filter(alocacao=alocacao, composicao__exame__sigla=pa[4]).last()
        try:
            exame=Exame.objects.get(sigla=pa[0])
            if pa[2]:  # GRUPO
                paval = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=exame)
            else:  # INDIVIDUAL
                paval = Avaliacao2.objects.filter(alocacao=alocacao, exame=exame)

            if paval:
                val_objetivos = None
                if pa[4] and banca:  # Banca
                    valido = True  # Verifica se todos avaliaram a pelo menos 24 horas atrás

                    # Verifica se já passou o evento de encerramento e assim liberar notas
                    evento = Evento.get_evento(sigla="EE", ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
                    if evento:
                        # Após o evento de encerramento liberar todas as notas
                        if now.date() > evento.endDate:
                            checa_b = False

                    if checa_b:
                        for membro in banca.membros():
                            avaliacao = paval.filter(avaliador=membro).last()
                            if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=24)):
                                valido = False

                    if valido:
                        val_objetivos, _, _ = get_objetivos(paval, alocacao.projeto.ano, alocacao.projeto.semestre)

                else:
                    val_objetivos, _, _ = get_objetivos(paval, alocacao.projeto.ano, alocacao.projeto.semestre)

                if pa[0] == "P":
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
        if aval["sigla"] is not None and aval["nota"] is not None and aval["peso"] is not None:
            peso_final += aval["peso"]
            nota_final += aval["nota"] * aval["peso"]
            if aval["sigla"] in ("RII", "RFI", "API", "AFI"):
                peso_individual += aval["peso"]
                nota_individual += aval["nota"] * aval["peso"]
            if aval["sigla"] in ("RIG", "APG", "RPL", "PPF"):
                peso_grupo_inter += aval["peso"]
                nota_grupo_inter += aval["nota"] * aval["peso"]
            if aval["sigla"] in ("RFG", "AFG"):
                peso_grupo_final += aval["peso"]
                nota_grupo_final += aval["nota"] * aval["peso"]
            if aval["sigla"] in ("BI", "BF"):
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
