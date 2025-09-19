#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Janeiro de 2025
"""

import datetime

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from projetos.models import Banca, Encontro

from academica.support_notas import converte_letra

from academica.support3 import get_media_alocacao_i
from academica.support4 import get_banca_estudante
from academica.models import Exame

from projetos.models import Coorientador, Avaliacao2
from projetos.models import Banca, Evento
from projetos.models import Projeto, Configuracao

from users.models import Alocacao
from users.support import get_edicoes

def get_banca_incompleta(projeto, sigla, avaliadores):
    """Verifica se todas as avaliações da banca estão completas."""
    banca = Banca.objects.filter(projeto=projeto, composicao__exame__sigla=sigla).last()
    now = datetime.datetime.now()
    banca_incompleta = 0  # 0 se não há banca
    if banca:
        if avaliadores:  # 1 se existe banca
            if banca.membro1 and banca.membro1 not in avaliadores:
                banca_incompleta = 1
            if banca.membro2 and banca.membro2 not in avaliadores:
                banca_incompleta = 1
            if banca.membro3 and banca.membro3 not in avaliadores:
                banca_incompleta = 1

            if banca.composicao.exame.sigla in ["BF", "BI"]:
                if banca.projeto.orientador and banca.projeto.orientador.user not in avaliadores:
                    banca_incompleta = 1

            if banca_incompleta == 1:
                if (now - banca.endDate).days > 3:  # muito atrasada
                    banca_incompleta = 3
                elif (now - banca.endDate).days > 0:  # pouco atrasada
                    banca_incompleta = 2
        else:
            banca_incompleta = 1

    return banca_incompleta, banca


# Criei esse função temporária para tratar caso a edição seja passada diretamente na URL
def resultado_projetos_intern(request, ano=None, semestre=None, professor=None):
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            projetos = Projeto.objects.all()

            if edicao != "todas":
                ano, semestre = edicao.split('.')
                projetos = projetos.filter(ano=ano, semestre=semestre)

            show_orientador = True
            if professor is not None:
                # Incluindo também se coorientação
                coorientacoes = Coorientador.objects.filter(usuario=professor.user).values_list("projeto", flat=True)
                projetos_ori = projetos.filter(orientador=professor)
                projetos_coori = projetos.filter(id__in=coorientacoes)
                projetos = projetos_ori | projetos_coori
                if projetos_coori.count() == 0:
                    show_orientador = False

            notas = {}
            nomes_relatorios = ["Relatório Intermediário", "Relatório Final"]
            for nome in nomes_relatorios:
                notas[nome] = []
            nomes_bancas = [ ("Banca Final", "BF"), ("Banca Intermediária", "BI")]
            for nome in nomes_bancas:
                notas[nome[0]] = []

            for projeto in projetos:

                alocacoes = Alocacao.objects.filter(projeto=projeto)
                
                if alocacoes:

                    primeira = alocacoes.first()
                    medias = get_media_alocacao_i(primeira)

                    if ("peso_grupo_inter" in medias) and (medias["peso_grupo_inter"] is not None) and (medias["peso_grupo_inter"] > 0):
                        nota = medias["nota_grupo_inter"]/medias["peso_grupo_inter"]
                        nota_incompleta = 0  # Nota entregue
                        notas["Relatório Intermediário"].append({"conceito": "{0}".format(converte_letra(nota, espaco="&nbsp;")),
                                                "nota_texto": "{0:5.2f}".format(nota),
                                                "nota": nota,
                                                "certificacao": "",
                                                    "nota_incompleta": nota_incompleta})                    
                    else:

                        evento_r = Evento.get_evento(sigla="ERI", ano=projeto.ano, semestre=projeto.semestre)  # Entrega do Relatório Intermediário (Grupo e Individual)
                        evento_b = Evento.get_evento(sigla="BI", ano=projeto.ano, semestre=projeto.semestre)  # Bancas Intermediárias

                        if evento_r:
                            atraso_r = (datetime.date.today() - evento_r.endDate).days
                            atraso_b = (datetime.date.today() - evento_b.endDate).days
                            if  atraso_b > 7:  # muito atrasada
                                nota_incompleta = 3
                            elif atraso_r > 0:  # pouco atrasada
                                nota_incompleta = 2
                            elif atraso_r == 0:  # No dia
                                nota_incompleta = 1
                            else:  # Antes do prazo
                                nota_incompleta = 0
                        else:
                            nota_incompleta = 0  # Sem evento
                        notas["Relatório Intermediário"].append({"conceito": "&nbsp;-&nbsp;",
                                                    "nota_texto": "",
                                                    "nota": 0,
                                                    "certificacao": "",
                                                    "nota_incompleta": nota_incompleta})

                    if ("peso_grupo_final" in medias) and (medias["peso_grupo_final"] is not None) and (medias["peso_grupo_final"] > 0):
                        nota = medias["nota_grupo_final"]/medias["peso_grupo_final"]
                        nota_incompleta = 0  # Nota entregue
                        notas["Relatório Final"].append({"conceito": "{0}".format(converte_letra(nota, espaco="&nbsp;")),
                                                "nota_texto": "{0:5.2f}".format(nota),
                                                "nota": nota,
                                                "certificacao": "",
                                                "nota_incompleta": nota_incompleta})                    
                    else:

                        evento_r = Evento.get_evento(sigla="ERF", ano=projeto.ano, semestre=projeto.semestre)  # Entrega do Relatório Final (Grupo e Individual)
                        evento_b = Evento.get_evento(sigla="BF", ano=projeto.ano, semestre=projeto.semestre)  # Bancas Finais

                        if evento_r:
                            atraso_r = (datetime.date.today() - evento_r.endDate).days
                            atraso_b = (datetime.date.today() - evento_b.endDate).days
                            if  atraso_b > 7:  # muito atrasada
                                nota_incompleta = 3
                            elif atraso_r > 0:  # pouco atrasada
                                nota_incompleta = 2
                            elif atraso_r == 0:  # No dia
                                nota_incompleta = 1
                            else:  # Antes do prazo
                                nota_incompleta = 0
                        else:
                            nota_incompleta = 0  # Sem evento
                        notas["Relatório Final"].append({"conceito": "&nbsp;-&nbsp;",
                                                    "nota_texto": "",
                                                    "nota": 0,
                                                    "certificacao": "",
                                                    "nota_incompleta": nota_incompleta})
 
                else:
                    notas["Relatório Intermediário"].append(("&nbsp;-&nbsp;", None, 0))
                    notas["Relatório Final"].append(("&nbsp;-&nbsp;", None, 0))
                
                for titulo_aval in nomes_bancas:
                    exame = Exame.objects.get(titulo=titulo_aval[0])
                    aval_b = Avaliacao2.objects.filter(projeto=projeto, exame=exame)  # Por Bancas
                    banca_info = get_banca_estudante(aval_b, ano=projeto.ano, semestre=projeto.semestre)
                    nota_b = banca_info["media"]
                    peso = banca_info["peso"]
                    avaliadores = banca_info["avaliadores"]


                    nota_incompleta, _ = get_banca_incompleta(projeto=projeto, sigla=titulo_aval[1], avaliadores=avaliadores)

                    if peso is not None:
                        notas[titulo_aval[0]].append({"conceito": "{0}".format(converte_letra(nota_b, espaco="&nbsp;")),
                                                    "nota_texto": "{0:5.2f}".format(nota_b),
                                                    "nota": nota_b,
                                                    "certificacao": "",
                                                    "nota_incompleta": nota_incompleta})                    
                    else:
                        notas[titulo_aval[0]].append({"conceito": "&nbsp;-&nbsp;",
                                                    "nota_texto": "",
                                                    "nota": 0,
                                                    "certificacao": "",
                                                    "nota_incompleta": nota_incompleta})

            tabela = zip(projetos,
                         notas["Relatório Intermediário"],
                         notas["Relatório Final"],
                         notas["Banca Intermediária"],
                         notas["Banca Final"],
                        #  notas["Falconi"],
                         )

            context = {
                    "tabela": tabela,
                    "edicao": edicao,
                    "show_orientador": show_orientador,
                }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:
        edicoes = get_edicoes(Projeto)[0]

        if ano and semestre:
            selecionada_edicao = str(ano) + "." + str(semestre)
        else:
            configuracao = get_object_or_404(Configuracao)
            selecionada_edicao = "{0}.{1}".format(configuracao.ano, configuracao.semestre)

        informacoes = [
            ("#ProjetosTable tr > *:nth-child(2)", "Período", "Semester"),
            ("#ProjetosTable tr > *:nth-child(3)", "Orientador", "Advisor"),
            ("""#ProjetosTable tr > *:nth-child(4),
                #ProjetosTable tr > *:nth-child(5),
                #ProjetosTable tr > *:nth-child(6),
                #ProjetosTable tr > *:nth-child(7)""", "Notas", "Grades"),
            (".grupo", "Grupo", "Group"),
            (".email", "e-mail", "e-mail", "grupo"),
            (".curso", "curso", "program", "grupo"),
        ]

        context = {
            "titulo": {"pt": "Resultado dos Projetos", "en": "Projects Results"},
            "edicoes": edicoes,
            "selecionada_edicao": selecionada_edicao,
            "informacoes": informacoes,
        }

    return render(request, "professores/resultado_projetos.html", context)


def puxa_encontros(edicao):
    """Puxa os encontros/mentorias de acordo com a edição selecionada."""
    projeto = None
    encontros = Encontro.objects.all().order_by("startDate")
    if edicao == "todas":
        pass  # segue com encontros
    elif edicao == "proximas":
        hoje = datetime.date.today()
        encontros = encontros.filter(startDate__gt=hoje)
    elif '.' in edicao:
        ano, semestre = map(int, edicao.split('.'))

        encontros = encontros.filter(startDate__year=ano)
        if semestre == 1:
            encontros = encontros.filter(startDate__month__lt=8)
        else:
            encontros = encontros.filter(startDate__month__gt=7)
    else:
        projeto = get_object_or_404(Projeto, id=edicao)
        encontros = encontros.filter(projeto=projeto)

    # checando se projetos atuais tem banca marcada
    configuracao = get_object_or_404(Configuracao)
    sem_dinamicas = Projeto.objects.filter(ano=configuracao.ano,
                                    semestre=configuracao.semestre)
    for encontro in encontros:
        if encontro.projeto:
            sem_dinamicas = sem_dinamicas.exclude(id=encontro.projeto.id)

    context = {
        "encontros": encontros,
        "sem_dinamicas": sem_dinamicas,
        "projeto": projeto,
        "edicao": edicao,
    }
    return context


def puxa_bancas(edicao):
    """Puxa as bancas de acordo com a edição selecionada."""
    sem_banca = []
    projeto = None
    configuracao = get_object_or_404(Configuracao)
    if edicao == "proximas":
        # Coletando bancas agendadas a partir de hoje
        hoje = datetime.date.today()
        bancas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")

        # checando se projetos atuais tem banca marcada
        projetos = Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre)
        for banca in bancas:
            if banca.projeto:
                projetos = projetos.exclude(id=banca.projeto.id)
        sem_banca = projetos

    elif edicao == "todas":
        bancas = Banca.objects.all().order_by("startDate")

    elif '.' in edicao:
        ano, semestre = map(int, edicao.split('.'))
        bancas_p = Banca.objects.filter(projeto__ano=ano, projeto__semestre=semestre)
        bancas_a = Banca.objects.filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre)
        bancas = (bancas_p | bancas_a).order_by("startDate")

    else:
        projeto = get_object_or_404(Projeto, id=edicao)
        bancas = Banca.objects.filter(projeto=projeto).order_by("startDate")

    context = {
        "bancas": bancas,
        "sem_banca": sem_banca,
        "projeto": projeto,
        "edicao": edicao,
    }
    return context