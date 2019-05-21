# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.urls import path
from . import views

urlpatterns = [
    #path('signup/', views.SignUp.as_view(), name='signup'),
    #path('usuario/<str:pk>/', views.Usuario.as_view(), name='usuario'),
    #path('show/<str:pk>/', views.show_profile, name='show'),
    path('update/', views.update_profile, name='updatep'),
    #path('export/', views.export, name='export'),
    #path('exportxls/', views.exportXLS, name='exportxls'),
]
