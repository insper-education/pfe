#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import re           #regular expression (para o import)

from django.conf import settings

from django.utils import html

#from projetos.models import Proposta, Organizacao, Configuracao, Anotacao
from projetos.models import Proposta, Configuracao

from projetos.models import Area, AreaDeInteresse

from projetos.messages import email

#from users.models import PFEUser, Aluno, Professor, Parceiro, Administrador, Opcao, Alocacao
from users.models import Opcao

from users.support import adianta_semestre

#from .messages import email, create_message, message_agendamento

def cria_area_proposta(request, proposta):
    """Cria um objeto Areas e preenche ele."""

    check_values = request.POST.getlist('selection')

    todas_areas = Area.objects.filter(ativa=True)
    for area in todas_areas:
        if area.titulo in check_values:
            if not AreaDeInteresse.objects.filter(area=area, proposta=proposta).exists():
                AreaDeInteresse.create_proposta_area(proposta, area).save()
        else:
            if AreaDeInteresse.objects.filter(area=area, proposta=proposta).exists():
                AreaDeInteresse.objects.get(area=area, proposta=proposta).delete()

    outras = request.POST.get("outras", "")
    if outras != "":
        (outra, _created) = AreaDeInteresse.objects.get_or_create(area=None, proposta=proposta)
        outra.outras = request.POST.get("outras", "")
        outra.save()
    else:
        if AreaDeInteresse.objects.filter(area=None, proposta=proposta).exists():
            AreaDeInteresse.objects.get(area=None, proposta=proposta).delete()

def lista_areas(proposta):
    """Lista áreas de um objeto Areas."""

    mensagem = ""

    areas = AreaDeInteresse.objects.filter(proposta=proposta).exclude(area=None)
    for area in areas:
        mensagem += "&bull; "+area.area.titulo+"<br>\n"

    if AreaDeInteresse.objects.filter(area=None, proposta=proposta).exists():
        outras = AreaDeInteresse.objects.get(area=None, proposta=proposta).outras
        mensagem += "Outras: " + outras + "<br>\n"

    return mensagem


def ordena_propostas(disponivel=True, ano=0, semestre=0):
    """Gera lista com propostas ordenados pelos com maior interesse pelos alunos."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return None

    if ano == 0:
        ano = configuracao.ano
    if semestre == 0:
        semestre = configuracao.semestre

    opcoes_list = []
    if disponivel: # somente as propostas disponibilizadas
        propostas = Proposta.objects.filter(ano=ano).\
                               filter(semestre=semestre).\
                               filter(disponivel=True)
    else: # todas as propostas
        propostas = Proposta.objects.filter(ano=ano).\
                               filter(semestre=semestre)
    for proposta in propostas:
        opcoes = Opcao.objects.filter(proposta=proposta)
        opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
        opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=ano).\
                                       filter(aluno__semestrePFE=semestre)
        count = 0
        for opcao in opcoes_validas:
            if opcao.prioridade <= 5:
                count += 1
        opcoes_list.append(count)
    mylist = zip(propostas, opcoes_list)
    mylist = sorted(mylist, key=lambda x: x[1], reverse=True)
    return mylist


def ordena_propostas_novo(disponivel=True, ano=2018, semestre=2, curso='T'):
    """Gera lista com propostas ordenados pelos com maior interesse pelos alunos."""

    prioridades = [[], [], [], [], []]
    estudantes = [[], [], [], [], []]

    if ano < 2018:
        propostas = Proposta.objects.all()
    else:
        propostas = Proposta.objects.filter(ano=ano).\
                                     filter(semestre=semestre)

    if disponivel: # somente as propostas disponibilizadas
        propostas = propostas.filter(disponivel=True)

    for proposta in propostas:

        opcoes = Opcao.objects.filter(proposta=proposta)

        # Parte seguinte parece desnecessária
        opcoes = opcoes.filter(aluno__user__tipo_de_usuario=1)

        # Só opções para a proposta dos estudantes nesse ano e semester
        opcoes = opcoes.filter(aluno__anoPFE=proposta.ano).\
                        filter(aluno__semestrePFE=proposta.semestre)

        if curso != 'T':
            opcoes = opcoes.filter(aluno__curso=curso)

        count = [0, 0, 0, 0, 0]
        estudantes_tmp = ["", "", "", "", ""]
        for opcao in opcoes:
            if opcao.prioridade == 1:
                count[0] += 1
                if estudantes_tmp[0] != "":
                    estudantes_tmp[0] += ", "
                estudantes_tmp[0] += opcao.aluno.user.get_full_name()
            elif opcao.prioridade == 2:
                count[1] += 1
                if estudantes_tmp[1] != "":
                    estudantes_tmp[1] += ", "
                estudantes_tmp[1] += opcao.aluno.user.get_full_name()
            elif opcao.prioridade == 3:
                count[2] += 1
                if estudantes_tmp[2] != "":
                    estudantes_tmp[2] += ", "
                estudantes_tmp[2] += opcao.aluno.user.get_full_name()
            elif opcao.prioridade == 4:
                count[3] += 1
                if estudantes_tmp[3] != "":
                    estudantes_tmp[3] += ", "
                estudantes_tmp[3] += opcao.aluno.user.get_full_name()
            elif opcao.prioridade == 5:
                count[4] += 1
                if estudantes_tmp[4] != "":
                    estudantes_tmp[4] += ", "
                estudantes_tmp[4] += opcao.aluno.user.get_full_name()

        prioridades[0].append(count[0])
        prioridades[1].append(count[1])
        prioridades[2].append(count[2])
        prioridades[3].append(count[3])
        prioridades[4].append(count[4])

        estudantes[0].append(estudantes_tmp[0])
        estudantes[1].append(estudantes_tmp[1])
        estudantes[2].append(estudantes_tmp[2])
        estudantes[3].append(estudantes_tmp[3])
        estudantes[4].append(estudantes_tmp[4])

    mylist = zip(propostas,
                 prioridades[0],
                 prioridades[1],
                 prioridades[2],
                 prioridades[3],
                 prioridades[4],
                 estudantes[0],
                 estudantes[1],
                 estudantes[2],
                 estudantes[3],
                 estudantes[4])

    mylist = sorted(mylist, key=lambda x: (x[1], x[2], x[3], x[4], x[5]), reverse=True)

    return mylist


def preenche_proposta(request, proposta):
    """Preenche um proposta a partir de um request."""

    if proposta is None: # proposta nova
        proposta = Proposta.create()

        try:
            configuracao = Configuracao.objects.get()
            ano = configuracao.ano              # Ano atual
            semestre = configuracao.semestre    # Semestre atual
        except Configuracao.DoesNotExist:
            return None

        # Vai para próximo semestre
        ano, semestre = adianta_semestre(ano, semestre)

        proposta.ano = ano
        proposta.semestre = semestre

    proposta.nome = request.POST.get("nome", "")
    proposta.email = request.POST.get("email", "")
    proposta.website = request.POST.get("website", "")
    proposta.nome_organizacao = request.POST.get("organizacao", "")
    proposta.endereco = request.POST.get("endereco", "")
    proposta.contatos_tecnicos = request.POST.get("contatos_tecnicos", "")
    proposta.contatos_administrativos = request.POST.get("contatos_adm", "")
    proposta.descricao_organizacao = request.POST.get("descricao_organizacao", "")
    proposta.departamento = request.POST.get("info_departamento", "")
    proposta.titulo = request.POST.get("titulo", "")

    proposta.descricao = request.POST.get("desc_projeto", "")
    proposta.expectativas = request.POST.get("expectativas", "")
    proposta.recursos = request.POST.get("recursos", "")
    proposta.observacoes = request.POST.get("observacoes", "")

    print(request.POST)
    tipo = request.POST.get("interesse", "")
    if tipo != "":
        proposta.tipo_de_interesse = int(tipo)

    proposta.save()

    cria_area_proposta(request, proposta)

    return proposta


def envia_proposta(proposta, enviar=True):
    """Envia Proposta por email."""

    # Isso tinha que ser feito por template, arrumar qualquer hora.
    message = "<h3>Proposta de Projeto para o PFE {0}.{1}</h3>\n\n".\
                   format(proposta.ano, proposta.semestre)

    message += "Para editar essa proposta acesse:</b>\n <a href='{0}'>{0}</a>\n\n".\
        format(settings.SERVER+proposta.get_absolute_url())

    message += "<b>Título da Proposta de Projeto:</b> {0}\n\n".format(proposta.titulo)
    message += "<b>Proposta submetida por:</b> {0} \n".format(proposta.nome)
    message += "<b>e-mail:</b> "
    for each in list(map(str.strip, re.split(",|;", proposta.email))):
        message += "&lt;{0}&gt; ".format(each)
    message += "\n\n"

    message += "<b>Nome da Organização:</b> {0}\n".\
        format(proposta.nome_organizacao)
    message += "<b>Website:</b> {0}\n".format(proposta.website)
    message += "<b>Endereco:</b> {0}\n".format(proposta.endereco)

    message += "\n\n"

    message += "<b>Contatos Técnicos:</b>\n {0}\n\n".\
                   format(proposta.contatos_tecnicos)

    message += "<b>Contatos Administrativos:</b>\n {0}\n\n".\
                   format(proposta.contatos_administrativos)

    message += "<b>Informações sobre a instituição/empresa:</b>\n {0}\n\n".\
                   format(proposta.descricao_organizacao)

    message += "<b>Informações sobre a departamento:</b>\n {0}\n\n".\
                   format(proposta.departamento)

    message += "\n\n"

    message += "<b>Descrição do Projeto:</b>\n {0}\n\n".format(proposta.descricao)
    message += "<b>Expectativas de resultados/entregas:</b>\n {0}\n\n".\
                   format(proposta.expectativas)

    message += "\n"

    message += "<b>Áreas/Habilidades envolvidas no projeto:</b>\n"
    message += lista_areas(proposta)

    message += "\n\n"
    message += "<b>Recursos a serem disponibilizados aos alunos:</b>\n {0}\n\n".\
                   format(proposta.recursos)
    message += "<b>Outras observações para os alunos:</b>\n {0}\n\n".\
                   format(proposta.observacoes)

    message += "<b>O principal interesse da empresa com o projeto é:</b>\n {0}\n\n".\
                   format(proposta.get_interesse())

    message += "\n\n"
    message += "<b>Data da proposta:</b> {0}\n\n\n".\
                   format(proposta.data.strftime("%d/%m/%Y %H:%M"))

    message += "\n\n"
    message += """
    <b>Obs.:</b> Ao submeter o projeto, deve ficar claro que a intenção do Projeto Final de Engenharia é 
    que os alunos tenham um contato próximo com as pessoas responsáveis nas instituições parceiras 
    para o desenvolvimento de uma solução em engenharia. Em geral os alunos se deslocam uma vez 
    por semana para entender melhor o desafio, demonstrar resultados preliminares, fazerem 
    planejamentos em conjunto, dentre de outros pontos que podem variar de projeto para projeto. 
    Também deve ficar claro que embora não exista um custo direto para as instituições parceiras, 
    essas terão de levar em conta que pelo menos um profissional deverá dedicar algumas horas 
    semanalmente para acompanhar os alunos. Além disso se a proposta contemplar gastos, como por 
    exemplo servidores, matéria prima de alguma forma, o Insper não terá condição de bancar tais 
    gastos e isso terá de ficar a cargo da empresa, contudo os alunos terão acesso aos 
    laboratórios do Insper para o desenvolvimento do projeto em horários agendados.<b>\n"""

    message = html.urlize(message)
    message = message.replace('\n', '<br>\n')

    subject = 'Proposta PFE : ({0}.{1} - {2}'.format(proposta.ano,
                                                     proposta.semestre,
                                                     proposta.titulo)

    if enviar:
        recipient_list = list(map(str.strip, re.split(",|;", proposta.email)))
        recipient_list += ["lpsoares@insper.edu.br",]

        check = email(subject, recipient_list, message)
        if check != 1:
            message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

    return message


def retorna_ternario(propostas):
    """Função retorna dados para gráfico ternário."""
    ternario = []
    for proposta in propostas:
        comp = 0
        comp += 1 if proposta.perfil_aluno1_computacao else 0
        comp += 1 if proposta.perfil_aluno2_computacao else 0
        comp += 1 if proposta.perfil_aluno3_computacao else 0
        comp += 1 if proposta.perfil_aluno4_computacao else 0

        mecat = 0
        mecat += 1 if proposta.perfil_aluno1_mecatronica else 0
        mecat += 1 if proposta.perfil_aluno2_mecatronica else 0
        mecat += 1 if proposta.perfil_aluno3_mecatronica else 0
        mecat += 1 if proposta.perfil_aluno4_mecatronica else 0

        meca = 0
        meca += 1 if proposta.perfil_aluno1_mecanica else 0
        meca += 1 if proposta.perfil_aluno2_mecanica else 0
        meca += 1 if proposta.perfil_aluno3_mecanica else 0
        meca += 1 if proposta.perfil_aluno4_mecanica else 0

        if proposta.organizacao:
            sigla = proposta.organizacao.sigla
        elif proposta.nome_organizacao:
            sigla = proposta.nome_organizacao
        else:
            sigla = ""

        total = (comp + mecat + meca) * 0.01
        if total:
            found = False
            for tern in ternario:
                if int(comp/total) == tern[0] and \
                   int(mecat/total) == tern[1] and \
                   int(meca/total) == tern[2]:
                    tern[3] += 3
                    if sigla:
                        tern[4] += ", " + sigla
                    found = True
                    break
            if not found:
                ternario.append([int(comp/total), int(mecat/total), int(meca/total), 5, sigla])
        else:
            found = False
            for tern in ternario:
                if tern[0] == 33 and tern[1] == 33 and tern[2] == 33:
                    tern[3] += 3
                    if sigla:
                        tern[4] += ", " + sigla
                    found = True
                    break
            if not found:
                ternario.append([33, 33, 33, 5, sigla])
    return ternario
