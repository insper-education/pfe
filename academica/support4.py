#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 9 de Janeiro de 2025
"""

import logging
import datetime

from django.core.exceptions import ValidationError

from .models import Exame

from .support2 import get_objetivos

from projetos.models import Avaliacao2, Banca, Evento

from users.models import Alocacao


# Get an instance of a logger
logger = logging.getLogger("django")


def get_banca_estudante(estudante, avaliacoes_banca):
    """Retorna média final das bancas informadas."""
    val_objetivos, pes_total, avaliadores = get_objetivos(estudante, avaliacoes_banca)

    # if not val_objetivos:
    #     return 0, None, None

    # média dos objetivos
    media_local = 0.0
    peso_local = 0.0
    for obj in val_objetivos:
        if pes_total == 0:  # Não pesa na nota final
            media_local += val_objetivos[obj][0]
        else:
            media_local += val_objetivos[obj][0]*val_objetivos[obj][1]
        peso_local += val_objetivos[obj][1]

    if val_objetivos:
        peso_local = float(peso_local)
        if peso_local != 0:
            media_local = float(media_local)/peso_local
        else:
            media_local = float(media_local)/float(len(val_objetivos))
    else:
        peso_local = None

    #return media_local, peso_local, avaliadores
    return {
        "media": media_local,
        "peso": peso_local,
        "avaliadores": avaliadores,
        "objetivos": val_objetivos
    }


def get_notas_estudante(estudante, request=None, ano=None, semestre=None, checa_banca=True):
    """Recuper as notas do Estudante."""
    edicao = {}  # dicionário para cada alocação do estudante

    if ano and semestre:
        alocacoes = Alocacao.objects.filter(aluno=estudante.pk, projeto__ano=ano,projeto__semestre=semestre)
    else:
        alocacoes = Alocacao.objects.filter(aluno=estudante.pk)

    now = datetime.datetime.now()

    # Sigla, Nome, Grupo, Nota/Check, Banca
    pavaliacoes = [
        ("RP", "Relatório Preliminar", True, False, None),
        ("RII", "Relatório Intermediário Individual", False, True, None),
        ("RIG", "Relatório Intermediário de Grupo", True, True, None),
        ("BI", "Banca Intermediária", True, True, "BI"),
        ("RFG", "Relatório Final de Grupo", True, True, None),
        ("RFI", "Relatório Final Individual", False, True, None),
        ("BF", "Banca Final", True, True, "BF"),
        ("P", "Probation", False, True, "P"),
        # ABAIXO NÃO MAIS USADAS, FORAM USADAS QUANDO AINDA EM DOIS SEMESTRES
        ("PPF", "Planejamento Primeira Fase", True, False, None),
        ("API", "Avaliação Parcial Individual", False, True, None),
        ("AFI", "Avaliação Final Individual", False, True, None),
        ("APG", "Avaliação Parcial de Grupo", True, True, None),
        ("AFG", "Avaliação Final de Grupo", True, True, None),
        # A principio não mostra aqui as notas da certificação Falconi
    ]

    for alocacao in alocacoes:
        
        notas = []  # iniciando uma lista de notas vazia

        for pa in pavaliacoes:
            checa_b = checa_banca
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
                    if pa[4] and banca:  # Banca
                        valido = True  # Verifica se todos avaliaram a pelo menos 24 horas atrás

                        # Verifica se já passou o evento de encerramento e assim liberar notas
                        evento = Evento.get_evento(sigla="EE", ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
                        if pa[4] != "F" and  evento:  # Não é banca probation e tem evento de encerramento
                            # Após o evento de encerramento liberar todas as notas
                            if now.date() > evento.endDate:
                                checa_b = False

                        if checa_b:

                            if (request is None) or (request.user.tipo_de_usuario not in [2,4]):  # Se não for professor/administrador
                                for membro in banca.membros():
                                    avaliacao = paval.filter(avaliador=membro).last()
                                    if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=24)):
                                        valido = False

                        if valido:
                            #pnota, ppeso, _ = get_banca_estudante(estudante, paval)
                            banca_info = get_banca_estudante(estudante, paval)
                            #notas.append((pa[0], pnota, ppeso/100 if ppeso else 0, pa[1]))
                            notas.append({
                                "sigla": pa[0],
                                "nota": banca_info["media"],
                                "peso": banca_info["peso"]/100 if banca_info["peso"] else 0,
                                "nome": pa[1],
                                "banca": True,
                                "objetivos": banca_info["objetivos"]
                            })

                    else:
                        if pa[3]:  # Nota
                            #pnota, ppeso, _ = get_banca_estudante(estudante, paval)
                            banca_info = get_banca_estudante(estudante, paval)
                            #notas.append((pa[0], pnota, ppeso/100 if ppeso else 0, pa[1]))
                            notas.append({
                                "sigla": pa[0],
                                "nota": banca_info["media"],
                                "peso": banca_info["peso"]/100 if banca_info["peso"] else 0,
                                "nome": pa[1],
                                "banca": False,
                                "objetivos": banca_info["objetivos"]
                            })
                        else:  # Check
                            pnp = paval.order_by("momento").last()
                            #notas.append((pa[0], float(pnp.nota) if pnp.nota else None, pnp.peso/100 if pnp.peso else 0, pa[1]))
                            notas.append({
                                "sigla": pa[0],
                                "nota": float(pnp.nota) if pnp.nota else None,
                                "peso": pnp.peso/100 if pnp.peso else 0,
                                "nome": pa[1],
                                "banca": False,
                                "objetivos": None
                            })

            except Exame.DoesNotExist:
                raise ValidationError("<h2>Erro ao identificar tipos de avaliações!</h2>")

        key = f"{alocacao.projeto.ano}.{alocacao.projeto.semestre}"
        if key in edicao:
            logger.error("Erro, duas alocações no mesmo semestre! " + estudante.user.get_full_name() + " " + key)
        edicao[key] = notas

    return edicao
