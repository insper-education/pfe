#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 27 de Setembro de 2020
"""

from django import template
register = template.Library()

@register.filter
def dict_key(d, k):
    """Retorna o valor do dicionário pela chave."""
    if k in d:
        return d[k]
    else:
        return None

@register.filter
def get_value(dictionary, key):
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def has_key(dictionary, key):
    if dictionary and isinstance(dictionary, dict):
        return key in dictionary
    return False

@register.filter
def to_range(value):
    return range(1, value + 1)


@register.filter
def has_forbidden_grade(allowed_grades, siglas):
    """Indica se uma faixa contém alguma menção acima do teto orientado."""
    if not allowed_grades:
        return False
    return any(
        (sigla.get("letra") if isinstance(sigla, dict) else sigla.letra) not in allowed_grades
        for sigla in siglas
    )
