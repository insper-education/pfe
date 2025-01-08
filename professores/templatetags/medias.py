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
    notas = [0,0,0,0]
    notas[0] = media_orientador(projeto)
    notas[1] = media_bancas(projeto)
    notas[2] = media_falconi(projeto)
    notas[3] = (notas[0] + notas[1] + notas[2])/3
    return notas