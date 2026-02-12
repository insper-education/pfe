#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index_estudantes, name="index_estudantes"),  # pagina inicial
    path("estudantes/", views.index_estudantes, name="estudantes"),
    path("alinhamentos_gerais/", views.alinhamentos_gerais, name="alinhamentos_gerais"),
    path("alocacao_semanal/", views.alocacao_semanal, name="alocacao_semanal"),
    path("alocacao_hora/", views.alocacao_hora, name="alocacao_hora"),
    path("avaliacao_pares/<str:momento>", views.avaliacao_pares, name="avaliacao_pares"),
    path("codigo_conduta/", views.codigo_conduta, name="codigo_conduta"),
    path("codigo_conduta_projeto/", views.codigo_conduta_projeto, name="codigo_conduta_projeto"),
    path("encontros_cancelar/<int:evento_id>", views.encontros_cancelar, name="encontros_cancelar"),
    path("encontros_marcar/", views.encontros_marcar, name="encontros_marcar"),
    path("estilo_comunicacao/", views.estilo_comunicacao, name="estilo_comunicacao"),
    path("estudante_feedback", views.estudante_feedback, name="estudante_feedback"),
    path("estudante_feedback/<str:hashid>", views.estudante_feedback_hashid, name="estudante_feedback_hashid"),
    path("exames_pesos/", views.exames_pesos, name="exames_pesos"),
    path("funcionalidade_grupo/", views.funcionalidade_grupo, name="funcionalidade_grupo"),
    path("dinamica_conflitos/", views.dinamica_conflitos, name="dinamica_conflitos"),
    path("informacoes_adicionais/", views.informacoes_adicionais, name="informacoes_adicionais"),
    path("minhas_bancas/", views.minhas_bancas, name="minhas_bancas"),
    path("pesos_rubricas/", views.pesos_rubricas, name="pesos_rubricas"),
    path("refresh_hora/", views.refresh_hora, name="refresh_hora"),
    path("relato_quinzenal/", views.relato_quinzenal, name="relato_quinzenal"),
    path("relato_visualizar/<int:id>", views.relato_visualizar, name="relato_visualizar"),
    path("selecao_propostas/", views.selecao_propostas, name="selecao_propostas"),
    path("submissao_documento/", views.submissao_documento, name="submissao_documento"),
    path("validate_feedback/", views.validate_feedback, name="validate_feedback"),

    path("ajax/opcao_temporaria/", views.opcao_temporaria, name="opcao_temporaria"),
]
