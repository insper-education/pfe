#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 31 de Outubro de 2024
"""

import bleach
from django import template
register = template.Library()

@register.filter(name='bleach_urlize')
def bleach_urlize(value):
    # Tags permitidas
    allowed_tags = ["a"]
    allowed_attrs = {"a": ["href", "title", "target"]}
    
    # Linkify o texto
    return bleach.linkify(value, parse_email=True, callbacks=[])