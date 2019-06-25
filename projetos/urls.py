# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'), #pagina inicial
    path('projetos/', views.projetos, name='projetos'),
    path('projeto/<int:pk>', views.ProjetoDetailView.as_view(), name='projeto'),
    path('completo/<int:pk>', views.completo, name='completo'),
    path('histograma/', views.histograma, name='histograma'),
    path('areas/', views.areas, name='areas'),
    path('administracao/', views.administracao, name='administracao'),
    path('organizacoes/', views.organizacoes, name='organizacoes'),
    path('organizacao/<str:login>', views.organizacao, name='organizacao'),
    path('professor/', views.professor, name='professor'),
    path('export/<str:modelo>/<str:formato>', views.export, name='export'),
    path('backup/<str:formato>', views.backup, name='backup'),
    path('email_backup/', views.email_backup, name='email_backup'),
    path('servico/', views.servico, name='servico'),
    path('propor/', views.propor, name='propor'),
    path('relatorio/<str:modelo>/<str:formato>', views.relatorio, name='relatorio'),
    path('relatorio_backup/', views.relatorio_backup, name='relatorio_backup'),
    path('fechados/', views.fechados, name='fechados'),
    path('carrega_disciplinas/', views.carrega_disciplinas, name='carrega_disciplinas'),
    path('calendario/', views.calendario, name='calendario'),
]
