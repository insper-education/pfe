# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 18 de Outubro de 2019

#Baseado em https://stackoverflow.com/questions/19598213/generating-a-date-relative-to-another-date-in-django-template

import datetime

from django import template
register = template.Library()

@register.filter
def plus_days(value, days):
    return value + datetime.timedelta(days=days)