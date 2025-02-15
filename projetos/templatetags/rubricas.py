#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 22 de Abril de 2020
"""

import json

from django import template
register = template.Library()

@register.filter
def get_rubrica(objetivos, objetivo):
    """Permite buscar uma rubrica."""
    if not objetivos:
        return None
    return objetivos.get(id=objetivo)

@register.filter
def get_texto_conceito(objetivo, conceito):
    """Permite buscar o texto de uma rubrica."""
    if (not conceito) or (not objetivo):
        return ""
    r = json.loads(objetivo.rubrica)["intermediaria"]["grupo"]
    if conceito == "A " or conceito == "A+":
        return r["A"]["pt"]
    if conceito == "B " or conceito == "B+":
        return r["B"]["pt"]
    if conceito == "C " or conceito == "C+":
        return r["C"]["pt"]
    if conceito == "D ":
        return r["D"]["pt"]
    if conceito == "I ":
        return r["I"]["pt"]
    return "Erro"

@register.filter
def get_texto_nota(objetivo, nota):
    """Permite buscar o texto de uma rubrica."""
    if (not nota) or (not objetivo):
        return ""
    r = json.loads(objetivo.rubrica)["final"]["grupo"]
    if nota >= 9:
        return r["A"]["pt"]
    if nota >= 7:
        return r["B"]["pt"]
    if nota >= 5:
        return r["C"]["pt"]
    if nota >= 4:
        return r["D"]["pt"]
    if nota >= 0:
        return r["I"]["pt"]
    return "Erro"

@register.filter
def get_texto_intermediaria_nota(objetivo, nota):
    """Permite buscar o texto de uma rubrica."""
    if (not nota) or (not objetivo):
        return ""
    r = json.loads(objetivo.rubrica)["intermediaria"]["grupo"]
    if nota >= 9:
        return r["A"]["pt"]
    if nota >= 7:
        return r["B"]["pt"]
    if nota >= 5:
        return r["C"]["pt"]
    if nota >= 4:
        return r["D"]["pt"]
    if nota >= 0:
        return r["I"]["pt"]
    return "Erro"

@register.filter
def get_texto_final_nota(objetivo, nota):
    """Permite buscar o texto de uma rubrica."""
    if (not nota) or (not objetivo):
        return ""
    r = json.loads(objetivo.rubrica)["final"]["grupo"]
    if nota >= 9:
        return r["A"]["pt"]
    if nota >= 7:
        return r["B"]["pt"]
    if nota >= 5:
        return r["C"]["pt"]
    if nota >= 4:
        return r["D"]["pt"]
    if nota >= 0:
        return r["I"]["pt"]
    return "Erro"
