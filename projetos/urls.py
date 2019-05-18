#https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Tutorial_local_library_website

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'), #pagina inicial
    path('projetos/', views.projetos, name='projetos'),
    path('projeto/<int:pk>', views.ProjetoDetailView.as_view(), name='projeto'),
    path('selecao/', views.selecao, name='selecao'),
]
