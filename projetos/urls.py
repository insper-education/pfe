# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'), #pagina inicial
    path('projetos/', views.projetos, name='projetos'),
    path('projeto/<int:pk>', views.ProjetoDetailView.as_view(), name='projeto'),
    path('selecao/', views.selecao, name='selecao'),
    path('export/', views.export, name='export'),
    path('exportxls/', views.exportXLS, name='exportxls'),
    path('histograma/', views.histograma, name='histograma'),
    path('administracao/', views.administracao, name='administracao'),
]
