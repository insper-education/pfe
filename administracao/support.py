#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 13 de Junho de 2023
"""

import dateutil.parser

from django.conf import settings
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError

from users.models import PFEUser, Aluno, Professor, Parceiro

from projetos.models import Organizacao, Evento
from projetos.support import get_upload_path, simple_upload

from operacional.models import Curso


def limpa_texto(texto):
    """Remove caracteres especiais do texto."""
    if texto is None:
        return None
    return texto.replace("\x00", "\uFFFD")


def get_limite_propostas(configuracao):
    if configuracao.semestre == 1:
        evento = Evento.objects.filter(tipo_de_evento=123, endDate__year=configuracao.ano, endDate__month__lt=7).order_by("endDate", "startDate").last()
    else:
        evento = Evento.objects.filter(tipo_de_evento=123, endDate__year=configuracao.ano, endDate__month__gt=6).order_by("endDate", "startDate").last()
    # (123, 'Indicação de interesse nos projetos do próximo semestre pelos estudante')

    if evento is not None:
        return evento.endDate
    
    inicio_pfe = dateutil.parser.parse("07/06/2018").date()
    return inicio_pfe

def get_data_planejada(configuracao):
    if configuracao.semestre == 1:
        evento = Evento.objects.filter(tipo_de_evento=113, endDate__year=configuracao.ano, endDate__month__lt=7).order_by("endDate", "startDate").last()
    else:
        evento = Evento.objects.filter(tipo_de_evento=113, endDate__year=configuracao.ano, endDate__month__gt=6).order_by("endDate", "startDate").last()
    # (113, 'Apresentação das propostas de projetos disponíveis para estudantes', 'darkslategray'),

    if evento is not None:
        return evento.endDate

    return None



def usuario_sem_acesso(request, acessos):
    
    if (not request.user.is_authenticated) or (request.user is None):
        mensagem = "Você não está autenticado!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    if request.user.tipo_de_usuario not in acessos:
        mensagem = "Você não tem privilégios de acesso a essa área!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)


def registra_organizacao(request, org=None):
    """Rotina para cadastrar organizacao no sistema."""
    if not org:
        organizacao = Organizacao.create()
    else:
        organizacao = org

    nome = request.POST.get('nome', None)
    if nome:
        organizacao.nome = nome.strip()

    sigla = request.POST.get('sigla', None)
    if sigla:
        organizacao.sigla = sigla.strip()

    organizacao.endereco = request.POST.get('endereco', None)

    website = request.POST.get('website', None)
    if website:
        if website[:4] == "http":
            organizacao.website = website.strip()
        else:
            organizacao.website = "http://" + website.strip()

    organizacao.informacoes = request.POST.get('informacoes', None)

    cnpj = request.POST.get('cnpj', None)
    if cnpj:
        organizacao.cnpj = cnpj[:2]+cnpj[3:6]+cnpj[7:10]+cnpj[11:15]+cnpj[16:18]

    organizacao.inscricao_estadual = request.POST.get('inscricao_estadual', None)
    organizacao.razao_social = request.POST.get('razao_social', None)
    organizacao.ramo_atividade = request.POST.get('ramo_atividade', None)

    if 'logo' in request.FILES:
        logotipo = simple_upload(request.FILES['logo'],
                                    path=get_upload_path(organizacao, ""))
        organizacao.logotipo = logotipo[len(settings.MEDIA_URL):]

    organizacao.save()

    return "", 200



def registro_usuario(request, user=None):
    """Rotina para cadastrar usuário no sistema."""
    if not user:
        usuario = PFEUser.create()  # Serve para diferenciar um usuário novo
    else:
        usuario = user

    email = request.POST.get('email', None)
    if email:
        usuario.email = email.strip()

    tipo_de_usuario = request.POST.get('tipo_de_usuario', None)
    if tipo_de_usuario == "estudante":
        usuario.tipo_de_usuario = 1  # (1, 'aluno') 
    elif tipo_de_usuario == "professor":
        usuario.tipo_de_usuario = 2  # (2, 'professor')
    elif tipo_de_usuario == "parceiro":
        usuario.tipo_de_usuario = 3  # (3, 'parceiro')
    else:
        # usuario.tipo_de_usuario = 3  # (4, 'administrador')
        return ("Erro na identificação do tipo de usuário.", 401, None)

    # se for um usuário novo
    if not user:
        if usuario.tipo_de_usuario == 1 or usuario.tipo_de_usuario == 2:
            username = request.POST["email"].split('@')[0]
        elif usuario.tipo_de_usuario == 3:
            username = request.POST["email"].split('@')[0] + '.' + \
                request.POST["email"].split('@')[1].split('.')[0]
        else:
            return ("Erro na recuperação do e-mail.", 401, None)

        #if PFEUser.objects.exclude(pk=usuario.pk).filter(username=username).exists():
        already_exist = PFEUser.objects.filter(username__iexact=username)
        if already_exist.exists():
            return ('Username "%s" já está sendo usado.' % already_exist.last().username, 401, None)

        usuario.username = username

    if "nome" in request.POST and len(request.POST["nome"].split()) > 1:
        usuario.first_name = limpa_texto(request.POST["nome"].split()[0])
        usuario.last_name = limpa_texto(' '.join(request.POST["nome"].split()[1:]))

    else:
        return ("Erro: Não inserido nome completo no formulário.", 401, None)

    if "genero" in request.POST:
        if request.POST['genero'] == "masculino":
            usuario.genero = 'M'
        elif request.POST['genero'] == "feminino":
            usuario.genero = 'F'
    else:
        usuario.genero = 'X'

    usuario.telefone = limpa_texto(request.POST.get('telefone', None))
    usuario.celular = limpa_texto(request.POST.get('celular', None))
    usuario.instant_messaging = limpa_texto(request.POST.get('instant_messaging', None))
    usuario.linkedin = limpa_texto(request.POST.get('linkedin', None))
    usuario.tipo_lingua = limpa_texto(request.POST.get('lingua', None))
    usuario.observacoes = limpa_texto(request.POST.get('observacao', None))

    if "ativo" in request.POST:
        if request.POST["ativo"] == '1':
            usuario.is_active = True
        else:
            usuario.is_active = False

    if 'comite' in request.POST:
        if request.POST["comite"] == '1':
            usuario.membro_comite = True
        else:
            usuario.membro_comite = False

    usuario.save()

    # Agora que o usuario foi criado, criar o tipo para não gerar inconsistências
    mensagem = ""

    if usuario.tipo_de_usuario == 1:  # estudante

        if not hasattr(user, "aluno"):
            estudante = Aluno.create(usuario)
        else:
            estudante = user.aluno

        estudante.matricula = request.POST.get('matricula', None)

        curso = request.POST.get('curso', None)

        estudante.curso2 = Curso.objects.get(sigla=curso)
        
        try:
            estudante.anoPFE = int(request.POST['ano'])
            estudante.semestrePFE = int(request.POST['semestre'])
        except (ValueError, OverflowError, MultiValueDictKeyError):
            estudante.anoPFE = None
            estudante.semestrePFE = None
            mensagem += "Erro na identificação do ano e semestre.<br>"

        try:
            estudante.cr = float(request.POST['cr'])
        except (ValueError, OverflowError, MultiValueDictKeyError):
            pass
            #estudante.cr = 0

        estudante.trancado = "estudante_trancado" in request.POST

        estudante.save()
        
        usuario.groups.add(Group.objects.get(name="Estudante"))  # Grupo de permissões


    elif usuario.tipo_de_usuario == 2:  # professor

        if not hasattr(user, "professor"):
            professor = Professor.create(usuario)
        else:
            professor = user.professor

        dedicacao = request.POST.get('dedicacao', None)
        if dedicacao == "ti":  # ("TI", "Tempo Integral"),
            professor.dedicacao = 'TI'
        elif dedicacao == "tp":  # ("TP", 'Tempo Parcial'),
            professor.dedicacao = 'TP'
        else:
            professor.dedicacao = None
            mensagem += "Erro na identificação de tipo de dedicação do professor.<br>"

        professor.areas = limpa_texto(request.POST.get('areas', None))
        professor.website = limpa_texto(request.POST.get('website', None))
        professor.lattes = limpa_texto(request.POST.get('lattes', None))

        professor.save()

        # Tipos individuais estão obsoletos, usar somente grupos !
        content_type = ContentType.objects.get_for_model(Professor)
        try:
            permission = Permission.objects.get(
                codename="change_professor",
                content_type=content_type,
            )
            usuario.user_permissions.add(permission)
        except Permission.DoesNotExist:
            pass  # não encontrada a permissão
        try:  # <Permission: users | Professor | Professor altera valores>
            permission = Permission.objects.get(
                codename="altera_professor",
                content_type=content_type,
            )
            usuario.user_permissions.add(permission)
        except Permission.DoesNotExist:
            pass  # não encontrada a permissão
        usuario.save()
        ##################### ^^^^  REMOVER ^^^^ #################

        usuario.groups.add(Group.objects.get(name="Professor"))  # Grupo de permissões


    elif usuario.tipo_de_usuario == 3:  # Parceiro

        if not hasattr(user, 'parceiro'):
            parceiro = Parceiro.create(usuario)
        else:
            parceiro = user.parceiro

        parceiro.cargo = request.POST.get('cargo', None)
        
        try:
            tmp_pk = int(request.POST['organizacao'])
            parceiro.organizacao = Organizacao.objects.get(pk=tmp_pk)
        except (ValueError, OverflowError, Organizacao.DoesNotExist):
            parceiro.organizacao = None
            mensagem += "Organização não encontrada.<br>"

        parceiro.principal_contato = 'principal_contato' in request.POST

        parceiro.save()

        # Tipos individuais estão obsoletos, usar somente grupos !
        content_type = ContentType.objects.get_for_model(Parceiro)
        permission = Permission.objects.get(
            codename='change_parceiro',
            content_type=content_type,
        )
        usuario.user_permissions.add(permission)
        usuario.save()
        ##################### ^^^^  REMOVER ^^^^ #################

        usuario.groups.add(Group.objects.get(name="Parceiro"))  # Grupo de permissões

    # elif usuario.tipo_de_usuario == 4:  # Administrador
        # user.groups.add(Group.objects.get(name="Administrador"))  # Grupo de permissões

    if mensagem != "":
        return (mensagem, 401, None)
    elif user:
        return ("Usuário atualizado na base de dados.", 200, usuario)
    else:
        return ("Usuário inserido na base de dados.", 200, usuario)
    
