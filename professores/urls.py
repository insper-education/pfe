#!/usr/bin/env python
# pylint: disable=C0103
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

from django.urls import path

from . import views

urlpatterns = [

    # pagina inicial
    path("",
         views.index_professor,
         name="index_professor"),

     path("professores",
         views.index_professor,
         name="professores"),

    path("avaliacoes_pares/",
         views.avaliacoes_pares,
         name="avaliacoes_pares"),

    path("avaliacoes_pares/<str:todos>",
         views.avaliacoes_pares,
         name="avaliacoes_pares"),

    path("avaliar_entregas/",
         views.avaliar_entregas,
         name="avaliar_entregas"),

    path("avaliar_entregas/<str:selecao>",
         views.avaliar_entregas,
         name="avaliar_entregas"),

    path("bancas_alocadas/",
         views.bancas_alocadas,
         name="bancas_alocadas"),

    path("orientacoes_alocadas/",
        views.orientacoes_alocadas,
        name="orientacoes_alocadas"),

    path("coorientacoes_alocadas/",
        views.coorientacoes_alocadas,
        name="coorientacoes_alocadas"),

    path("mentorias_alocadas/",
        views.mentorias_alocadas,
        name="mentorias_alocadas"),

    path("bancas_criar/",
         views.bancas_criar,
         name="bancas_criar"),

    path("bancas_criar/<str:data>",
         views.bancas_criar,
         name="bancas_criar"),

    path("bancas_editar/",
         views.bancas_editar,
         name="bancas_editar"),

    path("bancas_editar/<int:primarykey>",
         views.bancas_editar,
         name="bancas_editar"),

    path("mensagem_email/<str:tipo>/<int:primarykey>",
         views.mensagem_email,
         name="mensagem_email"),

    path("banca_ver/<int:primarykey>",
         views.banca_ver,
         name="banca_ver"),

    path("bancas_index/",
         views.bancas_index,
         name="bancas_index"),

    path("bancas_lista/<str:periodo_projeto>",
         views.bancas_lista,
         name="bancas_lista"),

    path("bancas_tabela/",
         views.bancas_tabela,
         name="bancas_tabela"),

    path("mentorias_tabela/",
         views.mentorias_tabela,
         name="mentorias_tabela"),

    path("aulas_tabela/",
         views.aulas_tabela,
         name="aulas_tabela"),

     path("banca/<slug:slug>",
         views.banca,
         name="banca"),

    path("bancas_tabela_completa/",
         views.bancas_tabela_completa,
         name="bancas_tabela_completa"),

    path("banca_avaliar/<slug:slug>",
         views.banca_avaliar,
         name="banca_avaliar"),

    path("banca_avaliar/<slug:slug>/<int:documento_id>",
         views.banca_avaliar,
         name="banca_avaliar"),

    path("entrega_avaliar/<int:composicao_id>/<int:projeto_id>",
         views.entrega_avaliar,
         name="entrega_avaliar"),

    path("entrega_avaliar/<int:composicao_id>/<int:projeto_id>/<int:estudante_id>",
         views.entrega_avaliar,
         name="entrega_avaliar"),

    path("conceitos_obtidos/<int:primarykey>",
         views.conceitos_obtidos,
         name="conceitos_obtidos"),

    path("coorientadores_tabela_completa/",
         views.coorientadores_tabela_completa,
         name="coorientadores_tabela_completa"),

    path("coorientadores_tabela/",
         views.coorientadores_tabela,
         name="coorientadores_tabela"),

    path("dinamicas_index/",
         views.dinamicas_index,
         name="dinamicas_index"),

    path("dinamicas_criar/",
         views.dinamicas_criar,
         name="dinamicas_criar"),

    path("dinamicas_criar/<str:data>",
         views.dinamicas_criar,
         name="dinamicas_criar"),

    path("dinamicas_editar/",
         views.dinamicas_editar,
         name="dinamicas_editar"),

    path("dinamicas_editar/<int:primarykey>",
         views.dinamicas_editar,
         name="dinamicas_editar"),

    path("dinamicas_lista/",
         views.dinamicas_lista,
         name="dinamicas_lista"),

    path("informe_bancas/<int:tipo>",
         views.informe_bancas,
         name="informe_bancas"),

    path("objetivo_editar/<int:primarykey>",
         views.objetivo_editar,
         name="objetivo_editar"),

    path("objetivos_rubricas/",
         views.objetivos_rubricas,
         name="objetivos_rubricas"),
     
    path("orientadores_tabela/",
         views.orientadores_tabela,
         name="orientadores_tabela"),

    path("orientadores_tabela_completa/",
         views.orientadores_tabela_completa,
         name="orientadores_tabela_completa"),

    path("relato_avaliar/<int:projeto_id>/<int:evento_id>",
         views.relato_avaliar,
         name="relato_avaliar"),

    path("relatos_quinzenais/",
         views.relatos_quinzenais,
         name="relatos_quinzenais"),

    path("relatos_quinzenais/<str:todos>",
         views.relatos_quinzenais,
         name="relatos_quinzenais"),

    path("planos_de_orientacao_todos/",
         views.planos_de_orientacao_todos,
         name="planos_de_orientacao_todos"),

     path("planos_de_orientacao/",
         views.planos_de_orientacao,
         name="planos_de_orientacao"),

    path("resultado_meus_projetos/",
         views.resultado_meus_projetos,
         name="resultado_meus_projetos"),

    path("resultado_projetos/",
         views.resultado_projetos,
         name="resultado_projetos"),

    path("resultado_projetos/<str:edicao>",
         views.resultado_projetos_edicao,
         name="resultado_projetos_edicao"),

    path("todos_professores/",
         views.todos_professores,
         name="todos_professores"),

    path("ver_pares/<int:alocacao_id>/<str:momento>",
         views.ver_pares,
         name="ver_pares"),

    path("ver_pares_projeto/<int:projeto_id>/<str:momento>",
         views.ver_pares_projeto,
         name="ver_pares_projeto"),

     path("ajax_bancas/",
         views.ajax_bancas,
         name="ajax_bancas"),

     path("ajax_atualiza_banca/",
         views.ajax_atualiza_banca,
         name="ajax_atualiza_banca"),

     path("ajax_atualiza_dinamica/",
         views.ajax_atualiza_dinamica,
         name="ajax_atualiza_dinamica"),

]
