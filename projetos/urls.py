#!/usr/bin/env python
# pylint: disable=C0103

"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.urls import path

from organizacoes.views import projeto_feedback

from . import views


urlpatterns = [

    # pagina inicial (herança problemática)
    path('',
         views.index,
         name='index'),

    # pagina inicial de projs.
    path('index_projetos/',
        views.index_projetos,
        name='index_projetos'),
        

    # simplificação atual
    #     path('index_projetos/',
    #          views.projetos_fechados,
    #          name='index_projetos'),

    path('analise_notas/',
         views.analise_notas,
         name='analise_notas'),

    path('conexoes_estabelecidas/',
         views.conexoes_estabelecidas,
         name='conexoes_estabelecidas'),

    path('evolucao_notas/',
         views.evolucao_notas,
         name='evolucao_notas'),

    path('carrega_bancos/',
         views.carrega_bancos,
         name='carrega_bancos'),

    path('comite/',
         views.comite,
         name='comite'),

    path('completo/<int:primakey>',
         views.projeto_completo,
         name='completo'),  # REMOVER

    path('distribuicao_areas/',
         views.distribuicao_areas,
         name='distribuicao_areas'),

    path('analise_objetivos/',
         views.analise_objetivos,
         name='analise_objetivos'),

    path('evolucao_objetivos/',
         views.evolucao_objetivos,
         name='evolucao_objetivos'),

    path('lista_acompanhamento',
         views.lista_acompanhamento,
         name='lista_acompanhamento'),

     path('acompanhamento_view',
         views.acompanhamento_view,
         name='acompanhamento_view'),

     path('certificacao_falconi',
         views.certificacao_falconi,
         name='certificacao_falconi'),

     path('correlacao_medias_cr',
         views.correlacao_medias_cr,
         name='correlacao_medias_cr'),

    path('lista_feedback',
         views.lista_feedback,
         name='lista_feedback'),

    path('logs/',
         views.logs,
         name='logs'),

    path('meuprojeto/',
         views.meuprojeto,
         name='meuprojeto'),

    path('migracao/',
         views.migracao,
         name='migracao'),

    path('mostra_feedback/<int:feedback_id>',
         views.mostra_feedback,
         name='mostra_feedback'),

    path('nomes/',
         views.nomes,
         name='nomes'),

    path('projeto_completo/<int:primakey>',
         views.projeto_completo,
         name='projeto_completo'),

    path('projeto_detalhes/<int:primarykey>',
         views.projeto_detalhes,
         name='projeto_detalhes'),

    # Antigo, remover
    path('projeto_feedback',
         projeto_feedback,
         name='projeto_feedback_old'),

    path('projetos_fechados/',
         views.projetos_fechados,
         name='projetos_fechados'),

    path('projetos_lista',
         views.projetos_lista,
         name='projetos_lista'),

    path('projetos_vs_propostas',
         views.projetos_vs_propostas,
         name='projetos_vs_propostas'),


    path('reembolso_pedir/',
         views.reembolso_pedir,
         name='reembolso_pedir'),

    path('relatorios/',
         views.relatorios,
         name='relatorios'),

    path('ajax/validate_aviso/',
         views.validate_aviso,
         name='validate_aviso'),

    path('graficos/',
         views.graficos,
         name='graficos'),

]
