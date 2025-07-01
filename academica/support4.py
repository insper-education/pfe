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


def get_banca_estudante(avaliacoes_banca, ano, semestre):
    """Retorna média final das bancas informadas."""
    val_objetivos, pes_total, avaliadores = get_objetivos(avaliacoes_banca, ano, semestre)

    media_local = 0.0
    peso_local = 0.0

    for valor, peso in val_objetivos.values():
        media_local += valor if pes_total == 0 else valor * peso
        peso_local += peso

    if val_objetivos:
        #peso_local = float(peso_local)
        if peso_local != 0:
            media_local /= peso_local
        else:
            media_local /= len(val_objetivos)
    else:
        peso_local = None

    return {
        "media": media_local,
        "peso": peso_local,
        "avaliadores": avaliadores,
        "objetivos": val_objetivos
    }


def get_notas_estudante(estudante, request=None, ano=None, semestre=None, checa_banca=True):
    """Recuper as notas do Estudante."""
    
    if ano and semestre:
        alocacoes = Alocacao.objects.filter(aluno=estudante.pk, projeto__ano=ano,projeto__semestre=semestre)
    else:
        alocacoes = Alocacao.objects.filter(aluno=estudante.pk)

    now = datetime.datetime.now()

    exames = Exame.objects.all().order_by("ordem")
    exames = exames.exclude(sigla="F")  # Exclui o exame de certificação Falconi
    
    edicao = {}  # dicionário para cada alocação do estudante
    for alocacao in alocacoes:
        
        notas = []  # iniciando uma lista de notas vazia

        for exame in exames:
            checa_b = checa_banca
            banca = None
            if exame.banca:
                if exame.grupo:  # Grupo - Intermediária/Final
                    banca = Banca.objects.filter(projeto=alocacao.projeto, composicao__exame__sigla=exame.sigla).last()
                else:  # Individual - Probation
                    banca = Banca.objects.filter(alocacao=alocacao, composicao__exame__sigla=exame.sigla).last()
            try:
                if exame.grupo:  # GRUPO
                    paval = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=exame)
                else:  # INDIVIDUAL
                    paval = Avaliacao2.objects.filter(alocacao=alocacao, exame=exame)

                if not paval:
                    continue 

                if exame.banca:
                    if banca:  # Banca
                        valido = True  # Verifica se todos avaliaram a pelo menos 24 horas atrás

                        # Verifica se já passou o evento de encerramento e assim liberar notas
                        evento_encerram = Evento.get_evento(sigla="EE", ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)

                        if evento_encerram:  # Não é banca probation e tem evento de encerramento
                            if exame.sigla != 'P': 
                                if now.date() > evento_encerram.endDate:  # Após o evento de encerramento liberar todas as notas
                                    checa_b = False
                        # else:  # Não tem evento de encerramento

                        # Verifica se já passou o semestre e assim liberar notas
                        if now.date() > datetime.date(alocacao.projeto.ano, 6 if alocacao.projeto.semestre == 1 else 12, 30):
                            checa_b = False

                        if checa_b:
                            if (request is None) or (not request.user.eh_prof_a):  # Se não for professor/administrador
                                for membro in banca.membros():
                                    avaliacao = paval.filter(avaliador=membro).last()
                                    if (not avaliacao) or (now - avaliacao.momento < datetime.timedelta(hours=24)):
                                        valido = False
                                        break

                        if valido:
                            banca_info = get_banca_estudante(paval, ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
                            notas.append({
                                "sigla": exame.sigla,
                                "nota": banca_info["media"],
                                "peso": banca_info["peso"]/100 if banca_info["peso"] else 0,
                                "nome": exame.titulo,
                                "banca": True,
                                "objetivos": banca_info["objetivos"]
                            })
                    else:
                        if exame.sigla == 'P':  # Probation sem banca (NÃO DEVERIA ACONTECER MAS SERVE PARA VALIDAR NOTAS)
                            pnp = paval.order_by("momento").last()   # USEI ISSO PARA PROJETOS ANTIGOS SEM REGISTRO DE BANCAS
                            if pnp:  # Se não houver avaliação, não adiciona nota
                                notas.append({
                                    "sigla": exame.sigla,
                                    "nota": float(pnp.nota) if pnp.nota else None,
                                    "peso": 0,
                                    "nome": exame.titulo,
                                    "banca": True,
                                    "objetivos": None
                                })
                        else:  # Exame sem banca (não deveria acontecer)
                            logger.error(f"Erro, exame com banca mas sem banca registrada: {exame.sigla} => {alocacao.projeto.get_titulo_org_periodo()}")



                if not exame.banca:  # Exame sem banca (SERIA QUASE COMO UM ELSE DO ANTERIOR)
                    if exame.periodo_para_rubricas!=0:  # Nota (não é só um Check)
                        banca_info = get_banca_estudante(paval, ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
                        notas.append({
                            "sigla": exame.sigla,
                            "nota": banca_info["media"],
                            "peso": banca_info["peso"]/100 if banca_info["peso"] else 0,
                            "nome": exame.titulo,
                            "banca": False,
                            "objetivos": banca_info["objetivos"]
                        })
                    else:  # Check
                        pnp = paval.order_by("momento").last()
                        notas.append({
                            "sigla": exame.sigla,
                            "nota": float(pnp.nota) if pnp.nota else None,
                            "peso": pnp.peso/100 if pnp.peso else 0,
                            "nome": exame.titulo,
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
