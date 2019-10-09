# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'), #pagina inicial
    path('administracao/', views.administracao, name='administracao'),
    path('areas/', views.areas, name='areas'),
    path('backup/<str:formato>', views.backup, name='backup'),
    path('calendario/', views.calendario, name='calendario'),
    path('carrega/<str:dado>', views.carrega, name='carrega'),
    path('carrega_bancos', views.carrega_bancos, name='carrega_bancos'),
    path('carregar/', views.carregar, name='carregar'),
    path('completo/<int:pk>', views.completo, name='completo'),
    path('dinamicas/', views.dinamicas, name='dinamicas'),
    path('documentos/', views.documentos, name='documentos'),
    path('download/<str:path>', views.download, name='download'),
    path('encontros/', views.encontros, name='encontros'),
    path('email_backup/', views.email_backup, name='email_backup'),
    path('export/<str:modelo>/<str:formato>', views.export, name='export'),
    path('exportar/', views.exportar, name='exportar'),
    path('fechados/', views.fechados, name='fechados'),
    path('histograma/', views.histograma, name='histograma'),
    path('meuprojeto/', views.meuprojeto, name='meuprojeto'),
    path('organizacoes/', views.organizacoes, name='organizacoes'),
    path('organizacao/<str:login>', views.organizacao, name='organizacao'),
    path('professor/', views.professor, name='professor'),
    path('professores/', views.professores, name='professores'),
    path('projetos/', views.projetos, name='projetos'),
    path('projeto/<int:pk>', views.ProjetoDetailView.as_view(), name='projeto'),
    path('projetos_lista/<str:periodo>', views.projetos_lista, name='projetos_lista'),
    path('propor/', views.propor, name='propor'),
    path('reembolso/', views.reembolso, name='reembolso'),
    path('relatorio/<str:modelo>/<str:formato>', views.relatorio, name='relatorio'),
    path('relatorio_backup/', views.relatorio_backup, name='relatorio_backup'),    
    path('relatorios/', views.relatorios, name='relatorios'),
    path('servico/', views.servico, name='servico'),
    path('submissao/', views.submissao, name='submissao'),
    path('tabela_documentos/', views.tabela_documentos, name='tabela_documentos'),
    path('todos/', views.todos, name='todos'),
    path('bancas/', views.bancas, name='bancas'),
]
