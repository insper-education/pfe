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