# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.urls import path
from . import views

urlpatterns = [
    path('alunos/', views.alunos, name='alunos'),
    path('alunos_inscrevendo/', views.alunos_inscrevendo, name='alunos_inscrevendo'),
    path('aluno/<int:pk>', views.aluno, name='aluno'),
    path('areas_interesse/', views.areas_interesse, name='areas_interesse'),
    path('perfil/', views.perfil, name='perfil'),
    path('professor_detail/<int:pk>', views.professor_detail, name='professor_detail'),

]