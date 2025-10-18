#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 4 de Abril de 2024
"""

from decimal import InvalidOperation
from django import template
register = template.Library()

@register.filter
def negate(value):
    return not value

@register.filter(name="divide_by")
def divide_by(value, divisor):
    if value is None or divisor is None or divisor == 0:
        return 0
    try:
        return value / divisor
    except (ZeroDivisionError, InvalidOperation, TypeError):
        return 0