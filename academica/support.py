#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Janeiro de 2024
"""

from datetime import date

from projetos.models import Documento, Evento, Avaliacao2, Observacao
from users.models import Alocacao

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
    for composicao in composicoes:

        if user and not composicao.exame.grupo:
            documentos = Documento.objects.filter(tipo_documento=composicao.tipo_documento, projeto=projeto, usuario=user)
        else:
            documentos = Documento.objects.filter(tipo_documento=composicao.tipo_documento, projeto=projeto)
        
        if projeto.semestre == 1:
            evento = Evento.objects.filter(tipo_de_evento=composicao.evento, endDate__year=projeto.ano, endDate__month__lt=7).last()
        else:          
            evento = Evento.objects.filter(tipo_de_evento=composicao.evento, endDate__year=projeto.ano, endDate__month__gt=6).last()
        
        if composicao.exame.grupo:
            avaliacoes = Avaliacao2.objects.filter(projeto=projeto, 
                                                exame=composicao.exame, 
                                                avaliador=projeto.orientador.user
                                                )
        else:
            if not user:  # Não deveria acontecer
                alocacao = None
            else:
                alocacao = Alocacao.objects.get(projeto=projeto, aluno=user.aluno)
            avaliacoes = Avaliacao2.objects.filter(projeto=projeto, 
                                                exame=composicao.exame, 
                                                avaliador=projeto.orientador.user,
                                                alocacao=alocacao
                                                )
        nota = 0
        if avaliacoes:
            peso = 0
            for avaliacao in avaliacoes:
                if avaliacao.peso and avaliacao.peso > 0:
                    nota += float(avaliacao.nota)*float(avaliacao.peso)
                    peso += float(avaliacao.peso)
            if peso > 0:
                nota = nota/peso
            else:
                nota = 0
        

        if composicao.exame.grupo:
            observacao = Observacao.objects.filter(projeto=projeto,
                                                    exame=composicao.exame,
                                                    avaliador=projeto.orientador.user
                                                ).last()
        else:
            if not user:  # Não deveria acontecer
                alocacao = None
            else:
                alocacao = Alocacao.objects.get(projeto=projeto, aluno=user.aluno)
            observacao = Observacao.objects.filter(projeto=projeto,
                                                    exame=composicao.exame,
                                                    avaliador=projeto.orientador.user,
                                                    alocacao=alocacao
                                                ).last()

            
        entregas.append({"composicao": composicao, 
                         "documentos": documentos, 
                         "evento": evento, 
                         "avaliacoes": avaliacoes,
                         "nota": nota,
                         "observacao": observacao,
                         })
        
        
    entregas = sorted(entregas, key=lambda t: (date.today() if t["evento"] is None else t["evento"].endDate))

    return entregas