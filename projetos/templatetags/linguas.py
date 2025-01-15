#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Janeiro de 2025
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def lng(pt_text, en_text):
    return mark_safe(f'''<span lang="pt">{pt_text}</span><span lang="en" style="display:none">{en_text}</span>''')

# Quando a palavra muda por causa do gênero
@register.simple_tag
def lng_g(pt_genero, pt_text_m, pt_text_f, en_text_m, en_text_f=None):
    if pt_genero.lower() == "m":
        pt_text = pt_text_m
        en_text = en_text_m
    else:
        pt_text = pt_text_f
        if en_text_f is None:
            en_text = en_text_m
        else:
            en_text = en_text_f
    return mark_safe(f'''<span lang="pt">{pt_text}</span><span lang="en" style="display:none">{en_text}</span>''')

# Quando a palavra muda por causa do número
@register.simple_tag
def lng_n(pt_numero, pt_text_s, pt_text_p, en_text_s, en_text_p=None):
    if pt_numero <= 1:
        pt_text = pt_text_s
        en_text = en_text_s
    else:
        pt_text = pt_text_p
        if en_text_p is None:
            en_text = en_text_s
        else:
            en_text = en_text_p
    return mark_safe(f'''<span lang="pt">{pt_text}</span><span lang="en" style="display:none">{en_text}</span>''')