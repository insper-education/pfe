#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 29 de Novembro de 2019
"""

from django import template
register = template.Library()

@register.simple_tag
def mede_aderencia(estudante, projeto):
    """."""
    total = 0
    if projeto.areas_de_interesse:
        if estudante.inovacao_social == projeto.areas_de_interesse.inovacao_social:
            total += 1
        if estudante.ciencia_dos_dados == projeto.areas_de_interesse.ciencia_dos_dados:
            total += 1
        if estudante.modelagem_3D == projeto.areas_de_interesse.modelagem_3D:
            total += 1
        if estudante.manufatura == projeto.areas_de_interesse.manufatura:
            total += 1
        if estudante.resistencia_dos_materiais == projeto.areas_de_interesse.resistencia_dos_materiais:
            total += 1
        if estudante.modelagem_de_sistemas == projeto.areas_de_interesse.modelagem_de_sistemas:
            total += 1
        if estudante.controle_e_automacao == projeto.areas_de_interesse.controle_e_automacao:
            total += 1
        if estudante.termodinamica == projeto.areas_de_interesse.termodinamica:
            total += 1
        if estudante.fluidodinamica == projeto.areas_de_interesse.fluidodinamica:
            total += 1
        if estudante.eletronica_digital == projeto.areas_de_interesse.eletronica_digital:
            total += 1
        if estudante.programacao == projeto.areas_de_interesse.programacao:
            total += 1
        if estudante.inteligencia_artificial == projeto.areas_de_interesse.inteligencia_artificial:
            total += 1
        if estudante.banco_de_dados == projeto.areas_de_interesse.banco_de_dados:
            total += 1
        if estudante.computacao_em_nuvem == projeto.areas_de_interesse.computacao_em_nuvem:
            total += 1
        if estudante.visao_computacional == projeto.areas_de_interesse.visao_computacional:
            total += 1
        if estudante.computacao_de_alto_desempenho == projeto.areas_de_interesse.computacao_de_alto_desempenho:
            total += 1
        if estudante.robotica == projeto.areas_de_interesse.robotica:
            total += 1
        if estudante.realidade_virtual_aumentada == projeto.areas_de_interesse.realidade_virtual_aumentada:
            total += 1
        if estudante.protocolos_de_comunicacao == projeto.areas_de_interesse.protocolos_de_comunicacao:
            total += 1
        if estudante.eficiencia_energetica == projeto.areas_de_interesse.eficiencia_energetica:
            total += 1
        if estudante.administracao_economia_financas == projeto.areas_de_interesse.administracao_economia_financas:
            total += 1
    else:
        return "--"
    total *= 100/21
    return int(total)