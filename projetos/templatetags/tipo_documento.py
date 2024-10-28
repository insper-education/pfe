#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Novembro de 2023
"""

from django import template
register = template.Library()

@register.filter
def tipo_documento(documentos, tipo):
    """Retorna um documento por tipo."""
    if isinstance(tipo, str):
        return documentos.filter(tipo_documento__sigla=tipo).last()
    return documentos.filter(tipo_documento__id=tipo).last()
    
@register.filter
def tipo_documentos(documentos, tipo):
    """Retorna um documento por tipo."""
    return documentos.filter(tipo_documento__id=tipo)
    
    