#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'), #pagina inicial
    path('administracao/', views.administracao, name='administracao'),
    path('areas/', views.areas, name='areas'),
    path('avisos_listar/', views.avisos_listar, name='avisos_listar'),
    path('backup/<str:formato>', views.backup, name='backup'),
    path('bancas_agendamento/', views.bancas_agendamento, name='bancas_agendamento'),
    path('bancas_index/', views.bancas_index, name='bancas_index'),
    path('bancas_buscar', views.bancas_buscar, name='bancas_buscar'),
    path('bancas_criar', views.bancas_criar, name='bancas_criar'),
    path('bancas_editar/<int:primarykey>', views.bancas_editar, name='bancas_editar'),
    path('bancas_lista/<str:periodo>', views.bancas_lista, name='bancas_lista'),
    path('calendario/', views.calendario, name='calendario'),
    path('carrega/<str:dado>', views.carrega, name='carrega'),
    path('carrega_bancos/', views.carrega_bancos, name='carrega_bancos'),
    path('carregar/', views.carregar, name='carregar'),
    path('completo/<int:primakey>', views.completo, name='completo'),
    path('comite/>', views.comite, name='comite'),
    path('cria_anotacao/<str:login>', views.cria_anotacao, name='cria_anotacao'),
    path('dinamicas/', views.dinamicas, name='dinamicas'),
    path('index_aluno/', views.index_aluno, name='index_aluno'),
    path('index_documentos/', views.index_documentos, name='index_documentos'),
    path('index_professor/', views.index_professor, name='index_professor'),
    path('encontros_marcar/', views.encontros_marcar, name='encontros_marcar'),
    path('emails/', views.emails, name='emails'),
    path('email_backup/', views.email_backup, name='email_backup'),
    path('export/<str:modelo>/<str:formato>', views.export, name='export'),
    path('exportar/', views.exportar, name='exportar'),
    path('projetos_fechados/', views.projetos_fechados, name='projetos_fechados'),
    path('histograma/', views.histograma, name='histograma'),
    path('meuprojeto/', views.meuprojeto, name='meuprojeto'),
    path('minhas_bancas/', views.minhas_bancas, name='minhas_bancas'),
    path('organizacoes_lista/', views.organizacoes_lista, name='organizacoes_lista'),
    path('organizacao_completo/<str:org>', views.organizacao_completo, name='organizacao_completo'),
    path('professores_tabela/', views.professores_tabela, name='professores_tabela'),
    path('selecao_projetos/', views.selecao_projetos, name='selecao_projetos'),
    path('projeto_detalhe/<int:primarykey>', views.projeto_detalhe, name='projeto_detalhe'),
    path('projetos_lista/<str:periodo>', views.projetos_lista, name='projetos_lista'),
    path('propor/', views.propor, name='propor'),
    path('reembolso_pedir/', views.reembolso_pedir, name='reembolso_pedir'),
    path('relatorio/<str:modelo>/<str:formato>', views.relatorio, name='relatorio'),
    path('relatorio_backup/', views.relatorio_backup, name='relatorio_backup'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('servico/', views.servico, name='servico'),
    path('submissao/', views.submissao, name='submissao'),
    path('tabela_documentos/', views.tabela_documentos, name='tabela_documentos'),
    path('todos/', views.todos, name='todos'),
    path('todos_parceiros/', views.todos_parceiros, name='todos_parceiros'),
    path('todos_professores/', views.todos_professores, name='todos_professores'),
    path('events/<int:event_id>', views.export, name="event_ics_export"),
]

#urlpatterns += patterns('',
    #url(r'^events/(?P&lt;event_id&gt;\d+)/export/', 'app_events.ics_views.export', name="event_ics_export"),
    #url(r'^events/(?P&lt;event_id&gt;\d+)/export/', 'views.ics_views.export', name="event_ics_export"),
#)