#!/usr/bin/env python
"""
pfe URL Configuration
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from projetos import arquivos, sites

from .views import *

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico")),

    path("", index, name="index"),
    path("info", info, name="info"),

    path("estudantes/", include("estudantes.urls")),
    path("organizacoes/", include("organizacoes.urls")),
    path("projetos/", include("projetos.urls")),
    path("propostas/", include("propostas.urls")),
    path("professores/", include("professores.urls")),
    path("documentos/", include("documentos.urls")),
    path("administracao/", include("administracao.urls")),
    path("operacional/", include("operacional.urls")),
    path("calendario/", include("calendario.urls")),
    path("academica/", include("academica.urls")),
    path("users/", include("users.urls")), #Transferir tudo para accounts (NO FUTURO)
    path("users/", include("django.contrib.auth.urls")), #Transferir tudo para accounts (NO FUTURO)
    path("accounts/", include("django.contrib.auth.urls")),
    path(settings.ADMIN_SITE, admin.site.urls),
    path("arquivos/<str:documentos>/<str:path>", arquivos.arquivos, name="arquivos"),
    path("arquivos/<str:organizacao>/<str:usuario>/<str:path>", arquivos.arquivos, name="arquivos"),
    path("arquivos/<str:organizacao>/<str:projeto>/<str:usuario>/<str:path>", arquivos.arquivos, name="arquivos"),
    path("doc/<str:tipo>", arquivos.doc, name="doc"),
    path("manutencao/", manutencao, name="manutencao"),
    path("migracao/", migracao, name="migracao"),
    path("upload_site_e_pastas/<int:projeto_id>", sites.upload_site_e_pastas, name="upload_site_e_pastas"),
    re_path(r'^sites/(?P<projeto_id>\d+)/(?P<path>.*)$', sites.sites, name="sites"),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

handler400 = "pfe.views.custom_400"


#The URLs provided by auth are:
# accounts/login/ [name="login"]
# accounts/logout/ [name="logout"]
# accounts/password_change/ [name="password_change"]
# accounts/password_change/done/ [name="password_change_done"]
# accounts/password_reset/ [name="password_reset"]
# accounts/password_reset/done/ [name="password_reset_done"]
# accounts/reset/<uidb64>/<token>/ [name="password_reset_confirm"]
# accounts/reset/done/ [name="password_reset_complete"]
