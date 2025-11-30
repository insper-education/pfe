#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Janeiro de 2024
"""

import logging

from django.db.models import Q

from projetos.models import Desconto
from projetos.support4 import get_objetivos_atuais_cache


# Get an instance of a logger
logger = logging.getLogger("django")


def get_objetivos(avaliacoes, ano, semestre):
    """Retorna objetivos de um conjunto de avaliações."""

    objetivos = get_objetivos_atuais_cache(ano=ano, semestre=semestre)
    
    if not objetivos: # Fallback: semestre sem objetivo
        return {}, None, None
    
    # Buscando todas as avaliações relevantes
    avaliacoes_lista = list(
        avaliacoes.filter(objetivo__in=objetivos)
        .select_related("avaliador", "objetivo")
        .order_by("objetivo", "avaliador", "-momento")
    )
    
    if not avaliacoes_lista:  # Fallback: avaliações sem objetivo
        avaliacoes_sem_obj = avaliacoes.filter(objetivo__isnull=True)
        if not avaliacoes_sem_obj.exists():
            return {}, None, None
        
        nota_total = 0.0
        contador = 0
        for aval in avaliacoes_sem_obj:
            if aval.nota:
                nota_total += float(aval.nota)
                contador += 1
        
        if contador:
            return {None: (nota_total/contador, 0.0)}, None, None
        else:
            return {}, None, None
    
    # organiza avaliações por objetivo
    lista_objetivos = {}
    avaliadores = set()
    siglas_vistas = set()
    
    # Dicionário para agrupar avaliações por objetivo
    avaliacoes_por_objetivo = {}
    for aval in avaliacoes_lista:
        if aval.objetivo not in avaliacoes_por_objetivo:
            avaliacoes_por_objetivo[aval.objetivo] = []
        avaliacoes_por_objetivo[aval.objetivo].append(aval)
    
    # Processa cada objetivo
    for objetivo in objetivos:
        avaliacoes_obj = avaliacoes_por_objetivo.get(objetivo, [])
        
        if not avaliacoes_obj:
            continue
        
        # Verifica duplicidade de siglas
        if objetivo.sigla in siglas_vistas:
            logger.error(f"Erro, dois objetivos no mesmo semestre com a mesma sigla! ano={ano} semestre={semestre} => {objetivo.sigla}")
        siglas_vistas.add(objetivo.sigla)
        
        lista_objetivos[objetivo] = {}
        avaliadores_vistos = set()
        
        # Processa avaliações (já ordenadas por avaliador, -momento)
        for aval in avaliacoes_obj:
            # Pega apenas a primeira avaliação de cada avaliador
            if aval.avaliador not in avaliadores_vistos:
                avaliadores_vistos.add(aval.avaliador)
                avaliadores.add(aval.avaliador)
                
                if aval.na or (aval.nota is None) or (aval.peso is None):
                    lista_objetivos[objetivo][aval.avaliador] = None
                else:
                    lista_objetivos[objetivo][aval.avaliador] = (float(aval.nota), float(aval.peso))
    
    if not lista_objetivos:  # Fallback: avaliações sem objetivo
        avaliacoes_sem_obj = avaliacoes.filter(objetivo__isnull=True)
        if not avaliacoes_sem_obj.exists():
            return {}, None, None
        
        nota_total = 0.0
        contador = 0
        for aval in avaliacoes_sem_obj:
            if aval.nota:
                nota_total += float(aval.nota)
                contador += 1
        
        if contador:
            return {None: (nota_total/contador, 0.0)}, None, None
        else:
            return {}, None, None
    
    # CALCULA MÉDIA POR OBJETIVO
    val_objetivos = {}
    pes_total = 0
    
    for obj, avaliacoes_dict in lista_objetivos.items():
        if not avaliacoes_dict:
            continue
        
        val = 0.0
        pes = 0.0
        count = 0
        
        for avaliador, dados in avaliacoes_dict.items():
            if dados is not None:
                count += 1
                val += dados[0]
                pes += dados[1]
                pes_total += dados[1]
        
        if count > 0:
            valor = val / float(count)
            peso = pes / float(count)
            val_objetivos[obj] = (valor, peso)
    
    return val_objetivos, pes_total, avaliadores





# def get_objetivos(avaliacoes, ano, semestre):
#     """Retorna objetivos de um conjunto de avaliações."""
#     lista_objetivos = {}
#     avaliadores = set()

#     objetivos = get_objetivos_atuais_cache(ano=ano, semestre=semestre)

#     for objetivo in objetivos:
#         avaliacoes_p_obj = avaliacoes.filter(objetivo=objetivo).order_by("avaliador", "-momento")
#         if avaliacoes_p_obj:
#             for objtmp in lista_objetivos:  # Se já existe um objetivo com a mesma sigla haverá um erro na média
#                 if objtmp.sigla == objetivo.sigla:
#                     logger.error(f"Erro, dois objetivos no mesmo semestre com a mesma sigla! ano={ano} semestre={semestre} => {objetivo.sigla}")
#             lista_objetivos[objetivo] = {}
#             for aval in avaliacoes_p_obj:
#                 if aval.avaliador not in lista_objetivos[objetivo]:  # Se não for o mesmo avaliador
#                     avaliadores.add(aval.avaliador)
#                     if aval.na or (aval.nota is None) or (aval.peso is None):
#                         lista_objetivos[objetivo][aval.avaliador] = None
#                     else:
#                         lista_objetivos[objetivo][aval.avaliador] = (float(aval.nota), float(aval.peso))
#                 # Senão é só uma avaliação de objetivo mais antiga (E IGNORAR)

#     if not lista_objetivos:
#         # Se não houver objetivos, verifica se há avaliações sem objetivo (USANDO PARA CHECKAR SE INVALIDA PROBATÓTIO)
#         nota = 0.0
#         contador = 0
#         avaliacoes_sem_obj = avaliacoes.filter(objetivo__isnull=True).order_by("avaliador", "-momento")
#         if avaliacoes_sem_obj:
#             for aval in avaliacoes_sem_obj:
#                 if aval.nota:
#                     nota += float(aval.nota)
#                     contador += 1
#                     # IGNORANDO PESO
#             if contador:
#                 return {None: (nota/contador, 0.0)}, None, None
#             else:
#                 return {}, None, None
#         else:  
#             return {}, None, None

#     # média por objetivo
#     val_objetivos = {}
#     pes_total = 0
#     for obj in lista_objetivos:  # Verificando cada objetivo de aprendizado identificado
#         val = 0.0
#         pes = 0.0
#         count = 0
#         if lista_objetivos[obj]:
#             for avali in lista_objetivos[obj]:
#                 if lista_objetivos[obj][avali]:
#                     count += 1
#                     val += lista_objetivos[obj][avali][0]
#                     pes += lista_objetivos[obj][avali][1]
#                     pes_total += lista_objetivos[obj][avali][1]
#             if count:
#                 valor = val/float(count)
#                 peso = pes/float(count)
#                 val_objetivos[obj] = (valor, peso)

#     return val_objetivos, pes_total, avaliadores


def get_descontos_alocacao(alocacao):
    """
    Recupera os descontos de uma alocação, somando as notas e coletando mensagens.
    Retorna (soma das notas, lista de mensagens).
    """
    descontos = Desconto.objects.filter(Q(alocacao=alocacao) | Q(projeto=alocacao.projeto)).select_related("alocacao", "projeto")
    nota_descontos = 0.0
    mensagens = []
    for desconto in descontos:
        if desconto.nota is not None:
            nota_descontos += float(desconto.nota)
            mensagens.append(desconto.get_mensagem())
        else:
            mensagens.append(f"Desconto sem nota definido: {desconto.get_mensagem()}")
    return nota_descontos, mensagens
