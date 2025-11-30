#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 25 de Junho de 2025
"""

import datetime

from django.db.models import Q
from django.core.cache import cache

from .models import ObjetivosDeAprendizagem


# PARAR DE USAR ESSA FUNÇÃO, USAR get_objetivos_atuais_cache
def get_objetivos_atuais(ano=None, semestre=None):
    
    objetivos = ObjetivosDeAprendizagem.objects.all()

    if ano and semestre:
        mes = 3 if semestre == 1 else 9
        data = datetime.datetime(ano, mes, 1)
        objetivos = objetivos.filter(data_inicial__lt=data)
        objetivos = objetivos.filter(data_final__gt=data) | objetivos.filter(data_final__isnull=True)

    else:
        # Só os objetivos atualmente em uso
        hoje = datetime.date.today()
        objetivos = objetivos.filter(data_final__gt=hoje) | objetivos.filter(data_final__isnull=True)


    objetivos = objetivos.order_by("ordem")

    return objetivos


# Idealmente migrar todos para cá
def get_objetivos_atuais_cache(ano=None, semestre=None):
    """
    Retorna objetivos de aprendizagem filtrados por período.
    Usa Django cache para evitar queries repetidas.
    """
    
    # Criar chave de cache única
    if ano and semestre:
        cache_key = f"objetivos_{ano}_{semestre}"
    else:
        # Cache baseado na data atual (expira à meia-noite)
        hoje = datetime.date.today()
        cache_key = f"objetivos_atual_{hoje.isoformat()}"
    
    # Tenta buscar do cache
    objetivos = cache.get(cache_key)
    
    if objetivos is not None:
        return objetivos
    
    # Se não está no cache, busca do banco
    if ano and semestre:
        mes = 3 if semestre == 1 else 9
        data = datetime.datetime(ano, mes, 1)
        
        # Combina filtros em uma única query
        objetivos_qs = ObjetivosDeAprendizagem.objects.filter(
            Q(data_inicial__lt=data) & 
            (Q(data_final__gt=data) | Q(data_final__isnull=True))
        ).order_by("ordem")
    else:
        # Só os objetivos atualmente em uso
        hoje = datetime.date.today()
        
        objetivos_qs = ObjetivosDeAprendizagem.objects.filter(
            Q(data_final__gt=hoje) | Q(data_final__isnull=True)
        ).order_by("ordem")
    
    # Converte para lista e armazena no cache
    objetivos = list(objetivos_qs)
    
    timeout = 3600  # 1h
    cache.set(cache_key, objetivos, timeout)
    
    return objetivos
