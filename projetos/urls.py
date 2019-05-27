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
    path('selecao/', views.selecao, name='selecao'),
    path('histograma/', views.histograma, name='histograma'),
    path('areas/', views.areas, name='areas'),
    path('administracao/', views.administracao, name='administracao'),
    path('organizacoes/', views.organizacoes, name='organizacoes'),
    path('organizacao/<str:login>', views.organizacao, name='organizacao'),
    path('professor/', views.professor, name='professor'),
    path('export/<str:modelo>/<str:formato>', views.export, name='export'),
    path('backup/<str:formato>', views.backup, name='backup'),
]
