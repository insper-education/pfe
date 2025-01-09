#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Janeiro de 2024
"""

import logging

from projetos.models import ObjetivosDeAprendizagem


# Get an instance of a logger
logger = logging.getLogger("django")

def get_objetivos(self, avaliacoes):
    """Retorna objetivos de um conjunto de avaliações."""
    lista_objetivos = {}
    avaliadores = set()

    for objetivo in ObjetivosDeAprendizagem.objects.all():
        avaliacoes_p_obj = avaliacoes.filter(objetivo=objetivo).order_by("avaliador", "-momento")
        if avaliacoes_p_obj:
            for objtmp in lista_objetivos:  # Se já existe um objetivo com a mesma sigla haverá um erro na média
                if objtmp.sigla == objetivo.sigla:
                    logger.error(f"Erro, dois objetivos no mesmo semestre com a mesma sigla! {self} {objetivo.sigla}")
            lista_objetivos[objetivo] = {}
            for aval in avaliacoes_p_obj:
                if aval.avaliador not in lista_objetivos[objetivo]:  # Se não for o mesmo avaliador
                    avaliadores.add(aval.avaliador)
                    if aval.na or (aval.nota is None) or (aval.peso is None):
                        lista_objetivos[objetivo][aval.avaliador] = None
                    else:
                        lista_objetivos[objetivo][aval.avaliador] = (float(aval.nota), float(aval.peso))
                # Senão é só uma avaliação de objetivo mais antiga (E IGNORAR)

    if not lista_objetivos:
        return 0, None, None

    # média por objetivo
    val_objetivos = {}
    pes_total = 0
    for obj in lista_objetivos:  # Verificando cada objetivo de aprendizado identificado
        val = 0.0
        pes = 0.0
        count = 0
        if lista_objetivos[obj]:
            for avali in lista_objetivos[obj]:
                if lista_objetivos[obj][avali]:
                    count += 1
                    val += lista_objetivos[obj][avali][0]
                    pes += lista_objetivos[obj][avali][1]
                    pes_total += lista_objetivos[obj][avali][1]
            if count:
                valor = val/float(count)
                peso = pes/float(count)
                val_objetivos[obj] = (valor, peso)

    return val_objetivos, pes_total, avaliadores