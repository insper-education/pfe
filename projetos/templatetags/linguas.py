#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Janeiro de 2025
"""

import locale

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

def thtml(pt_text, en_text):
    return mark_safe(f'''<span lang="pt">{pt_text}</span><span lang="en" style="display:none">{en_text}</span>''')

@register.simple_tag
def lng(pt_text, en_text):
    return thtml(pt_text, en_text)

# Para mostrar datas
@register.simple_tag
def lng_d(date, pt_text="", en_text=""):
    pt_text = date.strftime("%d/%m/%y") + ( " " + pt_text if pt_text else "")
    en_text = date.strftime("%b %d, %y") + ( " " + en_text if en_text else "")
    return thtml(pt_text, en_text)

# Para mostrar datas
@register.simple_tag
def lng_dl(date, pt_text="", en_text=""):
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
    pt_text = date.strftime("%d de %B de %Y") + ( " " + pt_text if pt_text else "")
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    en_text = date.strftime("%B %d, %Y") + ( " " + en_text if en_text else "")
    return thtml(pt_text, en_text)

# Para números com duas casas decimais
@register.simple_tag
def lng_2(numero):
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
    pt_text = locale.format_string("%.2f", numero, grouping=True)
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    en_text = locale.format_string("%.2f", numero, grouping=True)
    return thtml(pt_text, en_text)

# Teste se verdade usa primeiro, senão segundo
@register.simple_tag
def lng_b(pt_bool, pt_text_t, pt_text_f, en_text_t, en_text_f=None):
    if pt_bool:
        pt_text = pt_text_t
        en_text = en_text_t
    else:
        pt_text = pt_text_f
        if en_text_f is None:
            en_text = en_text_t
        else:
            en_text = en_text_f
    return thtml(pt_text, en_text)

# Quando a palavra muda por causa do gênero
@register.simple_tag
def lng_g(pt_genero, pt_text_m, pt_text_f, en_text_m, en_text_f=None):
    if pt_genero.lower() == "f":
        pt_text = pt_text_f
        if en_text_f is None:
            en_text = en_text_m
        else:
            en_text = en_text_f
    else:
        pt_text = pt_text_m
        en_text = en_text_m
    return thtml(pt_text, en_text)

# Quando a palavra muda por causa do número
@register.simple_tag
def lng_n(numero, pt_text_s, pt_text_p, en_text_s, en_text_p=None):
    try:
        numero = int(numero)
    except (ValueError, TypeError):
        numero = 0
    if numero <= 1:
        pt_text = pt_text_s
        en_text = en_text_s
    else:
        pt_text = pt_text_p
        if en_text_p is None:
            en_text = en_text_s
        else:
            en_text = en_text_p
    return thtml(pt_text, en_text)
