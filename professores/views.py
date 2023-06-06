#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import datetime
import dateutil.parser

from urllib.parse import quote, unquote

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.utils import html

from users.models import PFEUser, Professor, Aluno, Alocacao
from users.support import get_edicoes

from projetos.models import Coorientador, ObjetivosDeAprendizagem, Avaliacao2, Observacao
from projetos.models import Banca, Evento, Encontro
from projetos.models import Projeto, Configuracao, Organizacao
from projetos.support import converte_letra, converte_conceito
from projetos.support import get_objetivos_atuais
from projetos.messages import email

from .support import professores_membros_bancas, falconi_membros_banca
from .support import editar_banca
from .support import recupera_orientadores_por_semestre
from .support import recupera_coorientadores_por_semestre

from estudantes.models import Relato, Pares

@login_required
@permission_required("users.altera_professor", login_url='/')
def index_professor(request):
    """Mostra página principal do usuário professor."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)

    if user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
        mensagem = "Você não está cadastrado como professor!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    professor_id = 0
    try:
        professor_id = Professor.objects.get(pk=request.user.professor.pk).id
    except Professor.DoesNotExist:
        pass
        # Administrador não possui também conta de professor

    context = {
        'professor_id': professor_id,
    }
    return render(request, 'professores/index_professor.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def avaliacoes_pares(request):
    """Formulários com os projetos e avaliações de pares."""

    user = get_object_or_404(PFEUser, pk=request.user.pk)

    configuracao = get_object_or_404(Configuracao)

    projetos = Projeto.objects.filter(orientador=user.professor, ano=configuracao.ano, semestre=configuracao.semestre)

    context = {
        "user": user,
        "projetos": projetos,
    }

    return render(request, 'professores/avaliacoes_pares.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/')
def avaliacoes_pares_todas(request):
    """Formulários com os projetos e relatos a avaliar do professor orientador."""

    if request.is_ajax():

        if 'edicao' in request.POST:

            projetos = Projeto.objects.all()

            edicao = request.POST['edicao']
            if edicao != 'todas':
                periodo = request.POST['edicao'].split('.')
                ano = int(periodo[0])
                semestre = int(periodo[1])
                projetos = projetos.filter(ano=ano, semestre=semestre)
                
            context = {
                "administracao": True,
                "projetos": projetos,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:

        edicoes, _, _ = get_edicoes(Projeto)
        context = {
                "administracao": True,
                "edicoes": edicoes,
            }

    return render(request, 'professores/avaliacoes_pares.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def bancas_alocadas(request):
    """Mostra detalhes sobre o professor."""
    professor = get_object_or_404(Professor, pk=request.user.professor.pk)

    bancas = (Banca.objects.filter(membro1=professor.user) |
              Banca.objects.filter(membro2=professor.user) |
              Banca.objects.filter(membro3=professor.user))

    bancas = bancas.order_by("-startDate")

    context = {
        'professor': professor,
        'bancas': bancas,
    }

    return render(request, 'professores/bancas_alocadas.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/')
def orientacoes_alocadas(request):
    """Mostra detalhes sobre o professor."""
    professor = get_object_or_404(Professor, pk=request.user.professor.pk)

    projetos = Projeto.objects.filter(orientador=professor)\
        .order_by("-ano", "-semestre", "titulo")

    context = {
        'professor': professor,
        'projetos': projetos,
    }

    return render(request, 'professores/orientacoes_alocadas.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/')
def coorientacoes_alocadas(request):
    """Mostra detalhes sobre o professor."""
    professor = get_object_or_404(Professor, pk=request.user.professor.pk)

    coorientacoes = Coorientador.objects.filter(usuario=professor.user)\
        .order_by("-projeto__ano",
                  "-projeto__semestre",
                  "projeto__titulo")

    context = {
        'professor': professor,
        'coorientacoes': coorientacoes,
    }

    return render(request, 'professores/coorientacoes_alocadas.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/')
def mentorias_alocadas(request):
    """Mostra detalhes sobre o professor."""
    professor = get_object_or_404(Professor, pk=request.user.professor.pk)

    mentorias = Encontro.objects.filter(facilitador=professor.user)\
        .order_by('startDate')

    context = {
        'professor': professor,
        'mentorias': mentorias,
    }

    return render(request, 'professores/mentorias_alocadas.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def bancas_index(request):
    """Menus de bancas e calendario de bancas."""
    bancas = Banca.objects.all()

    # (14, 'Banca intermediária'
    dias_bancas_interm = Evento.objects.filter(tipo_de_evento=14)

    # (15, 'Bancas finais'
    dias_bancas_finais = Evento.objects.filter(tipo_de_evento=15)

    # (50, 'Certificação Falconi'
    dias_bancas_falcon = Evento.objects.filter(tipo_de_evento=50)

    dias_bancas = (dias_bancas_interm |
                   dias_bancas_finais |
                   dias_bancas_falcon)

    context = {
        'bancas': bancas,
        'dias_bancas': dias_bancas,
    }

    return render(request, 'professores/bancas_index.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def bancas_criar(request):
    """Cria uma banca de avaliação para o projeto."""
    configuracao = get_object_or_404(Configuracao)

    if request.method == 'POST':
        if 'projeto' in request.POST:
            projeto = get_object_or_404(Projeto,
                                        id=int(request.POST['projeto']))

            banca = Banca.create(projeto)
            editar_banca(banca, request)
            mensagem = "Banca criada.<br><br>"

            mensagem += "Data: " + banca.startDate.strftime("%d/%m/%Y - %H:%M:%S") + "<br><br>"

            mensagem += "Envolvidos:<br><ul>"

            # Orientador
            if banca.projeto.orientador:
                mensagem += "<li>" + banca.projeto.orientador.user.get_full_name() + " [orientador] "
                mensagem += '<a href="mailto:' + banca.projeto.orientador.user.email + '">&lt;' + banca.projeto.orientador.user.email + "&gt;</a></li>"
            
            # coorientadores
            for coorientador in banca.projeto.coorientador_set.all():
                mensagem += "<li>" + coorientador.usuario.get_full_name() + " [coorientador] "
                mensagem += '<a href="mailto:' + coorientador.usuario.email + '">&lt;' + coorientador.usuario.email + "&gt;</a></li>"

            # membro1
            if banca.membro1:
                mensagem += "<li>" + banca.membro1.get_full_name() + " [membro da banca] "
                mensagem += '<a href="mailto:' + banca.membro1.email + '">&lt;' + banca.membro1.email + "&gt;</a></li>"
            
            # membro2
            if banca.membro2:
                mensagem += "<li>" + banca.membro2.get_full_name() + " [membro da banca] "
                mensagem += '<a href="mailto:' + banca.membro2.email + '">&lt;' + banca.membro2.email + "&gt;</a></li>"

            # membro3
            if banca.membro3:
                mensagem += "<li>" + banca.membro3.get_full_name() + " [membro da banca] "
                mensagem += '<a href="mailto:' + banca.membro3.email + '">&lt;' + banca.membro3.email + "&gt;</a></li>"

            # estudantes
            for alocacao in banca.projeto.alocacao_set.all():
                mensagem += "<li>" + alocacao.aluno.user.get_full_name()
                mensagem += "[" + str(alocacao.aluno.curso2) + "] "
                mensagem += '<a href="mailto:' + alocacao.aluno.user.email + '">&lt;' + alocacao.aluno.user.email + "&gt;</a></li>"
            
            mensagem += "</ul>"
            
            context = {
                "area_principal": True,
                "bancas_index": True,
                "agendar_banca": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Banca não registrada, erro identificando projeto")

    ano = configuracao.ano
    semestre = configuracao.semestre
    projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

    professores, _ = professores_membros_bancas()
    falconis, _ = falconi_membros_banca()

    # Coletando bancas agendadas a partir de hoje
    hoje = datetime.date.today()
    bancas_agendadas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")
    projetos_agendados = list(bancas_agendadas.values_list('projeto', flat=True))

    context = {
        'projetos': projetos,
        'professores': professores,
        "TIPO_DE_BANCA": Banca.TIPO_DE_BANCA,
        "falconis": falconis,
        "projetos_agendados": projetos_agendados,
    }
    return render(request, 'professores/bancas_editar.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def bancas_editar(request, primarykey):
    """Edita uma banca de avaliação para o projeto."""
    banca = get_object_or_404(Banca, pk=primarykey)

    if request.method == 'POST':

        context = {"mensagem": "Algum problema ocorreu!",}
        if 'atualizar' in request.POST:
            if editar_banca(banca, request):
                mensagem = "Banca editada."
            else:
                mensagem = "Erro ao Editar banca."
            context = {
                "area_principal": True,
                "bancas_index": True,
                "mensagem": mensagem,
            }
        elif 'excluir' in request.POST:
            context = {"mensagem": "Banca excluída!",}
            if 'projeto' in request.POST:
                banca.delete()

        return render(request, 'generic.html', context=context)

    projetos = Projeto.objects.exclude(orientador=None)\
        .order_by("-ano", "-semestre")

    professores, _ = professores_membros_bancas()
    falconis, _ = falconi_membros_banca()

    context = {
        'projetos': projetos,
        'professores': professores,
        'banca': banca,
        "TIPO_DE_BANCA": Banca.TIPO_DE_BANCA,
        "falconis": falconis,
    }
    return render(request, 'professores/bancas_editar.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def bancas_lista(request, periodo_projeto):
    """Lista as bancas agendadas, conforme periodo ou projeto pedido."""
    context = {'periodo': periodo_projeto}

    if periodo_projeto == "proximas":
        # Coletando bancas agendadas a partir de hoje
        hoje = datetime.date.today()
        bancas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")

        # checando se projetos atuais tem banca marcada
        configuracao = get_object_or_404(Configuracao)
        projetos = Projeto.objects.filter(ano=configuracao.ano,
                                          semestre=configuracao.semestre)
        for banca in bancas:
            projetos = projetos.exclude(id=banca.projeto.id)
        context["sem_banca"] = projetos

    elif periodo_projeto == "todas":
        bancas = Banca.objects.all().order_by("startDate")

    elif '.' in periodo_projeto:
        periodo = periodo_projeto.split('.')
        try:
            ano = int(periodo[0])
            semestre = int(periodo[1])
        except ValueError:
            return HttpResponseNotFound('<h1>Erro em!</h1>')

        bancas = Banca.objects.filter(projeto__ano=ano)\
            .filter(projeto__semestre=semestre).order_by("startDate")

    else:
        projeto = get_object_or_404(Projeto, id=periodo_projeto)
        context["projeto"] = projeto
        bancas = Banca.objects.filter(projeto=projeto).order_by("startDate")

    context["bancas"] = bancas

    edicoes, _, _ = get_edicoes(Projeto)
    context["edicoes"] = edicoes
    
    return render(request, 'professores/bancas_lista.html', context)



@login_required
@permission_required('users.altera_professor', login_url='/')
def bancas_tabela(request):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']

            if edicao == 'todas':
                bancas = Banca.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                if semestre == "1/2":
                    bancas = Banca.objects.filter(projeto__ano=ano)
                else:
                    bancas = Banca.objects.all().filter(projeto__ano=ano).filter(projeto__semestre=semestre)

            membros = dict()
            
            for banca in bancas:
                if banca.projeto.orientador:
                    if banca.tipo_de_banca != 2:  # Nao eh Falconi
                        membros.setdefault(banca.projeto.orientador.user, []).append(banca)
                if banca.membro1:
                    membros.setdefault(banca.membro1, []).append(banca)
                if banca.membro2:
                    membros.setdefault(banca.membro2, []).append(banca)
                if banca.membro3:
                    membros.setdefault(banca.membro3, []).append(banca)

        context = {
            "membros": membros,
        }

    else:
        edicoes, _, _ = get_edicoes(Projeto, anual=True)
        context = {
            "edicoes": edicoes,
        }

    return render(request, 'professores/bancas_tabela.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def bancas_tabela_completa(request):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    configuracao = get_object_or_404(Configuracao)

    membros_pfe = []
    periodo = []

    ano = 2018
    semestre = 2
    while True:
        membros = dict()
        bancas = Banca.objects.all().filter(projeto__ano=ano)\
            .filter(projeto__semestre=semestre)
        for banca in bancas:
            if banca.projeto.orientador:
                membros.setdefault(banca.projeto.orientador.user, [])\
                    .append(banca)
            if banca.membro1:
                membros.setdefault(banca.membro1, []).append(banca)
            if banca.membro2:
                membros.setdefault(banca.membro2, []).append(banca)
            if banca.membro3:
                membros.setdefault(banca.membro3, []).append(banca)

        membros_pfe.append(membros)
        periodo.append(str(ano)+"."+str(semestre))

        if ((ano == configuracao.ano) and (semestre == configuracao.semestre)):
            break

        if semestre == 2:
            semestre = 1
            ano += 1
        else:
            semestre = 2

    # inverti lista deixando os mais novos primeiro
    anos = zip(membros_pfe[::-1], periodo[::-1])

    context = {
        'anos': anos,
    }

    return render(request, 'professores/bancas_tabela_completa.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def banca_ver(request, primarykey):
    """Retorna banca pedida."""
    banca = get_object_or_404(Banca, id=primarykey)

    context = {
        'banca': banca,
    }

    return render(request, 'professores/banca_ver.html', context)


# Mensagem preparada para o avaliador
def mensagem_avaliador(banca, avaliador, julgamento, julgamento_observacoes, objetivos_possiveis, realizada):
    message = "<h3>Avaliação PFE</h3><br>\n"

    if realizada:
        message += "<h3 style='color:red;text-align:center;'>"
        message += "Essa é uma atualização de uma avaliação já enviada anteriormente!"
        message += "</h3><br><br>"

    message += "<b>Título do Projeto:</b> {0}<br>\n".format(banca.projeto.get_titulo())
    message += "<b>Organização:</b> {0}<br>\n".format(banca.projeto.organizacao)
    message += "<b>Orientador:</b> {0}<br>\n".format(banca.projeto.orientador)
    message += "<b>Avaliador:</b> {0}<br>\n".format(avaliador.get_full_name())
    message += "<b>Data:</b> {0}<br>\n".format(banca.startDate.strftime("%d/%m/%Y %H:%M"))

    message += "<b>Banca:</b> "
    tipos = dict(Banca.TIPO_DE_BANCA)
    if banca.tipo_de_banca in tipos:
        message += tipos[banca.tipo_de_banca]
    else:
        message += "Tipo de banca não definido"

    message += "<br>\n<br>\n"
    message += "<b>Conceitos:</b><br>\n"
    message += "<table style='border: 1px solid black; "
    message += "border-collapse:collapse; padding: 0.3em;'>"

    for i in range(objetivos_possiveis):
        if julgamento[i] and not julgamento[i].na:
            message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                format(julgamento[i].objetivo)
            message += "<td style='border: 1px solid black; text-align:center'>"
            message += "&nbsp;{0}&nbsp;</td>\n".\
                format(converte_letra(julgamento[i].nota))

    message += "</table>"

    message += "<br>\n<br>\n"

    if julgamento_observacoes:
        message += "<b>Observações (somente enviada para orientador):</b>\n"
        message += "<p style='border:1px; border-style:solid; padding: 0.3em; margin: 0;'>"
        message += html.escape(julgamento_observacoes.observacoes).replace('\n', '<br>\n')
        message += "</p>"
        message += "<br>\n<br>\n"

    # Criar link para reeditar
    message += "<a href='" + settings.SERVER
    message += "/professores/banca_avaliar/" + str(banca.slug)

    message += "?avaliador=" + str(avaliador.id)
    for count, julg in enumerate(julgamento):
        if julg and not julg.na:
            message += "&objetivo" + str(count) + "=" + str(julg.objetivo.id)
            message += "&conceito" + str(count) + "=" + converte_letra(julg.nota, mais="X")
    if julgamento_observacoes:
        message += "&observacoes=" + quote(julgamento_observacoes.observacoes)
    message += "'>"
    message += "Caso deseje reenviar sua avaliação, clique aqui."
    message += "</a><br>\n"
    message += "<br>\n"

    # Relistar os Objetivos de Aprendizagem
    message += "<br><b>Objetivos de Aprendizagem</b>"

    for julg in julgamento:

        if julg:

            message += "<br><b>{0}</b>: {1}".format(julg.objetivo.titulo, julg.objetivo.objetivo)
            message += "<table "
            message += "style='border:1px solid black; border-collapse:collapse; width:100%;'>"
            message += "<tr>"

            if (not julg.na) and converte_letra(julg.nota) == "I":
                message += "<td style='border: 2px solid black; width:18%;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Insatisfatório (I)</th>"

            if (not julg.na) and converte_letra(julg.nota) == "D":
                message += "<td style='border: 2px solid black; width:18%;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Em Desenvolvimento (D)</th>"

            if (not julg.na) and (converte_letra(julg.nota) == "C" or converte_letra(julg.nota) == "C+"):
                message += "<td style='border: 2px solid black; width:18%;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Essencial (C/C+)</th>"

            if (not julg.na) and (converte_letra(julg.nota) == "B" or converte_letra(julg.nota) == "B+"):
                message += "<td style='border: 2px solid black; width:18%;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Proficiente (B/B+)</th>"

            if (not julg.na) and (converte_letra(julg.nota) == "A" or converte_letra(julg.nota) == "A+"):
                message += "<td style='border: 2px solid black; width:18%;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black; width:18%;'>"
            message += "Avançado (A/A+)</th>"

            message += "</tr>"
            message += "<tr>"

            if (not julg.na) and converte_letra(julg.nota) == "I":
                message += "<td style='border: 2px solid black;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_I)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_I)
            message += "</td>"

            if (not julg.na) and (converte_letra(julg.nota) == "D-" or converte_letra(julg.nota) == "D" or converte_letra(julg.nota) == "D+"):
                message += "<td style='border: 2px solid black;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_D)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_D)
            message += "</td>"

            if (not julg.na) and (converte_letra(julg.nota) == "C" or converte_letra(julg.nota) == "C+"):
                message += "<td style='border: 2px solid black;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_C)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_C)
            message += "</td>"

            if (not julg.na) and (converte_letra(julg.nota) == "B" or converte_letra(julg.nota) == "B+"):
                message += "<td style='border: 2px solid black;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_B)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_B)
            message += "</td>"

            if (not julg.na) and (converte_letra(julg.nota) == "A" or converte_letra(julg.nota) == "A+"):
                message += "<td style='border: 2px solid black;"
                message += " background-color: #F4F4F4;'>"
            else:
                message += "<td style='border: 1px solid black;'>"
            if banca.tipo_de_banca == 1:
                message += "{0}".format(julg.objetivo.rubrica_intermediaria_A)
            else:
                message += "{0}".format(julg.objetivo.rubrica_final_A)
            message += "</td>"

            message += "</tr>"
            message += "</table>"

    return message

def converte_conceitos(nota):
    if( nota >= 9.5 ): return ("A+")
    if( nota >= 8.5 ): return ("A")
    if( nota >= 7.5 ): return ("B+")
    if( nota >= 6.5 ): return ("B")
    if( nota >= 5.5 ): return ("C+")
    if( nota >= 4.5 ): return ("C")
    if( nota >= 3.5 ): return ("D+")
    if( nota >= 2.5 ): return ("D")
    if( nota >= 1.5 ): return ("D-")
    return ("I")

def arredonda_conceitos(nota):
    if( nota >= 9.5 ): return 10
    if( nota >= 8.5 ): return 9
    if( nota >= 7.5 ): return 8
    if( nota >= 6.5 ): return 7
    if( nota >= 5.5 ): return 6
    if( nota >= 4.5 ): return 5
    if( nota >= 3.5 ): return 4
    if( nota >= 2.5 ): return 3
    if( nota >= 1.5 ): return 2
    return 0

# Mensagem preparada para o orientador/coordenador
def mensagem_orientador(banca):
    message = "<h3>Informe de Avaliação de Banca PFE</h3><br>\n"

    message += "<b>Título do Projeto:</b> {0}<br>\n".format(banca.projeto.get_titulo())
    message += "<b>Organização:</b> {0}<br>\n".format(banca.projeto.organizacao)
    message += "<b>Orientador:</b> {0}<br>\n".format(banca.projeto.orientador)
    message += "<b>Data:</b> {0}<br>\n".format(banca.startDate.strftime("%d/%m/%Y %H:%M"))

    message += "<b>Banca:</b> "
    tipos = dict(Banca.TIPO_DE_BANCA)
    if banca.tipo_de_banca in tipos:
        message += tipos[banca.tipo_de_banca]
    else:
        message += "Tipo de banca não definido"

    message += "<br><br><b style='color: bloodred; font-size: 1.5em;'>"
    message += "AGUARDE TODOS OS MEMBROS DA BANCA FAZEREM SUAS AVALIAÇÕES.<br>"
    message += "INSIRA AS MÉDIAS CALCULADAS DOS CONCEITOS NO CAMPO DA BANCA NO BLACKBOARD.<br>"
    message += "NÃO ALTERE A NOTA FINAL NO BLACKBOARD MANUALMENTE!<br>"
    message += "</b>"

    message += "Em caso de dúvia nas avaliações mais recentes, consulte: "
    message += "<a href='http://pfe.insper.edu.br/professores/conceitos_obtidos/" + str(banca.projeto.id) + "'>"
    message += "http://pfe.insper.edu.br/professores/conceitos_obtidos/" + str(banca.projeto.id) + "</a>"

    objetivos = ObjetivosDeAprendizagem.objects.all()

    avaliadores = {}

    if banca.tipo_de_banca == 0: #Final
        tipo_de_avaliacao = 2 #Final
    elif banca.tipo_de_banca == 1: #Iterm
        tipo_de_avaliacao = 1 #Iterm
    elif banca.tipo_de_banca == 2: #Falconi
        tipo_de_avaliacao = 99 #Falconi
    else:
        tipo_de_avaliacao = 200 #Erro
    
    for objetivo in objetivos:

        avaliacoes = Avaliacao2.objects.filter(projeto=banca.projeto,
                                                 objetivo=objetivo,
                                                 tipo_de_avaliacao=tipo_de_avaliacao)\
            .order_by('avaliador', '-momento')

        for avaliacao in avaliacoes:
            if avaliacao.avaliador not in avaliadores:
                avaliadores[avaliacao.avaliador] = {}
            if objetivo not in avaliadores[avaliacao.avaliador]:
                avaliadores[avaliacao.avaliador][objetivo] = avaliacao
                avaliadores[avaliacao.avaliador]["momento"] = avaliacao.momento

    observacoes = Observacao.objects.filter(projeto=banca.projeto, tipo_de_avaliacao=tipo_de_avaliacao).\
        order_by('avaliador', '-momento')
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores:
            avaliadores[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes" not in avaliadores[observacao.avaliador]:
            avaliadores[observacao.avaliador]["observacoes"] = observacao.observacoes

    message += "<br><br>"

    obj_avaliados = {}

    message += "<table>"

    message2 = ""  # Para inverter a ordem de apresentação

    for avaliador, objs in avaliadores.items():
          
        message2 += "<tr><td>"

        message2 += "<strong>Avaliador"
        if avaliador.genero == "F":
             message2 += "a"
        message2 += ": </strong>"
        message2 += avaliador.get_full_name() + "<br>"

        message2 += "<strong>Avaliado em: </strong>"
        message2 += objs["momento"].strftime('%d/%m/%Y às %H:%M') + "<br>"

        message2 += "<strong>Conceitos:</strong><br>"

        message2 += "<ul style='margin-top: 0px;'>"

        for objetivo, conceito in objs.items():
            if objetivo != "momento" and objetivo != "observacoes":
                message2 += "<li>"
                message2 += objetivo.titulo
                message2 += " : "
                if conceito.nota:
                    message2 += converte_conceitos(conceito.nota)                
                    message2 += "</li>"
                    if objetivo.titulo in obj_avaliados:
                        obj_avaliados[objetivo.titulo]["nota"] += conceito.nota
                        obj_avaliados[objetivo.titulo]["qtd"] += 1
                    else:
                        obj_avaliados[objetivo.titulo] = {}
                        obj_avaliados[objetivo.titulo]["nota"] = conceito.nota
                        obj_avaliados[objetivo.titulo]["qtd"] = 1
                else:
                    message2 += "N/A</li>"

        if "observacoes" in objs and objs["observacoes"]:
            message2 += "<li>Observações: " + objs["observacoes"] + "</li>"

        message2 += "</ul>"
        message2 += "</td></tr>"
    

    message += "<tr style='color:red;'>"
    message += "<td style='padding-bottom: 40px;'>"
    message += "<div style='border-width:3px; border-style:solid; border-color:#ff0000; display: inline-block; padding: 10px;'>"
    message += "<b>" + "Média das avaliações: "
    message += "<ul>"
    

    medias = 0
    for txt, obj in obj_avaliados.items():
        if obj["qtd"] > 0.0:
            message += "<li>"
            message += txt
            message += ": "
            media = obj["nota"]/obj["qtd"]
            medias += arredonda_conceitos(media)
            message += converte_conceitos(media)
            message += "</li>"
        else:
            message += "<li>N/A</li>"

    message += "</ul>"
    
    message += "&#10149; Nota Final Calculada = "
    if len(obj_avaliados):
        message += '<span>'
        message += "<b style='font-size: 1.16em;'>"
        message += "%.2f" % (medias/len(obj_avaliados))
        message += "</b><br>"
        message += '</span>'
    else:
        message += '<span>N/A</span>'

    message += "</b></div>"

    message += "</td></tr>"

    message += message2

    message += "</table>"

    return message

# @login_required
# @permission_required("users.altera_professor", login_url='/')
@transaction.atomic
def banca_avaliar(request, slug):
    """Cria uma tela para preencher avaliações de bancas."""
    configuracao = get_object_or_404(Configuracao)
    coordenacao = configuracao.coordenacao

    prazo_preencher_banca = configuracao.prazo_preencher_banca

    try:
        banca = Banca.objects.get(slug=slug)

        adm = PFEUser.objects.filter(pk=request.user.pk, tipo_de_usuario=4).exists()  # se adm

        if adm:  # é administrador
            pass  # usuário sempre autorizado
        elif banca.endDate.date() + datetime.timedelta(days=prazo_preencher_banca) < datetime.date.today():
            mensagem = "Prazo de submissão da Avaliação de Banca vencido.<br>"
            mensagem += "Entre em contato com a coordenação do PFE "
            mensagem += "para enviar sua avaliação.<br>"
            mensagem += coordenacao.user.get_full_name() + " "
            mensagem += "<a href='mailto:" + coordenacao.user.email + "'>"
            mensagem += coordenacao.user.email + "</a>.<br>"
            return HttpResponse(mensagem)

        if not banca.projeto:
            return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

    except Banca.DoesNotExist:
        return HttpResponseNotFound('<h1>Banca não encontrada!</h1>')

    objetivos = get_objetivos_atuais()
    
    # Banca(Intermediária, Final) ou Falconi
    if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1:
        objetivos = objetivos.filter(avaliacao_banca=True)
    elif banca.tipo_de_banca == 2:  # Falconi
        objetivos = objetivos.filter(avaliacao_falconi=True)
    else:
        return HttpResponseNotFound('<h1>Tipo de Banca não indentificado</h1>')

    if request.method == 'POST':
        if 'avaliador' in request.POST:

            avaliador = get_object_or_404(PFEUser,
                                          pk=int(request.POST['avaliador']))

            if banca.tipo_de_banca == 1:  # (1, 'intermediaria'),
                tipo_de_avaliacao = 1  # ( 1, 'Banca Intermediária'),
            elif banca.tipo_de_banca == 0:  # (0, 'final'),
                tipo_de_avaliacao = 2  # ( 2, 'Banca Final'),
            elif banca.tipo_de_banca == 2:  # (2, 'falconi'),
                tipo_de_avaliacao = 99  # (99, 'Falconi'),

            # Identifica que uma avaliação já foi realizada anteriormente
            realizada = Avaliacao2.objects.filter(projeto=banca.projeto,
                                                  avaliador=avaliador,
                                                  tipo_de_avaliacao=tipo_de_avaliacao)\
                .exists()

            objetivos_possiveis = len(objetivos)
            julgamento = [None]*objetivos_possiveis
            
            avaliacoes = dict(filter(lambda elem: elem[0][:9] == "objetivo.", request.POST.items()))

            for i, aval in enumerate(avaliacoes):

                obj_nota = request.POST[aval]
                conceito = obj_nota.split('.')[1]
                julgamento[i] = Avaliacao2.create(projeto=banca.projeto)
                julgamento[i].avaliador = avaliador

                pk_objetivo = int(obj_nota.split('.')[0])
                julgamento[i].objetivo = get_object_or_404(ObjetivosDeAprendizagem,
                                                            pk=pk_objetivo)

                julgamento[i].tipo_de_avaliacao = tipo_de_avaliacao
                if conceito == "NA":
                    julgamento[i].na = True
                else:
                    julgamento[i].nota = converte_conceito(conceito)

                    if tipo_de_avaliacao == 1:  # (1, 'intermediaria')        
                        julgamento[i].peso = julgamento[i].objetivo.peso_banca_intermediaria
                    elif tipo_de_avaliacao == 2:  # ( 2, 'Banca Final'),
                        julgamento[i].peso = julgamento[i].objetivo.peso_banca_final
                    elif tipo_de_avaliacao == 99:  # ( 99, 'Banca Falconi'),
                        julgamento[i].peso = julgamento[i].objetivo.peso_banca_falconi

                    julgamento[i].na = False
                julgamento[i].save()

            julgamento_observacoes = None
            if 'observacoes' in request.POST and request.POST['observacoes'] != "":
                julgamento_observacoes = Observacao.create(projeto=banca.projeto)
                julgamento_observacoes.avaliador = avaliador
                julgamento_observacoes.observacoes = request.POST['observacoes']
                julgamento_observacoes.tipo_de_avaliacao = tipo_de_avaliacao
                julgamento_observacoes.save()


            # Envio de mensagem para Avaliador
            message = mensagem_avaliador(banca, avaliador, julgamento, julgamento_observacoes, objetivos_possiveis, realizada)
            subject = 'Avaliação de Banca PFE : {0}'.format(banca.projeto)
            recipient_list = [avaliador.email, ]
            check = email(subject, recipient_list, message)
            if check != 1:
                message_error = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"


            # Envio de mensagem para Orientador / Coordenação
            message = mensagem_orientador(banca)
            subject = 'Avaliação de Banca PFE : {0}'.format(banca.projeto)
            # Intermediária e Final
            if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1:
                recipient_list = [banca.projeto.orientador.user.email, ]
            elif banca.tipo_de_banca == 2:  # Falconi
                recipient_list = [coordenacao.user.email, ]
            check = email(subject, recipient_list, message)
            if check != 1:
                message_error = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

            resposta = "Avaliação submetida e enviada para:<br>"
            for recipient in recipient_list:
                resposta += "&bull; {0}<br>".format(recipient)
            if realizada:
                resposta += "<br><br><h2>Essa é uma atualização de uma avaliação já enviada anteriormente!</h2><br><br>"
            resposta += "<br><a href='javascript:history.back(1)'>Voltar</a>"
            context = {
                "area_principal": True,
                "mensagem": resposta,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Avaliação não submetida.")
    else:

        orientacoes = ""
        orientacoes_en = ""

        # Intermediária e Final
        if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1:
            pessoas, membros = professores_membros_bancas(banca)
            orientacoes += "Os orientadores são responsáveis por conduzir a banca. Os membros do grupo terão <b>40 minutos para a apresentação</b>. Os membros da banca terão depois <b>50 minutos para arguição</b> (que serão divididos pelos membros convidados), podendo tirar qualquer dúvida a respeito do projeto e fazerem seus comentários. Caso haja muitas interferências da banca durante a apresentação do grupo, poderá se estender o tempo de apresentação. A dinâmica de apresentação é livre, contudo, <b>todos os membros do grupo devem estar prontos para responder qualquer tipo de pergunta</b> sobre o projeto, assim um membro da banca pode fazer uma pergunta direcionada para um estudante específico do grupo se desejar. Caso o grupo demore mais que os 40 minutos a banca poderá definir uma punição em um objetivo de aprendizado, idealmente no objetivo de Comunicação."
            orientacoes += "<br><br>"
            orientacoes += "Como ordem recomendada para a arguição da banca, se deve convidar: professores convidados, professores coorientadores, orientador(a) do projeto e por fim demais pessoas assistindo à apresentação. A banca poderá perguntar tanto sobre a apresentação, como o relatório entregue, permitindo uma clara ponderação nas rubricas dos objetivos de aprendizado."
            orientacoes += "<br><br>"
            orientacoes += "As bancas do Projeto Final de Engenharia servem como mais um evidência de aprendizado, assim, além da percepção dos membros da banca em relação ao nível alcançado nos objetivos de aprendizado pelos membros do grupo, serve também como registro da evolução do projeto. Dessa forma, ao final, a banca terá mais <b>15 minutos para ponderar</b>, nesse momento se pede para dispensar os estudantes e demais convidados externos. Recomendamos 5 minutos para os membros da banca relerem os objetivos de aprendizagem e rubricas, fazerem qualquer anotação e depois 10 minutos para uma discussão final. Cada membro da banca poderá colocar seu veredito sobre grupo, usando as rubricas a seguir. O(a) orientador(a) irá publicar (no Blackboard) posteriormente os conceitos."
            orientacoes += "<br><br>"
            orientacoes += "No Projeto Final de Engenharia, a maioria dos projetos está sob sigilo, através de contratos realizados (quando pedido ou necessário) entre a Organização Parceira e o Insper, se tem os professores automaticamente responsáveis por garantir o sigilo das informações. Assim <b>pessoas externas só podem participar das bancas com prévia autorização</b>, isso inclui outros estudantes que não sejam do grupo, familiares ou amigos."
            orientacoes += "<br>"

            orientacoes_en += "The advisors are responsible for leading the presentation. The group members will have <b>40 minutes for the presentation</b>. The evaluation board members will then have <b>50 minutes for the discussion</b> (which will be divided by the invited members), being able to ask any questions about the project and make their comments. If there is a lot of interference from the examination members during the group's presentation, the presentation time may be extended. <b>all group members should be ready to answer any kind of question</b> about the project, so a board member can ask a question directed at a specific student in the group if desired. If a group takes longer than 40 minutes, the examination board will be able to define a punishment in a learning objective, ideally in the Communication objective."
            orientacoes_en += "<br><br>"
            orientacoes_en += "As recommended order for the board members's argument, the following should be invited: guest professors, co-advisor professors, project supervisor and finally other people watching the presentation. The examination board may ask about the presentation, as well as the report delivered, enabling a clear weighting for the learning objectives rubrics."
            orientacoes_en += "<br><br>"
            orientacoes_en += "Presentations of the Final Engineering Project serve as another evidence of learning, thus, in addition to the perception of the members of the board in relation to the level reached in the learning objectives by the members of the group, it also serves as a record of the evolution of the project. In this way, at the end, the examination board will have more <b>15 minutes to consider</b>, at which point they are asked to dismiss students and other external guests. We recommend 5 minutes for panel members to reread the learning objectives and rubrics, make any notes, and then 10 minutes for a final discussion. Each board member will be able to define a verdict for the group, using the rubrics below. The advisor will later post (on Blackboard) the grades (average)."
            orientacoes_en += "<br><br>"
            orientacoes_en += "In the Final Engineering Project, most projects are kept confidential, through contracts made (when requested or necessary) between the Partner Organization and Insper, the professors are automatically responsible for guaranteeing the confidentiality of the information. <b>external people can only participate in the presentaions with prior authorization</b>, this includes other students who are not part of the group, family or friends."
            orientacoes_en += "<br>"
            
        
        # Falconi
        elif banca.tipo_de_banca == 2:
            pessoas, membros = falconi_membros_banca(banca)
            orientacoes += "Os membros do grupo terão <b>10 minutos para a apresentação</b>. Os consultores da Falconi terão depois outros <b>10 minutos para arguição e observações</b>, podendo tirar qualquer dúvida a respeito do projeto e fazerem seus comentários. Caso haja interferências durante a apresentação do grupo, poderá se estender o tempo de apresentação. A dinâmica de apresentação é livre, contudo, <b>todos os membros do grupo devem estar prontos para responder qualquer tipo de pergunta</b> sobre o projeto. Um consultor da Falconi pode fazer uma pergunta direcionada para um estudante específico do grupo se desejar."
            orientacoes += "<br><br>"
            orientacoes += "As apresentações para a comissão de consultores da Falconi serão usadas para avaliar os melhores projetos. Cada consultor da Falconi poderá colocar seu veredito sobre grupo, usando as rubricas a seguir. Ao final a coordenação do PFE irá fazer a média das avaliações e os projetos que atingirem os níveis de excelência pré-estabelecidos irão receber o certificado de destaque."
            orientacoes += "<br><br>"
            orientacoes += "No Projeto Final de Engenharia, a maioria dos projetos está sob sigilo, através de contratos realizados (quando pedido ou necessário) entre a Organização Parceira e o Insper. A Falconi assinou um documento de responsabilidade em manter o sigilo das informações divulgadas nas apresentações. Assim <b>pessoas externas só podem participar das bancas com prévia autorização</b>, isso inclui outros estudantes que não sejam do grupo, familiares ou amigos."
            orientacoes += "<br>"

            orientacoes_en += "Group members will have <b>15 minutes for the presentation</b>. Falconi consultants will then have another <b>15 minutes for discussion and observations</b>, being able to clarify any doubts about the project and make their comments. If there is interference during the group presentation, the presentation time may be extended. The presentation dynamics is free, however, <b>all group members must be ready to answer any type of question< /b> about the project. A Falconi consultant can ask a question directed at a specific student in the group if desired."
            orientacoes_en += "<br><br>"
            orientacoes_en += "The presentations to Falconi's commission of consultants will be used to evaluate the best projects. Each Falconi consultant will be able to put his verdict on the group, using the following rubrics. At the end, the PFE coordination will average the evaluations and the projects that reach the pre-established levels of excellence will receive the outstanding certificate."
            orientacoes_en += "<br><br>"
            orientacoes_en += "In the Final Engineering Project, most projects are kept confidential, through contracts made (when requested or necessary) between the Partner Organization and Insper. Falconi signed a document of responsibility to maintain the confidentiality of the information disclosed in the presentations. So <b>external people can only participate in the stands with prior authorization</b>, this includes other students who are not part of the group, family or friends."
            orientacoes_en += "<br>"

        # Carregando dados REST
        avaliador = request.GET.get('avaliador', '0')
        try:
            avaliador = int(avaliador)
        except ValueError:
            return HttpResponseNotFound('<h1>Usuário não encontrado!</h1>')
        
        conceitos = [None]*5
        for i in range(5):
            try:
                tmp1 = int(request.GET.get('objetivo'+str(i), '0'))
            except ValueError:
                return HttpResponseNotFound('<h1>Erro em objetivo!</h1>')
            tmp2 = request.GET.get('conceito'+str(i), '')
            conceitos[i] = (tmp1, tmp2)

        observacoes = unquote(request.GET.get('observacoes', ''))
        
        context = {
            'pessoas': pessoas,
            'membros': membros,
            'objetivos': objetivos,
            'banca': banca,
            "orientacoes": orientacoes,
            "orientacoes_en": orientacoes_en,
            "avaliador": avaliador,
            "conceitos": conceitos,
            "observacoes": observacoes,
        }
        return render(request, 'professores/banca_avaliar.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def informe_bancas(request, tipo):
    """Avisa todos os orientadores dos resultados das Bancas Intermediárias."""

    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    #(0, 'Final'),
    #(1, 'Intermediária'),
    
    bancas = Banca.objects.filter(projeto__ano=ano)\
            .filter(projeto__semestre=semestre)\
            .filter(tipo_de_banca=tipo)


    if request.method == 'POST':

        for banca in bancas:

            # Envio de mensagem para Orientador / Coordenação
            message = mensagem_orientador(banca)
            subject = 'Resultado da Avaliação de Banca PFE : {0}'.format(banca.projeto)

            recipient_list = [banca.projeto.orientador.user.email, ]
            
            check = email(subject, recipient_list, message)
            if check != 1:
                message_error = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"
                context = {"mensagem": message_error,}
                return render(request, 'generic.html', context=context)

        resposta = "Informe enviado para:<br>"

        for banca in bancas:
            resposta += "&bull; {0} - banca do dia: {1}<br>".format(banca.projeto.orientador, banca.startDate)

        resposta += "<br><a href='javascript:history.back(1)'>Voltar</a>"

        context = {
            "area_principal": True,
            "mensagem": resposta,
        }

        return render(request, 'generic.html', context=context)

    context = {
        "bancas": bancas,
        "tipo": "Finais" if tipo==0 else "Intermediárias",
    }
    return render(request, 'professores/informes_bancas.html', context=context)



@login_required
@permission_required("users.altera_professor", login_url='/')
def conceitos_obtidos(request, primarykey):  # acertar isso para pk
    """Visualiza os conceitos obtidos pelos alunos no projeto."""
    projeto = get_object_or_404(Projeto, pk=primarykey)

    objetivos = ObjetivosDeAprendizagem.objects.all()

    avaliadores_inter = {}
    avaliadores_final = {}
    avaliadores_falconi = {}

    for objetivo in objetivos:

        # Bancas Intermediárias
        bancas_inter = Avaliacao2.objects.filter(projeto=projeto,
                                                 objetivo=objetivo,
                                                 tipo_de_avaliacao=1)\
            .order_by('avaliador', '-momento')

        for banca in bancas_inter:
            if banca.avaliador not in avaliadores_inter:
                avaliadores_inter[banca.avaliador] = {}
            if objetivo not in avaliadores_inter[banca.avaliador]:
                avaliadores_inter[banca.avaliador][objetivo] = banca
                avaliadores_inter[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga

        # Bancas Finais
        bancas_final = Avaliacao2.objects.filter(projeto=projeto,
                                                 objetivo=objetivo,
                                                 tipo_de_avaliacao=2)\
            .order_by('avaliador', '-momento')

        for banca in bancas_final:
            if banca.avaliador not in avaliadores_final:
                avaliadores_final[banca.avaliador] = {}
            if objetivo not in avaliadores_final[banca.avaliador]:
                avaliadores_final[banca.avaliador][objetivo] = banca
                avaliadores_final[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga

        # Bancas Falconi
        bancas_falconi = Avaliacao2.objects.filter(projeto=projeto,
                                                   objetivo=objetivo,
                                                   tipo_de_avaliacao=99)\
            .order_by('avaliador', '-momento')

        for banca in bancas_falconi:
            if banca.avaliador not in avaliadores_falconi:
                avaliadores_falconi[banca.avaliador] = {}
            if objetivo not in avaliadores_falconi[banca.avaliador]:
                avaliadores_falconi[banca.avaliador][objetivo] = banca
                avaliadores_falconi[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga

    # Bancas Intermediárias
    observacoes = Observacao.objects.filter(projeto=projeto, tipo_de_avaliacao=1).\
        order_by('avaliador', '-momento')
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_inter:
            avaliadores_inter[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes" not in avaliadores_inter[observacao.avaliador]:
            avaliadores_inter[observacao.avaliador]["observacoes"] = observacao.observacoes
        # Senão é só uma avaliação de objetivo mais antiga

    # Bancas Finais
    observacoes = Observacao.objects.filter(projeto=projeto, tipo_de_avaliacao=2).\
        order_by('avaliador', '-momento')
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_final:
            avaliadores_final[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes" not in avaliadores_final[observacao.avaliador]:
            avaliadores_final[observacao.avaliador]["observacoes"] = observacao.observacoes
        # Senão é só uma avaliação de objetivo mais antiga

    # Bancas Falconi
    observacoes = Observacao.objects.filter(projeto=projeto, tipo_de_avaliacao=99).\
        order_by('avaliador', '-momento')
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_falconi:
            avaliadores_falconi[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes" not in avaliadores_falconi[observacao.avaliador]:
            avaliadores_falconi[observacao.avaliador]["observacoes"] = observacao.observacoes
        # Senão é só uma avaliação de objetivo mais antiga

    context = {
        'objetivos': objetivos,
        'projeto': projeto,
        'avaliadores_inter': avaliadores_inter,
        'avaliadores_final': avaliadores_final,
        "avaliadores_falconi": avaliadores_falconi,
    }

    return render(request, 'professores/conceitos_obtidos.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def dinamicas_index(request):
    """Menus de encontros."""
    encontros = Encontro.objects.all().order_by('startDate')

    context = {
        'encontros': encontros,
    }

    return render(request, 'professores/dinamicas_index.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
def dinamicas_criar(request):
    """Cria um encontro."""
    configuracao = get_object_or_404(Configuracao)

    if request.method == 'POST':

        if ('inicio' in request.POST) and ('fim' in request.POST):

            try:
                startDate = dateutil.parser.parse(request.POST['inicio'])
                endDate = dateutil.parser.parse(request.POST['fim'])
            except (ValueError, OverflowError):
                return HttpResponse("Erro com data da Dinâmica!")

            encontro = Encontro.create(startDate, endDate)

            local = request.POST.get('local', None)
            if local:
                encontro.location = local

            projeto = request.POST.get('projeto', None)
            if projeto:
                projeto = int(projeto)
                if projeto != 0:
                    try:
                        encontro.projeto = Projeto.objects.get(id=projeto)
                    except Projeto.DoesNotExist:
                        return HttpResponse("Projeto não encontrado.", status=401)
                else:
                    encontro.projeto = None

            facilitador = request.POST.get('facilitador', None)
            if facilitador:
                facilitador = int(facilitador)
                if facilitador != 0:
                    encontro.facilitador = get_object_or_404(PFEUser, id=facilitador)
                else:
                    encontro.facilitador = None

            encontro.save()

            mensagem = "Dinâmica criada."
            context = {
                "area_principal": True,
                "agendar_dinamica": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Dinâmica não registrada, erro!")

    ano = configuracao.ano
    semestre = configuracao.semestre
    projetos = Projeto.objects.filter(ano=ano, semestre=semestre)\
        .exclude(orientador=None)

    # Buscando pessoas para lista de Facilitadores
    professores_tmp = PFEUser.objects.filter(tipo_de_usuario=2)  # (2, 'professor')
    administradores = PFEUser.objects.filter(tipo_de_usuario=4)  # (4, 'administrador')
    professores = (professores_tmp | administradores).order_by(Lower("first_name"), Lower("last_name"))

    parceiros = PFEUser.objects.filter(tipo_de_usuario=3)
    organizacao = get_object_or_404(Organizacao, sigla="Falconi")
    falconis = parceiros.filter(parceiro__organizacao=organizacao).order_by(Lower("first_name"), Lower("last_name"))

    outros_parceiros = parceiros.exclude(parceiro__organizacao=organizacao)
    estudantes = PFEUser.objects.filter(tipo_de_usuario=1)  # (1, 'estudantes')
    pessoas = (outros_parceiros | estudantes).order_by(Lower("first_name"), Lower("last_name"))

    context = {
        "projetos": projetos,
        "professores": professores,
        "falconis": falconis,
        "pessoas": pessoas,
    }
    return render(request, 'professores/dinamicas_editar.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
def dinamicas_editar(request, primarykey):
    """Edita um encontro."""
    encontro = get_object_or_404(Encontro, pk=primarykey)
    configuracao = get_object_or_404(Configuracao)

    if request.method == 'POST':

        if ('inicio' in request.POST) and ('fim' in request.POST):

            try:
                encontro.startDate = dateutil.parser.parse(request.POST['inicio'])
                encontro.endDate = dateutil.parser.parse(request.POST['fim'])
            except (ValueError, OverflowError):
                return HttpResponse("Erro com data da Dinâmica!")

            local = request.POST.get('local', None)
            if local:
                encontro.location = local

            projeto = request.POST.get('projeto', None)
            if projeto:
                projeto = int(projeto)
                if projeto != 0:
                    encontro.projeto = get_object_or_404(Projeto, id=projeto)
                else:
                    encontro.projeto = None

            facilitador = request.POST.get('facilitador', None)
            if facilitador:
                facilitador = int(facilitador)
                if facilitador != 0:
                    encontro.facilitador = get_object_or_404(PFEUser, id=facilitador)
                else:
                    encontro.facilitador = None

            encontro.save()

            mensagem = "Dinâmica atualizada."
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Dinâmica não registrada, erro!")

    ano = configuracao.ano
    semestre = configuracao.semestre
    projetos = Projeto.objects.filter(ano=ano, semestre=semestre)\
        .exclude(orientador=None)

    # Buscando pessoas para lista de Facilitadores
    professores_tmp = PFEUser.objects.filter(tipo_de_usuario=2)  # 'professor'
    administradores = PFEUser.objects.filter(tipo_de_usuario=4)  # 'administr'
    professores = (professores_tmp | administradores).order_by(Lower("first_name"),
                                                               Lower("last_name"))

    parceiros = PFEUser.objects.filter(tipo_de_usuario=3)
    organizacao = get_object_or_404(Organizacao, sigla="Falconi")
    falconis = parceiros.filter(parceiro__organizacao=organizacao).order_by(Lower("first_name"),
                                                                            Lower("last_name"))

    outros_parceiros = parceiros.exclude(parceiro__organizacao=organizacao)
    estudantes = PFEUser.objects.filter(tipo_de_usuario=1)  # (1, 'estudantes')
    pessoas = (outros_parceiros | estudantes).order_by(Lower("first_name"),
                                                       Lower("last_name"))

    context = {
        'projetos': projetos,
        "professores": professores,
        "falconis": falconis,
        'pessoas': pessoas,
        'encontro': encontro,
    }
    return render(request, 'professores/dinamicas_editar.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def dinamicas_lista(request):
    """Mostra os horários de dinâmicas."""

    if request.is_ajax():
        if 'edicao' in request.POST:

            encontros = Encontro.objects.all().order_by('startDate')

            edicao = request.POST['edicao']
            if edicao == 'todas':
                pass  # segue com encontros
            elif edicao == 'proximas':
                hoje = datetime.date.today()
                encontros = encontros.filter(startDate__gt=hoje)
            else:
                periodo = request.POST['edicao'].split('.')
                ano = int(periodo[0])
                semestre = int(periodo[1])
                encontros = encontros.filter(startDate__year=ano)
                if semestre == 1:
                    encontros = encontros.filter(startDate__month__lt=8)
                else:
                    encontros = encontros.filter(startDate__month__gt=7)

            # checando se projetos atuais tem banca marcada
            configuracao = get_object_or_404(Configuracao)
            sem_dinamicas = Projeto.objects.filter(ano=configuracao.ano,
                                            semestre=configuracao.semestre)
            for encontro in encontros:
                if encontro.projeto:
                    sem_dinamicas = sem_dinamicas.exclude(id=encontro.projeto.id)

            context = {
                "sem_dinamicas": sem_dinamicas,
                'encontros': encontros,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:

        edicoes, _, _ = get_edicoes(Projeto)
        context = {
                "edicoes": edicoes,
            }

    return render(request, 'professores/dinamicas_lista.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def orientadores_tabela_completa(request):
    """Alocação dos Orientadores por semestre."""
    configuracao = get_object_or_404(Configuracao)
    orientadores = recupera_orientadores_por_semestre(configuracao)

    cabecalhos = ["Nome", "Grupos", ]
    titulo = "Alocação de Orientadores"

    context = {
        'anos': orientadores,
        "cabecalhos": cabecalhos,
        "titulo": titulo,
    }
    return render(request, 'professores/orientadores_tabela_completa.html', context)



@login_required
@permission_required('users.altera_professor', login_url='/')
def orientadores_tabela(request):
    """Alocação dos Orientadores por semestre."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']

            professores_pfe = Professor.objects.all().order_by(Lower("user__first_name"),
                                                               Lower("user__last_name"))

            professores = []

            if edicao == 'todas':
                professores_pfe = professores_pfe.filter(professor_orientador__isnull=False).distinct()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                if semestre == "1/2":
                    professores_pfe = professores_pfe.filter(professor_orientador__ano=ano).distinct()
                else:
                    professores_pfe = professores_pfe.filter(professor_orientador__ano=ano,
                                                             professor_orientador__semestre=semestre).distinct()

            professores = professores_pfe

            grupos = []

            for professor in professores:

                grupos_pfe = Projeto.objects.filter(orientador=professor)

                if edicao != 'todas':
                    if semestre == "1/2":
                        grupos_pfe = grupos_pfe.filter(ano=ano)
                    else:
                        grupos_pfe = grupos_pfe.filter(ano=ano).\
                                                filter(semestre=semestre)


                grupos.append(grupos_pfe)

            orientacoes = zip(professores, grupos)

        cabecalhos = ["Nome", "Grupos", "Projetos", ]

        context = {
            "orientacoes": orientacoes,
            "cabecalhos": cabecalhos,
        }

    else:
        edicoes, _, _ = get_edicoes(Projeto, anual=True)
        titulo = "Alocação de Orientadores"
        context = {
            "edicoes": edicoes,
            "titulo": titulo,
        }

    return render(request, 'professores/orientadores_tabela.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/')
def coorientadores_tabela_completa(request):
    """Alocação dos Coorientadores por semestre."""
    configuracao = get_object_or_404(Configuracao)
    coorientadores = recupera_coorientadores_por_semestre(configuracao)

    cabecalhos = ["Nome", "Grupos", ]
    titulo = "Alocação de Coorientadores"

    context = {
        'anos': coorientadores,
        "cabecalhos": cabecalhos,
        "titulo": titulo,
    }
    return render(request, 'professores/coorientadores_tabela_completa.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def coorientadores_tabela(request):
    """Alocação dos Coorientadores por semestre."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']

            professores_pfe = Professor.objects.all().order_by(Lower("user__first_name"),
                                                               Lower("user__last_name"))

            professores = []

            if edicao == 'todas':
                professores_pfe = professores_pfe.filter(user__coorientador__isnull=False).distinct()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                if semestre == "1/2":
                    professores_pfe = professores_pfe.filter(user__coorientador__projeto__ano=ano).distinct()
                else:
                    professores_pfe = professores_pfe.filter(user__coorientador__projeto__ano=ano,
                                                             user__coorientador__projeto__semestre=semestre).distinct()

            professores = professores_pfe

            grupos = []

            for professor in professores:

                grupos_pfe = Coorientador.objects.filter(usuario=professor.user)

                if edicao != 'todas':
                    if semestre == "1/2":
                        grupos_pfe = grupos_pfe.filter(projeto__ano=ano)
                    else:
                        grupos_pfe = grupos_pfe.filter(projeto__ano=ano).\
                                                filter(projeto__semestre=semestre)

                grupos.append(grupos_pfe)

            orientacoes = zip(professores, grupos)

        cabecalhos = ["Nome", "Grupos", "Projetos", ]
    
        context = {
            "orientacoes": orientacoes,
            "cabecalhos": cabecalhos,
        }

    else:
        edicoes, _, _ = get_edicoes(Projeto, anual=True)
        titulo = "Alocação de Coorientadores"
        context = {
            "edicoes": edicoes,
            "titulo": titulo,
        }

    return render(request, 'professores/coorientadores_tabela.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def relatos_quinzenais(request):
    """Formulários com os projetos e relatos a avaliar do professor orientador."""

    user = get_object_or_404(PFEUser, pk=request.user.pk)

    configuracao = get_object_or_404(Configuracao)

    projetos = Projeto.objects.filter(orientador=user.professor, ano=configuracao.ano, semestre=configuracao.semestre)

    context = {
        "user": user,
        "projetos": projetos,
    }

    return render(request, 'professores/relatos_quinzenais.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def relatos_quinzenais_todos(request):
    """Formulários com os projetos e relatos a avaliar do professor orientador."""

    if request.is_ajax():

        if 'edicao' in request.POST:

            projetos = Projeto.objects.all()

            edicao = request.POST['edicao']
            if edicao != 'todas':
                periodo = request.POST['edicao'].split('.')
                ano = int(periodo[0])
                semestre = int(periodo[1])
                projetos = projetos.filter(ano=ano, semestre=semestre)
                
            context = {
                "administracao": True,
                "projetos": projetos,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:

        edicoes, _, _ = get_edicoes(Projeto)
        context = {
                "administracao": True,
                "edicoes": edicoes,
            }

    return render(request, 'professores/relatos_quinzenais.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
@transaction.atomic
def relato_avaliar(request, projeto_id, evento_id):
    """Cria uma tela para preencher avaliações dos relatos quinzenais."""

    projeto = get_object_or_404(Projeto, pk=projeto_id)
    evento = get_object_or_404(Evento, pk=evento_id)

    evento_anterior = Evento.objects.filter(tipo_de_evento=20, endDate__lt=evento.endDate).order_by('endDate').last()
    
    alocacoes = Alocacao.objects.filter(projeto=projeto)

    relatos = []
    for alocacao in alocacoes:
        relatos.append(Relato.objects.filter(alocacao=alocacao,
                                    momento__gt=evento_anterior.endDate + datetime.timedelta(days=1),
                                    momento__lte=evento.endDate + datetime.timedelta(days=1)).order_by('momento').last() )
                                    # O datetime.timedelta(days=1) é necessário pois temos de checar passadas 24 horas, senão valo começo do dia

    # SE UM DIA DECIDIR AVALIAR OS RELATOS POR OBJETIVOS DE APRENDIZAGEM
    # objetivos = get_objetivos_atuais()
    # objetivos = objetivos.filter(avaliacao_aluno=True)
    # avaliador = projeto.orientador.user
    # tipo_de_avaliacao = 200 + ordenacao  # (200, "Relato Quinzenal 1"),

    user = get_object_or_404(PFEUser, pk=request.user.pk)

    # Só o próprio orientador pode editar uma avaliação
    if user == projeto.orientador.user:
        editor = True
    else:
        editor = False

    if request.method == 'POST':

        if editor:

            # edicao = request.POST['op']
            avaliacoes = dict(filter(lambda elem: elem[0][:3] == "op.", request.POST.items()))

            for i, aval in enumerate(avaliacoes):

                relato_id = int(aval.split('.')[1])
                relato = get_object_or_404(Relato, pk=relato_id)

                obj_nota = request.POST[aval]
                
                relato.avaliacao = float(obj_nota)  # Seria melhor decimal.
                relato.save()

            observacoes = request.POST["observacoes"]

            if observacoes != "":

                user = get_object_or_404(PFEUser, pk=request.user.pk)

                (obs, _created) = Observacao.objects.get_or_create(projeto=projeto,
                                                                avaliador=user,
                                                                momento=evento.endDate,  # data marcada do fim do evento
                                                                tipo_de_avaliacao=200)  # (200, "Relato Quinzenal"),
                obs.observacoes = observacoes
                obs.save()

                coordenacoes = PFEUser.objects.filter(coordenacao=True)
                email_coordenacoes = []
                for coordenador in coordenacoes:
                    email_coordenacoes.append(str(coordenador.email))

                # Manda mensagem para coordenadores
                email("Anotação Quinzenal", email_coordenacoes, observacoes+"<br><br>"+str(user))

            # objetivos_possiveis = len(objetivos)
            # julgamento = [None]*objetivos_possiveis
            
            # avaliacoes = dict(filter(lambda elem: elem[0][:9] == "objetivo.", request.POST.items()))

            # for i, aval in enumerate(avaliacoes):

            #     pk_objetivo = int(aval.split('.')[1])
            #     objetivo = get_object_or_404(ObjetivosDeAprendizagem, pk=pk_objetivo)

            #     (julgamento[i], _created) = Avaliacao2.objects.get_or_create(alocacao=relato.alocacao,
            #                                                                  tipo_de_avaliacao=tipo_de_avaliacao,
            #                                                                  objetivo=objetivo)

            #     julgamento[i].projeto = relato.alocacao.projeto
            #     julgamento[i].avaliador = avaliador

            #     obj_nota = request.POST[aval]
            #     julgamento[i].nota = obj_nota

            #     julgamento[i].peso = 0.0
                
            #     julgamento[i].save()

            context = {
                "area_principal": True,
                "mensagem": "avaliação realizada",
            }
            return render(request, 'generic.html', context=context)
            
        else:
            return HttpResponseNotFound('<h1>Erro na edição do relato!</h1>')

    else:  # GET
        
        # Identifica que uma avaliação já foi realizada anteriormente
        # avaliacoes = Avaliacao2.objects.filter(alocacao=relato.alocacao,
        #                                         avaliador=avaliador,
        #                                         tipo_de_avaliacao=tipo_de_avaliacao)

        obs = Observacao.objects.filter(projeto=projeto,
                                        momento__gt=evento_anterior.endDate + datetime.timedelta(days=1),
                                        momento__lte=evento.endDate + datetime.timedelta(days=1),
                                        tipo_de_avaliacao=200).last()  # (200, "Relato Quinzenal"),
                                        # O datetime.timedelta(days=1) é necessário pois temos de checar passadas 24 horas, senão valo começo do dia
        if obs:
            observacoes = obs.observacoes
        else:
            observacoes = None

        context = {
            # "objetivos": objetivos,
            "editor": editor,
            "projeto": projeto,
            "observacoes": observacoes,
            "alocacoes_relatos": zip(alocacoes, relatos),
            "evento": evento,
        }
        return render(request, 'professores/relato_avaliar.html', context=context)


# Criei esse função temporária para tratar caso a edição seja passada diretamente na URL
def resultado_projetos_intern(request, ano=None, semestre=None):
    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            if edicao == 'todas':
                projetos = Projeto.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

            relatorio_intermediario = []
            relatorio_final = []
            banca_intermediaria = []
            banca_final = []
            banca_falconi = []

            for projeto in projetos:

                # Aparentemente código repetido por erro
                # aval_banc_final = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=2)  # (2, 'Banca Final'),
                # nota_banca_final, peso = Aluno.get_banca(None, aval_banc_final, eh_banca=True)

                alocacoes = Alocacao.objects.filter(projeto=projeto)
                
                if alocacoes:

                    primeira = alocacoes.first()
                    medias = primeira.get_media

                    if ("peso_grupo_inter" in medias) and (medias["peso_grupo_inter"] is not None) and (medias["peso_grupo_inter"] > 0):
                        nota = medias["nota_grupo_inter"]/medias["peso_grupo_inter"]
                        relatorio_intermediario.append(("{0}".format(converte_letra(nota, espaco="&nbsp;")),
                                            "{0:5.2f}".format(nota),
                                            nota))
                    else:
                        relatorio_intermediario.append(("&nbsp;-&nbsp;", None, 0))

                    if ("peso_grupo_final" in medias) and (medias["peso_grupo_final"] is not None) and (medias["peso_grupo_final"] > 0):
                        nota = medias["nota_grupo_final"]/medias["peso_grupo_final"]
                        relatorio_final.append(("{0}".format(converte_letra(nota, espaco="&nbsp;")),
                                            "{0:5.2f}".format(nota),
                                            nota))
                    else:
                        relatorio_final.append(("&nbsp;-&nbsp;", None, 0))

                else:
                    relatorio_intermediario.append(("&nbsp;-&nbsp;", None, 0))
                    relatorio_final.append(("&nbsp;-&nbsp;", None, 0))


                aval_banc_final = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=2)  # B. Final
                nota_banca_final, peso, avaliadores = Aluno.get_banca(None, aval_banc_final, eh_banca=True)

                if peso is not None:
                    banca_final.append(("{0}".format(converte_letra(nota_banca_final, espaco="&nbsp;")),
                                        "{0:5.2f}".format(nota_banca_final),
                                        nota_banca_final))
                else:
                    banca_final.append(("&nbsp;-&nbsp;", None, 0))

                aval_banc_interm = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=1)  # B. Int.
                nota_banca_intermediaria, peso, avaliadores = Aluno.get_banca(None, aval_banc_interm, eh_banca=True)
                if peso is not None:
                    banca_intermediaria.append(("{0}".format(converte_letra(nota_banca_intermediaria,
                                                                            espaco="&nbsp;")),
                                                "{0:5.2f}".format(nota_banca_intermediaria),
                                                nota_banca_intermediaria))
                else:
                    banca_intermediaria.append(("&nbsp;-&nbsp;", None, 0))

                aval_banc_falconi = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=99)  # Falc.
                nota_banca_falconi, peso, avaliadores = Aluno.get_banca(None, aval_banc_falconi)
                if peso is not None:
                    nomes = ""
                    for nome in avaliadores:
                        nomes += "&#8226; "+str(nome)+"<br>"
                    banca_falconi.append(("{0}".format(nomes),
                                          "{0:5.2f}".format(nota_banca_falconi),
                                          nota_banca_falconi))
                else:
                    banca_falconi.append(("&nbsp;-&nbsp;", None, 0))

            tabela = zip(projetos,
                         relatorio_intermediario,
                         relatorio_final,
                         banca_intermediaria,
                         banca_final,
                         banca_falconi)

            context = {'tabela': tabela}

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:
        edicoes, _, _ = get_edicoes(Projeto)

        if ano and semestre:
            selecionada = str(ano) + "." + str(semestre)
        else:
            selecionada = None

        context = {
            "edicoes": edicoes,
            "selecionada": selecionada,
        }

    return render(request, 'professores/resultado_projetos.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/')
def resultado_projetos_edicao(request, edicao):
    """Mostra os resultados das avaliações (Bancas) para uma edição."""
    edicao = edicao.split('.')
    try:
        ano = int(edicao[0])
        semestre = int(edicao[1])
    except ValueError:
        return HttpResponseNotFound('<h1>Erro em!</h1>')
    return resultado_projetos_intern(request, ano, semestre)

@login_required
@permission_required('users.altera_professor', login_url='/')
def resultado_projetos(request):
    """Mostra os resultados das avaliações (Bancas)."""
    return resultado_projetos_intern(request)


@login_required
@permission_required("users.altera_professor", login_url='/')
def todos_professores(request):
    """Exibe todas os professores que estão cadastrados no PFE."""
    professores = Professor.objects.all()

    cabecalhos = ["Nome", "e-mail", "Bancas", "Orientações", "Lattes", ]
    titulo = "Professores"

    context = {
        'professores': professores,
        "cabecalhos": cabecalhos,
        "titulo": titulo,
        }

    return render(request, 'professores/todos_professores.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def objetivo_editar(request, primarykey):
    """Edita um objetivo de aprendizado."""
    objetivo = get_object_or_404(ObjetivosDeAprendizagem, pk=primarykey)

    if request.method == 'POST':
        if editar_banca(objetivo, request):
            mensagem = "Banca editada."
        else:
            mensagem = "Erro ao Editar banca."
        context = {
            "area_principal": True,
            "bancas_index": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    context = {
        'objetivo': objetivo,
    }
    return render(request, 'professores/objetivo_editar.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def objetivos_rubricas(request):
    """Exibe os objetivos e rubricas."""
    objetivos = get_objetivos_atuais()

    context = {
        'objetivos': objetivos, 
    }

    return render(request, 'professores/objetivos_rubricas.html', context)


@login_required
@transaction.atomic
def ver_pares(request, alocacao_id, momento):
    """Permite visualizar a avaliação de pares."""

    configuracao = get_object_or_404(Configuracao)

    user = get_object_or_404(Alocacao, pk=alocacao_id)
    estudante = Aluno.objects.get(pk=user.aluno.pk)

    # Avaliações de Pares
    # 31, 'Avaliação de Pares Intermediária'
    # 32, 'Avaliação de Pares Final'
    if momento=="intermediaria":
        tipo=0
    else:
        tipo=1

    projeto = Projeto.objects\
        .filter(alocacao__aluno=estudante, ano=configuracao.ano, semestre=configuracao.semestre).first()
    
    alocacao_de = Alocacao.objects.get(projeto=projeto, aluno=estudante)
    alocacoes = Alocacao.objects.filter(projeto=projeto).exclude(aluno=estudante)
    
    pares = []
    for alocacao in alocacoes:
        par = Pares.objects.filter(alocacao_de=alocacao_de, alocacao_para=alocacao, tipo=tipo).first()
        pares.append(par)

    colegas = zip(alocacoes, pares)

    context = {
        "estudante": estudante,
        "colegas": colegas,
        'momento': momento,
    }

    return render(request, 'professores/ver_pares.html', context)
