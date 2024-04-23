#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import re           # regular expression (para o import)
import PyPDF2

from django.conf import settings
from django.utils import html
from django.shortcuts import get_object_or_404
from django.template import Context, Template

from projetos.models import Proposta, Configuracao
from projetos.models import Area, AreaDeInteresse
from projetos.messages import email
from users.models import Opcao
from users.models import PFEUser
from users.support import adianta_semestre
from administracao.models import Carta

from operacional.models import Curso

def decodificar(campo, campos):
    """Recupera um campo de um documento PDF."""
    if campo in campos and "/V" in campos[campo]:
        if isinstance(campos[campo]["/V"], PyPDF2.generic.ByteStringObject):
            texto = campos[campo]["/V"].replace(b'\r', b'\n').decode('ISO-8859-1').strip() 
        else:
            texto = campos[campo]["/V"].strip()
        return texto.replace("\x00", "\uFFFD")
    return None


def areas_propostas(check_values, outras, proposta):
    todas_areas = Area.objects.filter(ativa=True)
    for area in todas_areas:
        if area.titulo in check_values:
            if not AreaDeInteresse.objects.filter(area=area, proposta=proposta).exists():
                AreaDeInteresse.create_proposta_area(proposta, area).save()
        else:
            if AreaDeInteresse.objects.filter(area=area, proposta=proposta).exists():
                AreaDeInteresse.objects.get(area=area, proposta=proposta).delete()

    if outras and outras != "":
        (outra, _created) = AreaDeInteresse.objects.get_or_create(area=None, proposta=proposta)
        outra.outras = outras
        outra.save()
    else:
        if AreaDeInteresse.objects.filter(area=None, proposta=proposta).exists():
            AreaDeInteresse.objects.get(area=None, proposta=proposta).delete()


def cria_area_proposta(request, proposta):
    """Cria um objeto Areas e preenche ele."""
    check_values = request.POST.getlist('selection')
    outras = request.POST.get("outras", "")
    areas_propostas(check_values, outras, proposta)
    return check_values


def cria_area_proposta_pdf(campos, proposta):
    """Cria um objeto Areas e preenche ele."""
    check_values = []
    for campo in campos:
        if "/V" in campos[campo]:
            if campos[campo]["/V"] == "/Yes":
                check_values.append(str(campo))
    outras = decodificar("outras", campos)
    areas_propostas(check_values, outras, proposta)
    return check_values


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
    if disponivel:  # somente as propostas disponibilizadas
        propostas = Proposta.objects.filter(ano=ano).\
                               filter(semestre=semestre).\
                               filter(disponivel=True)
    else:  # todas as propostas
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

    if disponivel:  # somente as propostas disponibilizadas
        propostas = propostas.filter(disponivel=True)

    for proposta in propostas:

        opcoes = Opcao.objects.filter(proposta=proposta)

        # Parte seguinte parece desnecessária
        opcoes = opcoes.filter(aluno__user__tipo_de_usuario=1)

        # Só opções para a proposta dos estudantes nesse ano e semester
        opcoes = opcoes.filter(aluno__anoPFE=proposta.ano).\
            filter(aluno__semestrePFE=proposta.semestre)

        if curso != 'T':
            opcoes = opcoes.filter(aluno__curso2__sigla_curta=curso)

        count = [0, 0, 0, 0, 0]
        estudantes_tmp = ["", "", "", "", ""]
        for opcao in opcoes:
            if opcao.prioridade == 1:
                count[0] += 1
                if estudantes_tmp[0] != "":
                    estudantes_tmp[0] += "; "
                estudantes_tmp[0] += opcao.aluno.user.get_full_name() + ' [' + opcao.aluno.curso2.sigla_curta + ']'
            elif opcao.prioridade == 2:
                count[1] += 1
                if estudantes_tmp[1] != "":
                    estudantes_tmp[1] += "; "
                estudantes_tmp[1] += opcao.aluno.user.get_full_name() + ' [' + opcao.aluno.curso2.sigla_curta + ']'
            elif opcao.prioridade == 3:
                count[2] += 1
                if estudantes_tmp[2] != "":
                    estudantes_tmp[2] += "; "
                estudantes_tmp[2] += opcao.aluno.user.get_full_name() + ' [' + opcao.aluno.curso2.sigla_curta + ']'
            elif opcao.prioridade == 4:
                count[3] += 1
                if estudantes_tmp[3] != "":
                    estudantes_tmp[3] += "; "
                estudantes_tmp[3] += opcao.aluno.user.get_full_name() + ' [' + opcao.aluno.curso2.sigla_curta + ']'
            elif opcao.prioridade == 5:
                count[4] += 1
                if estudantes_tmp[4] != "":
                    estudantes_tmp[4] += "; "
                estudantes_tmp[4] += opcao.aluno.user.get_full_name() + ' [' + opcao.aluno.curso2.sigla_curta + ']'

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
    if proposta is None:  # proposta nova
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

    proposta.nome = request.POST.get("nome", "").strip()
    proposta.email = request.POST.get("email", "").strip()
    proposta.website = request.POST.get("website", "").strip()
    proposta.nome_organizacao = request.POST.get("organizacao", "").strip()
    proposta.endereco = request.POST.get("endereco", "")
    proposta.contatos_tecnicos = request.POST.get("contatos_tecnicos", "")
    proposta.contatos_administrativos = request.POST.get("contatos_adm", "")
    proposta.descricao_organizacao = request.POST.get("descricao_organizacao", "")
    proposta.departamento = request.POST.get("info_departamento", "")
    proposta.titulo = request.POST.get("titulo", "").strip()

    proposta.descricao = request.POST.get("desc_projeto", "")
    proposta.expectativas = request.POST.get("expectativas", "")
    proposta.recursos = request.POST.get("recursos", "")
    proposta.observacoes = request.POST.get("observacoes", "")

    proposta.aprimorar = "aprimorar" in request.POST
    proposta.realizar = "realizar" in request.POST
    proposta.iniciar = "iniciar" in request.POST
    proposta.identificar = "identificar" in request.POST
    proposta.mentorar = "mentorar" in request.POST

    proposta.save()

    cria_area_proposta(request, proposta)

    return proposta


def preenche_proposta_pdf(campos, proposta):
    """Preenche um proposta a partir de um dicionario PDF."""
    if proposta is None:  # proposta nova
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

    proposta.nome = campos["nome"]
    proposta.email = campos["email"]

    proposta.website = decodificar("site", campos)
    proposta.nome_organizacao = decodificar("organizacao", campos)
    proposta.endereco = decodificar("endereco", campos)
    proposta.contatos_tecnicos = decodificar("contatos_tecnicos", campos)
    proposta.contatos_administrativos = decodificar("contatos_administrativos", campos)
    proposta.descricao_organizacao = decodificar("descricao_organizacao", campos)
    proposta.departamento = decodificar("departamento", campos)

    proposta.titulo = decodificar("titulo", campos)
    proposta.descricao = decodificar("descricao", campos)
    proposta.expectativas = decodificar("expectativas", campos)

    proposta.recursos = decodificar("recursos", campos)
    proposta.observacoes = decodificar("observacoes", campos)

    mensagem = ""
    if proposta.nome == None:
        proposta.nome = "NOME NÃO DEFINIDO"
        mensagem += "NOME NÃO DEFINIDO<br>"
    if proposta.titulo == None:
        proposta.titulo = "TÍTULO NÃO DEFINIDO"
        mensagem += "TÍTULO NÃO DEFINIDO<br>"
    if proposta.descricao == None:
        proposta.descricao = "DESCRIÇÃO NÃO DEFINIDA"
        mensagem += "DESCRIÇÃO NÃO DEFINIDA<br>"
    if proposta.contatos_tecnicos == None:
        proposta.contatos_tecnicos = "CONTATOS TÉCNICOS NÃO DEFINIDOS"
        mensagem += "CONTATOS TÉCNICOS NÃO DEFINIDOS<br>"
    if proposta.expectativas == None:
        proposta.expectativas = "EXPECTATIVAS NÃO DEFINIDAS"
        mensagem += "EXPECTATIVAS NÃO DEFINIDAS<br>"

    proposta.save()

    check_values = cria_area_proposta_pdf(campos, proposta)

    proposta.aprimorar =  "interesse#0" in check_values
    proposta.realizar =  "interesse#1" in check_values
    proposta.iniciar =  "interesse#2" in check_values
    proposta.identificar =  "interesse#3" in check_values
    proposta.mentorar =  "interesse#4" in check_values
    
    proposta.save()

    return proposta, mensagem

def lista_interesses(proposta):
    message = ""
    if proposta.aprimorar:
        message += "- {0}<br>".format(Proposta.TIPO_INTERESSE[0][1])
    if proposta.realizar:
        message += "- {0}<br>".format(Proposta.TIPO_INTERESSE[1][1])
    if proposta.iniciar:
        message += "- {0}<br>".format(Proposta.TIPO_INTERESSE[2][1])
    if proposta.identificar:
        message += "- {0}<br>".format(Proposta.TIPO_INTERESSE[3][1])
    if proposta.mentorar:
        message += "- {0}<br>".format(Proposta.TIPO_INTERESSE[4][1])
    return message

def envia_proposta(proposta, enviar=True):
    """Envia Proposta por email."""

    context_carta = {
            "proposta": proposta,
            "settings": settings,
            "emails": list(map(str.strip, re.split(",|;", proposta.email))),
            "lista_areas": lista_areas(proposta),
            "lista_interesses": lista_interesses(proposta),
        }
    carta = get_object_or_404(Carta, template="Proposta de Projeto")
    t = Template(carta.texto)
    message = t.render(Context(context_carta))
    message = html.urlize(message) # Faz links de e-mail, outros sites funcionarem

    subject = "Proposta PFE : ({0}.{1} - {2})".format(proposta.ano,
                                                      proposta.semestre,
                                                      proposta.titulo)

    if enviar:
        recipient_list = list(map(str.strip, re.split(",|;", proposta.email)))

        # coordenacoes = PFEUser.objects.filter(tipo_de_usuario=4)
        # for coordenador in coordenacoes:
        #     recipient_list.append(str(coordenador.email))
        configuracao = get_object_or_404(Configuracao)
        recipient_list.append(str(configuracao.coordenacao.user.email))

        check = email(subject, recipient_list, message)
        if check != 1:
            message = "<b>Algum problema de conexão, contacte: lpsoares@insper.edu.br</b>"

    return message


def retorna_ternario(propostas, cursos):
    """Função retorna dados para gráfico ternário."""
    ternario = [] # Lista com todas as propostas
    count = {}
    vagas = {}
    for curso in cursos: # para total de vagas
        vagas[curso] = 0

    for proposta in propostas:

        for curso in cursos:
            count[curso] = 0
            for i in range(1,5):
                if curso in getattr(proposta, "perfil"+str(i)).all(): 
                    count[curso] += 1
            vagas[curso] += count[curso]

        if proposta.organizacao:
            sigla = proposta.organizacao.sigla
        elif proposta.nome_organizacao:
            sigla = proposta.nome_organizacao
        else:
            sigla = "IND"

        # Porcentagem do total
        total = sum(count.values()) * 0.01

        # ternario [0, 1 e 2] São as posicoes no gráfico
        # ternario [3] é o peso, se só tiver um projeto é 5, ao repetir ganha +3
        # ternario [4] nome das empresas das propostas

        if total: # Não estão vazias as definições de perfis
            found = False
            med = [int(count[cursos[0]]/total), int(count[cursos[1]]/total), int(count[cursos[2]]/total)]
            for tern in ternario: # Procura se alguem já na posição do plot
                if med[0] == tern[0] and med[1] == tern[1] and med[2] == tern[2]:
                    tern[3] += 3
                    tern[4] += ", " + sigla
                    found = True
                    break
            if not found:
                ternario.append(med + [5, sigla])
        else:  # Estão vazias as definições de perfis
            found = False
            for tern in ternario:
                if tern[0] == 33 and tern[1] == 33 and tern[2] == 33:
                    tern[3] += 3
                    tern[4] += ", " + sigla
                    found = True
                    break
            if not found:
                ternario.append([33, 33, 33, 5, sigla])
    return vagas, ternario
