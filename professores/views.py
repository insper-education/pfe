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
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseNotFound
from django.db.models.functions import Lower
from django.utils import html

from users.models import PFEUser, Professor, Aluno
from users.support import get_edicoes


from projetos.models import ObjetivosDeAprendizagem, Avaliacao2, Observacao
from projetos.models import Banca, Evento, Encontro
from projetos.models import Projeto, Configuracao
from projetos.support import get_peso
from projetos.support import converte_letra, converte_conceito
from projetos.messages import email

from .support import professores_membros_bancas, falconi_membros_banca
from .support import editar_banca
from .support import recupera_orientadores_por_semestre
from .support import recupera_coorientadores_por_semestre


@login_required
@permission_required("users.altera_professor", login_url='/')
def index_professor(request):
    """Mostra página principal do usuário professor."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

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

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if request.method == 'POST':
        if 'projeto' in request.POST:

            try:
                projeto = Projeto.objects.get(id=int(request.POST['projeto']))
            except Projeto.DoesNotExist:
                return HttpResponse("Projeto não encontrado.", status=401)

            banca = Banca.create(projeto)
            editar_banca(banca, request)
            mensagem = "Banca criada."
            context = {
                "area_principal": True,
                "bancas_index": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Banca não registrada, erro identificando projeto")

    ano = configuracao.ano
    semestre = configuracao.semestre
    projetos = Projeto.objects.filter(ano=ano, semestre=semestre)\
        .exclude(orientador=None)

    professores = professores_membros_bancas()
    falconis = falconi_membros_banca()

    context = {
        'projetos': projetos,
        'professores': professores,
        "TIPO_DE_BANCA": Banca.TIPO_DE_BANCA,
        "falconis": falconis,
    }
    return render(request, 'professores/bancas_editar.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def bancas_editar(request, primarykey):
    """Edita uma banca de avaliação para o projeto."""
    try:
        banca = Banca.objects.get(pk=primarykey)
    except Banca.DoesNotExist:
        return HttpResponse("Banca não encontrada.", status=401)

    if request.method == 'POST':
        editar_banca(banca, request)
        mensagem = "Banca editada."
        context = {
            "area_principal": True,
            "bancas_index": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    projetos = Projeto.objects.exclude(orientador=None)\
        .order_by("-ano", "-semestre")

    professores = professores_membros_bancas()
    falconis = falconi_membros_banca()

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
    projeto = None

    if periodo_projeto == "proximas":
        hoje = datetime.date.today()
        bancas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")
    elif periodo_projeto == "todas":
        bancas = Banca.objects.all().order_by("startDate")
    else:
        try:
            projeto = Projeto.objects.get(id=periodo_projeto)
        except Projeto.DoesNotExist:
            return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')
        bancas = Banca.objects.filter(projeto=projeto).order_by("startDate")

    context = {
        'bancas': bancas,
        'periodo': periodo_projeto,
        "projeto": projeto,
    }

    return render(request, 'professores/bancas_lista.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def bancas_tabela(request):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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

    return render(request, 'professores/bancas_tabela.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def banca_ver(request, primarykey):
    """Retorna banca pedida."""
    try:
        banca = Banca.objects.get(id=primarykey)
    except Banca.DoesNotExist:
        return HttpResponseNotFound('<h1>Banca não encontrada!</h1>')

    context = {
        'banca': banca,
    }

    return render(request, 'professores/banca_ver.html', context)


# @login_required
# @permission_required("users.altera_professor", login_url='/')
def banca_avaliar(request, slug):
    """Cria uma tela para preencher avaliações de bancas."""
    try:
        banca = Banca.objects.get(slug=slug)

        if banca.endDate.date() + datetime.timedelta(days=5) < datetime.date.today():
            mensagem = "Prazo para submissão da Avaliação de Banca vencido.<br>"
            mensagem += "Entre em contato com a coordenação do PFE para enviar sua avaliação.<br>"
            mensagem += "Luciano Pereira Soares <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>.<br>"
            return HttpResponse(mensagem)

        if not banca.projeto:
            return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

    except Banca.DoesNotExist:
        return HttpResponseNotFound('<h1>Banca não encontrada!</h1>')

    # Intermediária e Final
    if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1:
        objetivos = ObjetivosDeAprendizagem.objects\
            .filter(avaliacao_banca=True).order_by("id")
    elif banca.tipo_de_banca == 2:  # Falconi
        objetivos = ObjetivosDeAprendizagem.objects\
            .filter(avaliacao_falconi=True).order_by("id")
    else:
        return HttpResponseNotFound('<h1>Tipo de Banca não indentificado!</h1>')

    if request.method == 'POST':
        if 'avaliador' in request.POST:

            try:
                avaliador = PFEUser.objects.get(pk=int(request.POST['avaliador']))
            except PFEUser.DoesNotExist:
                return HttpResponse("Usuário não encontrado.", status=401)

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

            objetivos_possiveis = 5
            julgamento = [None]*objetivos_possiveis
            for i in range(objetivos_possiveis):
                if 'objetivo.{0}'.format(i+1) in request.POST:
                    obj_nota = request.POST['objetivo.{0}'.format(i+1)]
                    conceito = obj_nota.split('.')[1]
                    julgamento[i] = Avaliacao2.create(projeto=banca.projeto)
                    julgamento[i].avaliador = avaliador

                    try:
                        pk_objetivo = int(obj_nota.split('.')[0])
                        julgamento[i].objetivo = ObjetivosDeAprendizagem.objects.get(pk=pk_objetivo)
                    except ObjetivosDeAprendizagem.DoesNotExist:
                        return HttpResponse("Objetivo de Aprendizagem não encontrados.", status=401)

                    julgamento[i].tipo_de_avaliacao = tipo_de_avaliacao
                    if conceito == "NA":
                        julgamento[i].na = True
                    else:
                        julgamento[i].nota = converte_conceito(conceito)
                        julgamento[i].peso = get_peso(tipo_de_avaliacao, julgamento[i].objetivo)
                        julgamento[i].na = False
                    julgamento[i].save()

            julgamento_observacoes = None
            if 'observacoes' in request.POST and request.POST['observacoes'] != "":
                julgamento_observacoes = Observacao.create(projeto=banca.projeto)
                julgamento_observacoes.avaliador = avaliador
                julgamento_observacoes.observacoes = request.POST['observacoes']
                julgamento_observacoes.tipo_de_avaliacao = tipo_de_avaliacao
                julgamento_observacoes.save()

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
            if julgamento[0] and not julgamento[0].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[0].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[0].nota))
            if julgamento[1] and not julgamento[1].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[1].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[1].nota))
            if julgamento[2] and not julgamento[2].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[2].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[2].nota))
            if julgamento[3] and not julgamento[3].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[3].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[3].nota))
            if julgamento[4] and not julgamento[4].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[4].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[4].nota))
            message += "</table>"

            message += "<br>\n<br>\n"

            if julgamento_observacoes:
                message += "<b>Observações:</b>\n"
                message += "<p style='border:1px; border-style:solid; padding: 0.3em; margin: 0;'>"
                message += html.escape(julgamento_observacoes.observacoes).replace('\n', '<br>\n')
                message += "</p>"
                message += "<br>\n<br>\n"

            # Criar link para reeditar
            message += "<a href='" + settings.SERVER + "/professores/banca_avaliar/" + str(banca.slug)

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
                    message += "{0}".format(julg.objetivo.rubrica_I)
                    message += "</td>"

                    if (not julg.na) and converte_letra(julg.nota) == "D":
                        message += "<td style='border: 2px solid black;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black;'>"
                    message += "{0}".format(julg.objetivo.rubrica_D)
                    message += "</td>"

                    if (not julg.na) and (converte_letra(julg.nota) == "C" or converte_letra(julg.nota) == "C+"):
                        message += "<td style='border: 2px solid black;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black;'>"
                    message += "{0}".format(julg.objetivo.rubrica_C)
                    message += "</td>"

                    if (not julg.na) and (converte_letra(julg.nota) == "B" or converte_letra(julg.nota) == "B+"):
                        message += "<td style='border: 2px solid black;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black;'>"
                    message += "{0}".format(julg.objetivo.rubrica_B)
                    message += "</td>"

                    if (not julg.na) and (converte_letra(julg.nota) == "A" or converte_letra(julg.nota) == "A+"):
                        message += "<td style='border: 2px solid black;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black;'>"
                    message += "{0}".format(julg.objetivo.rubrica_A)
                    message += "</td>"

                    message += "</tr>"
                    message += "</table>"

            subject = 'Banca PFE : {0}'.format(banca.projeto)

            recipient_list = [avaliador.email, ]

            # Intermediária e Final
            if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1:
                recipient_list += [banca.projeto.orientador.user.email, ]
            elif banca.tipo_de_banca == 2:  # Falconi
                recipient_list += ["lpsoares@insper.edu.br", ]

            check = email(subject, recipient_list, message)
            if check != 1:
                message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

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

        # Intermediária e Final
        if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1:
            pessoas = professores_membros_bancas()
            orientacoes += "O professor(a) orientador(a) é responsável por conduzir a banca. Os membros do grupo terão <b>40 minutos para a apresentação</b>. Os membros da banca terão depois <b>50 minutos para arguição</b> (que serão divididos pelos membros convidados), podendo tirar qualquer dúvida a respeito do projeto e fazerem seus comentários. Caso haja muitas interferências da banca durante a apresentação do grupo, poderá se estender o tempo de apresentação. A dinâmica de apresentação é livre, contudo, <b>todos os membros do grupo devem estar prontos para responder qualquer tipo de pergunta</b> sobre o projeto. Um membro da banca pode fazer uma pergunta direcionada para um estudante específico do grupo se desejar."
            orientacoes += "<br><br>"
            orientacoes += "Como ordem recomendada para a arguição da banca, se deve convidar: professores convidados, professores coorientadores, professor(a) orientador(a) do projeto e por fim demais pessoas assistindo à apresentação. A banca poderá perguntar tanto sobre a apresentação, como o relatório entregue, se espera coletar informações tanto da apresentação, como do relatório, permitindo uma clara ponderação nas rubricas dos objetivos de aprendizado do Projeto Final de Engenharia."
            orientacoes += "<br><br>"
            orientacoes += "As bancas do Projeto Final de Engenharia servem como mais um evidência de aprendizado, assim, além da percepção dos membros da banca em relação ao nível alcançado nos objetivos de aprendizado pelos membros do grupo, serve também como registro da evolução do projeto. Dessa forma, ao final, a banca terá mais <b>15 minutos para ponderar</b>, nesse momento se recomenda dispensar os estudantes e demais convidados externos. Recomendamos 5 minutos para os membros da banca relerem os objetivos de aprendizagem e rubricas, fazerem qualquer anotação e depois 10 minutos para uma discussão final. Cada membro da banca poderá colocar seu veredito sobre grupo, usando as rubricas a seguir. O professor(a) orientador(a) irá publicar (no Blackboard), ao final, a média dos conceitos anotados."
            orientacoes += "<br><br>"
            orientacoes += "No Projeto Final de Engenharia, a maioria dos projetos está sob sigilo, através de contratos realizados (quando pedido ou necessário) entre a Organização Parceira e o Insper, se tem os professores automaticamente responsáveis por garantir o sigilo das informações. Assim <b>pessoas externas só podem participar das bancas com prévia autorização</b>, isso inclui outros estudantes que não sejam do grupo, familiares ou amigos."
            orientacoes += "<br>"

        # Falconi
        elif banca.tipo_de_banca == 2:
            pessoas = falconi_membros_banca()
            orientacoes += "Os membros do grupo terão <b>15 minutos para a apresentação</b>. Os consultores da Falconi terão depois outros <b>15 minutos para arguição e observações</b>, podendo tirar qualquer dúvida a respeito do projeto e fazerem seus comentários. Caso haja interferências durante a apresentação do grupo, poderá se estender o tempo de apresentação. A dinâmica de apresentação é livre, contudo, <b>todos os membros do grupo devem estar prontos para responder qualquer tipo de pergunta</b> sobre o projeto. Um consultor da Falconi pode fazer uma pergunta direcionada para um estudante específico do grupo se desejar."
            orientacoes += "<br><br>"
            orientacoes += "As apresentações para a comissão de consultores da Falconi serão usadas para avaliar os melhores projetos. Cada consultor da Falconi poderá colocar seu veredito sobre grupo, usando as rubricas a seguir. Ao final a coordenação do PFE irá fazer a média das avaliações e os projetos que atingirem os níveis de excelência pré-estabelecidos irão receber o certificado de destaque."
            orientacoes += "<br><br>"
            orientacoes += "No Projeto Final de Engenharia, a maioria dos projetos está sob sigilo, através de contratos realizados (quando pedido ou necessário) entre a Organização Parceira e o Insper. A Falconi assinou um documento de responsabilidade em manter o sigilo das informações divulgadas nas apresentações. Assim <b>pessoas externas só podem participar das bancas com prévia autorização</b>, isso inclui outros estudantes que não sejam do grupo, familiares ou amigos."
            orientacoes += "<br>"


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
            'objetivos': objetivos,
            'banca': banca,
            "orientacoes": orientacoes,
            "avaliador": avaliador,
            "conceitos": conceitos,
            "observacoes": observacoes,
        }
        return render(request, 'professores/banca_avaliar.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def conceitos_obtidos(request, primarykey):  # acertar isso para pk
    """Visualiza os conceitos obtidos pelos alunos no projeto."""
    try:
        projeto = Projeto.objects.get(pk=primarykey)
    except Projeto.DoesNotExist:
        return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

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
@permission_required('users.altera_professor', login_url='/')
def dinamicas_criar(request):
    """Cria um encontro."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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
                    try:
                        encontro.facilitador = PFEUser.objects.get(id=facilitador)
                    except PFEUser.DoesNotExist:
                        return HttpResponse("Usuário não encontrado.", status=401)
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

    pessoas = PFEUser.objects.all().order_by(Lower("first_name"), Lower("last_name"))

    context = {
        'projetos': projetos,
        'pessoas': pessoas,
    }
    return render(request, 'professores/dinamicas_editar.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def dinamicas_editar(request, primarykey):
    """Edita um encontro."""
    try:
        encontro = Encontro.objects.get(pk=primarykey)
    except Encontro.DoesNotExist:
        return HttpResponse("Encontro não encontrado.", status=401)

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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
                    try:
                        encontro.facilitador = PFEUser.objects.get(id=facilitador)
                    except PFEUser.DoesNotExist:
                        return HttpResponse("Usuário não encontrado.", status=401)
                else:
                    encontro.facilitador = None

            encontro.save()

            mensagem = "Dinâmica criada."
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

    pessoas = PFEUser.objects.all().order_by(Lower("first_name"), Lower("last_name"))

    context = {
        'projetos': projetos,
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

            context = {
                'encontros': encontros,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:

        edicoes, _, _ = get_edicoes(Projeto)
        context = {
                'edicoes': edicoes,
            }

    return render(request, 'professores/dinamicas_lista.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def orientadores_tabela(request):
    """Alocação dos Orientadores por semestre."""
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuração do sistema.", status=401)

    orientadores = recupera_orientadores_por_semestre(configuracao)

    context = {
        'anos': orientadores,
    }
    return render(request, 'professores/orientadores_tabela.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def coorientadores_tabela(request):
    """Alocação dos Coorientadores por semestre."""
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    coorientadores = recupera_coorientadores_por_semestre(configuracao)

    context = {
        'anos': coorientadores,
    }

    return render(request, 'professores/coorientadores_tabela.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def resultado_bancas(request):
    """Mostra os resultados das avaliações (Bancas)."""
    edicoes, ano, semestre = get_edicoes(Projeto)

    context = {
        "edicoes": edicoes,
    }

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            if edicao == 'todas':
                projetos = Projeto.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

            banca_intermediaria = []
            banca_final = []
            banca_falconi = []

            for projeto in projetos:
                aval_banc_final = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=2)  # B. Final
                nota_banca_final, peso = Aluno.get_banca(None, aval_banc_final)
                if peso is not None:
                    banca_final.append(("{0}".format(converte_letra(nota_banca_final, espaco="&nbsp;")),
                                        "{0:5.2f}".format(nota_banca_final),
                                        nota_banca_final))
                else:
                    banca_final.append(("&nbsp;-&nbsp;", None, 0))

                aval_banc_interm = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=1)  # B. Int.
                nota_banca_intermediaria, peso = Aluno.get_banca(None, aval_banc_interm)
                if peso is not None:
                    banca_intermediaria.append(("{0}".format(converte_letra(nota_banca_intermediaria,
                                                                            espaco="&nbsp;")),
                                                "{0:5.2f}".format(nota_banca_intermediaria),
                                                nota_banca_intermediaria))
                else:
                    banca_intermediaria.append(("&nbsp;-&nbsp;", None, 0))

                aval_banc_falconi = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=99)  # Falc.
                nota_banca_falconi, peso = Aluno.get_banca(None, aval_banc_falconi)
                if peso is not None:
                    banca_falconi.append(("{0}".format(converte_letra(nota_banca_falconi, espaco="&nbsp;")),
                                        "{0:5.2f}".format(nota_banca_falconi),
                                        nota_banca_falconi))
                else:
                    banca_falconi.append(("&nbsp;-&nbsp;", None, 0))

            tabela = zip(projetos, banca_intermediaria, banca_final, banca_falconi)

            context['tabela'] = tabela

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    return render(request, 'professores/resultado_bancas.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def todos_professores(request):
    """Exibe todas os professores que estão cadastrados no PFE."""
    professores = Professor.objects.all()

    context = {
        'professores': professores,
        }

    return render(request, 'professores/todos_professores.html', context)
