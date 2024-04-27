#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [

    path("",
         views.calendario,
         name="calendario"),

    path("copia_calendario/",
         views.copia_calendario,
         name="copia_calendario"),

    path("events/<int:event_id>",
         views.export_calendar,
         name="event_ics_export"),

    path("ajax/atualiza_evento/",
         views.atualiza_evento,
         name="atualiza_evento"),

    path("ajax/remove_evento/",
         views.remove_evento,
         name="remove_evento"),

]
