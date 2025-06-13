#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index_administracao, name="index_administracao"),  # pagina inicial
    path("administracao", views.index_administracao, name="administracao"),
    path("bloqueados/", views.bloqueados, name="bloqueados"),
    path("cadastrar_disciplina/", views.cadastrar_disciplina, name="cadastrar_disciplina"),
    path("cadastrar_organizacao/", views.cadastrar_organizacao, name="cadastrar_organizacao"),
    path("cadastrar_organizacao/<int:proposta_id>", views.cadastrar_organizacao, name="cadastrar_organizacao"),
    path("cadastrar_usuario/", views.cadastrar_usuario, name="cadastrar_usuario"),
    path("cancela_tarefa/<str:task_id>/", views.cancela_tarefa, name="cancela_tarefa"),
    path("carrega_arquivo/<str:dado>", views.carrega_arquivo, name="carrega_arquivo"),
    path("conexoes_estabelecidas/", views.conexoes_estabelecidas, name="conexoes_estabelecidas"),
    path("configurar/", views.configurar, name="configurar"),
    path("desbloquear_usuarios/", views.desbloquear_usuarios, name="desbloquear_usuarios"),
    path("edita_organizacao/<int:primarykey>", views.edita_organizacao, name="edita_organizacao"),
    path("edita_usuario/<int:primarykey>", views.edita_usuario, name="edita_usuario"),
    path("estrela_estudante/", views.estrela_estudante, name="estrela_estudante"),
    path("export/<str:modelo>/<str:formato>", views.export, name="export"),
    path("exportar", views.exportar, name="exportar"),
    path("fechar_conexoes/", views.fechar_conexoes, name="fechar_conexoes"),
    path("index_carregar/", views.index_carregar, name="index_carregar"),
    path("lista_git/", views.lista_git, name="lista_git"),
    path("logs/", include("log_viewer.urls")),
    path("logs_django_admin/", views.logs_django_admin, name="logs_django_admin"),
    path("logs_django_admin/<int:dias>", views.logs_django_admin, name="logs_django_admin"),
    path("montar_grupos/", views.montar_grupos, name="montar_grupos"),
    path("pre_alocar_estudante/", views.pre_alocar_estudante, name="pre_alocar_estudante"),
    path("propor/", views.propor, name="propor"),
    path("relatorio/<str:modelo>/<str:formato>", views.relatorio, name="relatorio"),
    path("relatorios", views.relatorios, name="relatorios"),
    path("selecionar_orientadores/", views.selecionar_orientadores, name="selecionar_orientadores"),
    path("servico/", views.servico, name="servico"),
    path("tarefas_agendadas/", views.tarefas_agendadas, name="tarefas_agendadas"),
    path("versoes_sistema/", views.versoes_sistema, name="versoes_sistema"),

    path("ajax/definir_orientador/", views.definir_orientador, name="definir_orientador"),
    path("ajax/excluir_disciplina", views.excluir_disciplina, name="excluir_disciplina"),
]
