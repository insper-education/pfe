#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

from django import template

from academica.support import media_falconi, media_bancas, media_orientador

register = template.Library()

@register.filter()
def medias(projeto):
    notas = {
        "orientador": media_orientador(projeto),
        "bancas": media_bancas(projeto),
        "falconi": media_falconi(projeto),
    }
    notas["media"] = (notas["orientador"] + notas["bancas"] + notas["falconi"])/3
    return notas