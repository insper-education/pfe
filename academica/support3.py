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
from academica.support2 import get_objetivos

from projetos.models import Reprovacao, Avaliacao2, Banca, Evento
from projetos.support3 import get_notas_alocacao


# Get an instance of a logger
logger = logging.getLogger("django")


def em_probation(alocacao):
    """Retorna se em probation."""
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
                        val_objetivos, _, _ = get_objetivos(alocacao, paval)

                else:
                    val_objetivos, _, _ = get_objetivos(alocacao, paval)

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

def get_media_alocacao_i(alocacao):
    """Retorna média e peso final."""
    reprovacao = Reprovacao.objects.filter(alocacao=alocacao)
    if reprovacao:
        return {"media": reprovacao.last().nota, "pesos": 1}

    edicao = get_notas_alocacao(alocacao)

    nota_final = 0
    nota_individual = 0
    nota_grupo_inter = 0
    nota_grupo_final = 0
    peso_final = 0
    peso_individual = 0
    peso_grupo_inter = 0
    peso_grupo_final = 0
    for aval, nota, peso, _ in edicao:
        if aval is not None and nota is not None and peso is not None:
            peso_final += peso
            nota_final += nota * peso
            if aval in ("RII", "RFI", "API", "AFI"):
                peso_individual += peso
                nota_individual += nota * peso
            if aval in ("RIG", "APG", "RPL", "PPF"):
                peso_grupo_inter += peso
                nota_grupo_inter += nota * peso
            if aval in ("RFG", "AFG"):
                peso_grupo_final += peso
                nota_grupo_final += nota * peso
    peso_final = round(peso_final, 2)

    individual = None
    if peso_individual > 0:
        individual = nota_individual/peso_individual

    # Arredonda os valores finais para auxiliar do check de peso 100% e média 5.
    nota_final = round(nota_final, 6)
    peso_final = round(peso_final, 9)

    # Caso a nota individual seja menor que 5, a nota final é a menor das notas        
    if individual is not None and individual < 5:
        if individual < nota_final:
            nota_final = individual

    # Se a nota final permite passar, mas o estudante estiver em probation, a nota final é None
    if nota_final > 5.0 and em_probation(alocacao):
        probation = True
        nota_final = None
    else:
        probation = False

    return {
        "media": nota_final,
        "pesos": peso_final,
        "peso_grupo_inter": peso_grupo_inter,
        "nota_grupo_inter": nota_grupo_inter,
        "peso_grupo_final": peso_grupo_final,
        "nota_grupo_final": nota_grupo_final,
        "individual": individual,
        "probation": probation,
    }
