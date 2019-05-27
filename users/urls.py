# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.urls import path
from . import views

urlpatterns = [
    path('update/', views.update_profile, name='updatep'),
    path('alunos/', views.alunos, name='alunos'),
    path('aluno/<int:pk>', views.aluno, name='aluno'),
]