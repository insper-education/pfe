#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 9 de Novembro de 2024
"""

from urllib import parse

from django import template

register = template.Library()

@register.filter(name="add_http")
def add_http(url: str) -> str:
    if not url:
        return url
    
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return "http://" + url
    return url
