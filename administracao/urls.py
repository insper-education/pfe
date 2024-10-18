#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [

    # pagina inicial
    path("",
        views.index_administracao,
        name="index_administracao"),

    path("administracao",
        views.index_administracao,
        name="administracao"),

    path("backup/<str:formato>",
        views.backup,
        name="backup"),

    path("cadastrar_disciplina/",
        views.cadastrar_disciplina,
        name="cadastrar_disciplina"),

    path("cadastrar_organizacao/",
        views.cadastrar_organizacao,
        name="cadastrar_organizacao"),

    path("cadastrar_organizacao/<int:proposta_id>",
        views.cadastrar_organizacao,
        name="cadastrar_organizacao"),

    path("edita_organizacao/<int:primarykey>",
        views.edita_organizacao,
        name="edita_organizacao"),

    path("cadastrar_usuario/",
        views.cadastrar_usuario,
        name="cadastrar_usuario"),

    path("desbloquear_usuarios/",
        views.desbloquear_usuarios,
        name="desbloquear_usuarios"),

    path("edita_usuario/<int:primarykey>",
        views.edita_usuario,
        name="edita_usuario"),

    path("carrega_arquivo/<str:dado>",
        views.carrega_arquivo,
        name="carrega_arquivo"),

    path("index_carregar/",
        views.index_carregar,
        name="index_carregar"),

    path("configurar/",
        views.configurar,
        name="configurar"),

    path("relatorios",
        views.relatorios,
        name="relatorios"),

    path("exportar",
        views.exportar,
        name="exportar"),

    path("dados_backup",
        views.dados_backup,
        name="dados_backup"),

    path("dados_backup/<str:modo>",
        views.dados_backup,
        name="dados_backup"),

    path("export/<str:modelo>/<str:formato>",
        views.export,
        name="export"),

    path("propor/",
        views.propor,
        name="propor"),

    path("montar_grupos/",
        views.montar_grupos,
        name="montar_grupos"),

    path("relatorio/<str:modelo>/<str:formato>",
        views.relatorio,
        name="relatorio"),

    path("selecionar_orientadores/",
        views.selecionar_orientadores,
        name="selecionar_orientadores"),

    path("fechar_conexoes/",
        views.fechar_conexoes,
        name="fechar_conexoes"),

    path("servico/",
        views.servico,
        name="servico"),

    path("pre_alocar_estudante/",
        views.pre_alocar_estudante,
        name="pre_alocar_estudante"),

    path("estrela_estudante/",
        views.estrela_estudante,
        name="estrela_estudante"),

    path("ajax/definir_orientador/",
        views.definir_orientador,
        name="definir_orientador"),

    path("ajax/excluir_disciplina",
        views.excluir_disciplina,
        name="excluir_disciplina"),

    path("logs/<int:dias>",
        views.logs,
        name="logs"),

    path("logs/",
        views.logs,
        name="logs"),
    
    path("tarefas_agendadas/",
        views.tarefas_agendadas,
        name="tarefas_agendadas"),

    path("cancela_tarefa/<str:task_id>/",
        views.cancela_tarefa,
        name="cancel_task"),

    path("conexoes_estabelecidas/",
        views.conexoes_estabelecidas,
        name="conexoes_estabelecidas"),

    path("bloqueados/",
        views.bloqueados,
        name="bloqueados"),

]
