#!/usr/bin/env python
"""
pfe URL Configuration
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
#from django.views.generic.base import TemplateView # new

from projetos import views

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
    path('', RedirectView.as_view(url='/projetos/', permanent=True)),
    path('projetos/', include('projetos.urls')),
    path('users/', include('users.urls')), #Transferir tudo para accounts (NO FUTURO)
    path('users/', include('django.contrib.auth.urls')), #Transferir tudo para accounts (NO FUTURO)
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('arquivos/<str:documentos>/<str:path>', views.arquivos, name='arquivos'),
    path('arquivos/<str:organizacao>/<str:usuario>/<str:path>', views.arquivos2, name='arquivos2'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

#The URLs provided by auth are:
# accounts/login/ [name='login']
# accounts/logout/ [name='logout']
# accounts/password_change/ [name='password_change']
# accounts/password_change/done/ [name='password_change_done']
# accounts/password_reset/ [name='password_reset']
# accounts/password_reset/done/ [name='password_reset_done']
# accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
# accounts/reset/done/ [name='password_reset_complete']
