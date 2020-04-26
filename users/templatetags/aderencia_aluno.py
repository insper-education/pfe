#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 29 de Novembro de 2019
"""

from django import template
register = template.Library()

@register.simple_tag
def mede_aderencia(estudante, proposta):
    """."""
    total = 0
    if proposta.areas_de_interesse:
        if estudante.inovacao_social == proposta.areas_de_interesse.inovacao_social:
            total += 1
        if estudante.ciencia_dos_dados == proposta.areas_de_interesse.ciencia_dos_dados:
            total += 1
        if estudante.modelagem_3D == proposta.areas_de_interesse.modelagem_3D:
            total += 1
        if estudante.manufatura == proposta.areas_de_interesse.manufatura:
            total += 1
        if estudante.resistencia_dos_materiais == proposta.areas_de_interesse.resistencia_dos_materiais:
            total += 1
        if estudante.modelagem_de_sistemas == proposta.areas_de_interesse.modelagem_de_sistemas:
            total += 1
        if estudante.controle_e_automacao == proposta.areas_de_interesse.controle_e_automacao:
            total += 1
        if estudante.termodinamica == proposta.areas_de_interesse.termodinamica:
            total += 1
        if estudante.fluidodinamica == proposta.areas_de_interesse.fluidodinamica:
            total += 1
        if estudante.eletronica_digital == proposta.areas_de_interesse.eletronica_digital:
            total += 1
        if estudante.programacao == proposta.areas_de_interesse.programacao:
            total += 1
        if estudante.inteligencia_artificial == proposta.areas_de_interesse.inteligencia_artificial:
            total += 1
        if estudante.banco_de_dados == proposta.areas_de_interesse.banco_de_dados:
            total += 1
        if estudante.computacao_em_nuvem == proposta.areas_de_interesse.computacao_em_nuvem:
            total += 1
        if estudante.visao_computacional == proposta.areas_de_interesse.visao_computacional:
            total += 1
        if estudante.computacao_de_alto_desempenho == proposta.areas_de_interesse.computacao_de_alto_desempenho:
            total += 1
        if estudante.robotica == proposta.areas_de_interesse.robotica:
            total += 1
        if estudante.realidade_virtual_aumentada == proposta.areas_de_interesse.realidade_virtual_aumentada:
            total += 1
        if estudante.protocolos_de_comunicacao == proposta.areas_de_interesse.protocolos_de_comunicacao:
            total += 1
        if estudante.eficiencia_energetica == proposta.areas_de_interesse.eficiencia_energetica:
            total += 1
        if estudante.administracao_economia_financas == proposta.areas_de_interesse.administracao_economia_financas:
            total += 1
    else:
        return "--"
    total *= 100/21
    return int(total)
