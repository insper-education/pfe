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
    path('avaliacao/<int:primarykey>', views.avaliacao, name='avaliacao'),
    path('avisos_listar/', views.avisos_listar, name='avisos_listar'),
    path('backup/<str:formato>', views.backup, name='backup'),
    path('bancas_agendamento/', views.bancas_agendamento, name='bancas_agendamento'),
    path('bancas_index/', views.bancas_index, name='bancas_index'),
    path('bancas_buscar/', views.bancas_buscar, name='bancas_buscar'),
    path('bancas_criar/', views.bancas_criar, name='bancas_criar'),
    path('bancas_editar/<int:primarykey>', views.bancas_editar, name='bancas_editar'),
    path('bancas_lista/<str:periodo>', views.bancas_lista, name='bancas_lista'),
    path('bancas_tabela/', views.bancas_tabela, name='bancas_tabela'),
    path('calendario/', views.calendario, name='calendario'),
    path('calendario_limpo/', views.calendario_limpo, name='calendario_limpo'),
    path('carrega/<str:dado>', views.carrega, name='carrega'),
    path('carrega_bancos/', views.carrega_bancos, name='carrega_bancos'),
    path('carregar/', views.carregar, name='carregar'),
    path('certificados_submetidos/', views.certificados_submetidos, name='certificados_submetidos'),
    path('conceitos_obtidos/<int:primarykey>', views.conceitos_obtidos, name='conceitos_obtidos'),
    path('comite/>', views.comite, name='comite'),
    path('completo/<int:primakey>', views.completo, name='completo'),
    path('coorientadores_tabela/', views.coorientadores_tabela, name='coorientadores_tabela'),
    path('cria_anotacao/<str:login>', views.cria_anotacao, name='cria_anotacao'),
    path('dinamicas/<str:periodo>', views.dinamicas, name='dinamicas'),
    path('dinamicas/', views.dinamicas_root, name='dinamicas_root'),
    path('distribuicao_areas/<str:tipo>', views.distribuicao_areas, name='distribuicao_areas'),
    path('edita_aviso/<int:primakey>', views.edita_aviso, name='edita_aviso'),
    path('encontros_marcar/', views.encontros_marcar, name='encontros_marcar'),
    path('emails/', views.emails, name='emails'),
    path('email_backup/', views.email_backup, name='email_backup'),
    path('events/<int:event_id>', views.export_calendar, name="event_ics_export"),
    path('export/<str:modelo>/<str:formato>', views.export, name='export'),
    path('exportar/', views.exportar, name='exportar'),
    path('histograma/', views.histograma, name='histograma'),
    path('index_aluno/', views.index_aluno, name='index_aluno'),
    path('index_documentos/', views.index_documentos, name='index_documentos'),
    path('index_operacional/', views.index_operacional, name='index_operacional'),
    path('index_organizacao/', views.index_organizacao, name='index_organizacao'),
    path('index_professor/', views.index_professor, name='index_professor'),
    path('lista_feedback', views.lista_feedback, name='lista_feedback'),
    path('mapeamento/', views.mapeamento, name='mapeamento'),
    path('mapeamento_estudante_projeto/<str:anosemestre>', views.mapeamento_estudante_projeto, name='mapeamento_estudante_projeto'),
    path('meuprojeto/', views.meuprojeto, name='meuprojeto'),
    path('migracao/', views.migracao, name='migracao'),
    path('minhas_bancas/', views.minhas_bancas, name='minhas_bancas'),
    path('mostra_feedback/<int:feedback_id>', views.mostra_feedback, name='mostra_feedback'),
    path('organizacoes_lista/', views.organizacoes_lista, name='organizacoes_lista'),
    path('organizacao_completo/<str:org>', views.organizacao_completo, name='organizacao_completo'),
    path('organizacoes_tabela/', views.organizacoes_tabela, name='organizacoes_tabela'),
    path('professores_tabela/', views.professores_tabela, name='professores_tabela'),
    path('projeto_detalhe/<int:primarykey>', views.projeto_detalhe, name='projeto_detalhe'),
    path('projeto_feedback', views.projeto_feedback, name='projeto_feedback'),
    path('projetos_fechados/', views.projetos_fechados, name='projetos_fechados'),
    path('projetos_fechados/<str:periodo>', views.projetos_fechados, name='projetos_fechados_peri'),
    path('projetos_lista/<str:periodo>', views.projetos_lista, name='projetos_lista'),
    path('projeto_submeter', views.projeto_submeter, name='projeto_submeter'),
    path('propor/', views.propor, name='propor'),
    path('reembolso_pedir/', views.reembolso_pedir, name='reembolso_pedir'),
    path('relatorio/<str:modelo>/<str:formato>', views.relatorio, name='relatorio'),
    path('relatorio_backup/', views.relatorio_backup, name='relatorio_backup'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('selecao_projetos/', views.selecao_projetos, name='selecao_projetos'),
    path('servico/', views.servico, name='servico'),
    path('submissao/', views.submissao, name='submissao'),
    path('tabela_documentos/', views.tabela_documentos, name='tabela_documentos'),
    path('todos_parceiros/', views.todos_parceiros, name='todos_parceiros'),
    path('todos_professores/', views.todos_professores, name='todos_professores'),

    path('ajax/validate_aviso/', views.validate_aviso, name='validate_aviso'),

]
