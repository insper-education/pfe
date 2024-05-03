#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 3 de Maio de 2024
"""

from django import template
register = template.Library()

@register.filter
def clarear(value):
    # Recebe um valor hexadecimal e retorna um valor hexadecimal mais claro
    nova_cor = ""
    if value[0] == "#":
        value = value[1:]
        nova_cor = "#"
    r = int(value[:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:], 16)
    brilho = 64
    r = min(255, r + brilho)
    g = min(255, g + brilho)
    b = min(255, b + brilho)
    nova_cor += "{:02X}{:02X}{:02X}".format(r, g, b)
    return nova_cor

    