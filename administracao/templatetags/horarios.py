#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 6 de Agosto de 2026
"""

from django import template

import json

from administracao.models import Estrutura


register = template.Library()

@register.filter
def formata_horarios(horarios):
    """Formata os horários para exibição."""
    try:
        horarios_semanais = Estrutura.loads(nome="Horarios Semanais")
        print(f"Horários semanais: {horarios_semanais}")
        horarios = json.loads(horarios)
        dias_semana_pt = ["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"]
        dias_semana_en = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return [
                {
                  "pt": f"{dias_semana_pt[dia]} das {horarios_semanais[hora][0]} as {horarios_semanais[hora][1]}",
                  "en": f"{dias_semana_en[dia]} from {horarios_semanais[hora][0]} to {horarios_semanais[hora][1]}"
                } 
               for dia, hora in horarios ]
    except Exception as e:
        return ["Erro ao interpretar o horário de aulas"]
