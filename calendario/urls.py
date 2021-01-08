#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [

    path('', views.calendario, name='calendario'), #pagina inicial

    path('calendario_limpo/', views.calendario_limpo, name='calendario_limpo'),

    path('events/<int:event_id>', views.export_calendar, name="event_ics_export"),

    path('ajax/atualiza_evento/', views.atualiza_evento, name='atualiza_evento'),

]
