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
def formata_horarios(horarios, formato=None):
    """Formata os horários para exibição."""
    try:
        horarios_semanais = Estrutura.loads(nome="Horarios Semanais")
        horarios = json.loads(horarios)
        if formato == "curto":
            dias_semana_pt = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
            dias_semana_en = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            return [
                {
                  "pt": f"{dias_semana_pt[dia]} {horarios_semanais[hora][0]}",
                  "en": f"{dias_semana_en[dia]} {horarios_semanais[hora][0]}"
                }
                for dia, hora in horarios ]
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


@register.filter
def horarios_trab_grupo_aulas(projeto):
    """Retorna os horários de trabalho em grupo e aulas do período selecionado."""
    horarios_trab_grupo_aulas = Estrutura.loads(nome="Horarios Trabalho em Grupo e Aulas")
    edicoes_disponiveis = sorted([(int(k.split(".")[0]), int(k.split(".")[1])) for k in horarios_trab_grupo_aulas], reverse=True,)
    melhor_edicao = next((e for e in edicoes_disponiveis if e <= (projeto.ano, projeto.semestre)), None)
    trab_grupo_aulas = horarios_trab_grupo_aulas[f"{melhor_edicao[0]}.{melhor_edicao[1]}"] if melhor_edicao else {}
    return trab_grupo_aulas


@register.filter
def get_horarios(projeto):
    """Retorna as faixas de horários do período selecionado."""
    horarios_semanais = Estrutura.loads(nome="Horarios Semanais")
    return horarios_semanais
    
