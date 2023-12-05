#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 5 de Dezembro de 2023
"""

from django import template
register = template.Library()

@register.filter
def get_conexao(conexoes, parceiro):
    """Identifica o tipo de conexão."""
    return conexoes.filter(parceiro=parceiro).last()
