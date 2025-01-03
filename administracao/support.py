#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 13 de Junho de 2023
"""

import datetime
import dateutil.parser

from django.conf import settings
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied  # Para erro 400
from django.shortcuts import render, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.http import Http404

from administracao.models import TipoEvento

from users.models import PFEUser, Aluno, Professor, Parceiro

from projetos.models import Organizacao, Evento
from projetos.models import Configuracao
from projetos.support import get_upload_path, simple_upload

from operacional.models import Curso


def limpa_texto(texto):
    """Remove caracteres especiais do texto."""
    return texto.replace("\x00", "\uFFFD") if texto else None

def get_limite_propostas(configuracao):
    evento = Evento.get_evento(sigla="IIPE", configuracao=configuracao)
    if evento is not None:
        return evento.endDate
    inicio_pfe = dateutil.parser.parse("07/06/2018").date()
    return inicio_pfe

# Melhor dar preferência para essa rotina que retorna None se não houver data planejada
def get_limite_propostas2(configuracao):
    evento = Evento.get_evento(sigla="IIPE", configuracao=configuracao) 
    return evento.endDate if evento else None
    
def get_data_planejada(configuracao):
    """Retorna a data planejada para a liberação das propostas"""
    evento = Evento.get_evento(sigla="APDE", configuracao=configuracao)
    return evento.endDate if evento else None

def propostas_liberadas(configuracao):
    """Verifica se as propostas estão liberadas."""
    hoje = datetime.date.today()
    liberacao = get_data_planejada(configuracao)
    if liberacao and hoje >= liberacao:
            return True
    return False

def usuario_sem_acesso(request, acessos):
    """Verifica se o usuário tem acesso a determinada área."""
    if (not request.user.is_authenticated) or (request.user is None):
        raise PermissionDenied("Você não está autenticado!")
    if request.user.tipo_de_usuario not in acessos:
        raise PermissionDenied("Você não tem privilégios de acesso a essa área!")

def registra_organizacao(request, org=None):
    """Rotina para cadastrar organizacao no sistema."""
    if not org:
        organizacao = Organizacao.create()
    else:
        organizacao = org

    nome = request.POST.get("nome", None)
    if nome:
        organizacao.nome = nome.strip()

    sigla = request.POST.get("sigla", None)
    if sigla:
        organizacao.sigla = sigla.strip()

    organizacao.endereco = request.POST.get("endereco", None)

    website = request.POST.get("website", "").strip()
    if website:
        if website[:4] == "http":
            organizacao.website = website
        else:
            organizacao.website = "http://" + website
    else:
        organizacao.website = None

    organizacao.informacoes = request.POST.get("informacoes", None)

    cnpj = request.POST.get("cnpj", None)
    if cnpj:
        organizacao.cnpj = cnpj[:2]+cnpj[3:6]+cnpj[7:10]+cnpj[11:15]+cnpj[16:18]

    organizacao.inscricao_estadual = request.POST.get("inscricao_estadual", None)
    organizacao.razao_social = request.POST.get("razao_social", None)
    organizacao.ramo_atividade = request.POST.get("ramo_atividade", None)

    if "logo" in request.FILES:
        logotipo = simple_upload(request.FILES["logo"],
                                    path=get_upload_path(organizacao, ""))
        organizacao.logotipo = logotipo[len(settings.MEDIA_URL):]

    organizacao.save()

    return organizacao, "", 200


def registro_usuario(request, user=None):
    """Rotina para cadastrar usuário no sistema."""
    usuario = PFEUser.create() if not user else user  # Cria um usuário novo ou atualiza um existente

    email = request.POST.get("email", None)
    if email:
        usuario.email = email.strip()

    if usuario.tipo_de_usuario == 4:  # Administrador
        pass # Não mudar status de administrador por aqui
    else:
        tipo_de_usuario = request.POST.get("tipo_de_usuario", None)
        if tipo_de_usuario == "estudante":
            usuario.tipo_de_usuario = 1  # (1, "estudante") 
        elif tipo_de_usuario == "professor":
            usuario.tipo_de_usuario = 2  # (2, "professor")
        elif tipo_de_usuario == "parceiro":
            usuario.tipo_de_usuario = 3  # (3, "parceiro")
        elif tipo_de_usuario == "funcionario":
            usuario.tipo_de_usuario = 2  # (2, "professor") / funcionario
        else:
            # usuario.tipo_de_usuario = 4  # (4, "administrador")
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

    usuario.pronome_tratamento = limpa_texto(request.POST.get("pronome_tratamento", None))
    usuario.nome_social = limpa_texto(request.POST.get("nome_social", None))

    if "genero" in request.POST:
        if request.POST['genero'] == "masculino":
            usuario.genero = 'M'
        elif request.POST['genero'] == "feminino":
            usuario.genero = 'F'
    else:
        usuario.genero = 'X'

    usuario.telefone = limpa_texto(request.POST.get("telefone", None))
    usuario.celular = limpa_texto(request.POST.get("celular", None))
    usuario.instant_messaging = limpa_texto(request.POST.get("instant_messaging", None))
    usuario.linkedin = limpa_texto(request.POST.get("linkedin", None))
    usuario.tipo_lingua = limpa_texto(request.POST.get("lingua", None))
    usuario.observacoes = limpa_texto(request.POST.get("observacao", None))

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

        estudante.matricula = request.POST.get("matricula", None)

        curso = request.POST.get("curso", None)

        estudante.curso2 = Curso.objects.get(sigla=curso)
        
        try:
            estudante.anoPFE = int(request.POST["ano"])
            estudante.semestrePFE = int(request.POST["semestre"])
        except (ValueError, OverflowError, MultiValueDictKeyError):
            estudante.anoPFE = None
            estudante.semestrePFE = None
            mensagem += "Erro na identificação do ano e semestre.<br>"

        try:
            estudante.cr = float(request.POST["cr"])
        except (ValueError, OverflowError, MultiValueDictKeyError):
            pass
            #estudante.cr = 0
        
        externo_check = request.POST.get("externo_check", None)
        if externo_check == "True":
            estudante.externo = request.POST.get("externo", None)
        else:
            estudante.externo = None

        estudante.trancado = "estudante_trancado" in request.POST

        estudante.save()
        
        usuario.groups.add(Group.objects.get(name="Estudante"))  # Grupo de permissões


    elif usuario.tipo_de_usuario == 2:  # professor

        if not hasattr(user, "professor"):
            professor = Professor.create(usuario)
        else:
            professor = user.professor

        if tipo_de_usuario == "funcionario":
            professor.dedicacao = "O"  # ("O", "Outro"),

            professor.departamento = limpa_texto(request.POST.get("departamento", None))

        else:
            dedicacao = request.POST.get("dedicacao", None)
            if dedicacao == "TI":  # ("TI", "Tempo Integral"),
                professor.dedicacao = "TI"
            elif dedicacao == "TP":  # ("TP", 'Tempo Parcial'),
                professor.dedicacao = "TP"
            elif dedicacao == "V":  # ("V", "Visitante"),
                professor.dedicacao = "V"
            elif dedicacao == "E":  # ("E", "Externo"),
                professor.dedicacao = "E"
            elif dedicacao == "O":  # ("O", "Outro"),
                professor.dedicacao = "O"
            else:
                professor.dedicacao = None
                mensagem += "Erro na identificação de tipo de dedicação do professor.<br>"

            professor.areas = limpa_texto(request.POST.get("areas", None))
            professor.website = limpa_texto(request.POST.get("website", None))
            professor.lattes = limpa_texto(request.POST.get("lattes", None))

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

        if not hasattr(user, "parceiro"):
            parceiro = Parceiro.create(usuario)
        else:
            parceiro = user.parceiro

        parceiro.cargo = request.POST.get("cargo", None)
        
        try:
            tmp_pk = int(request.POST["organizacao"])
            parceiro.organizacao = Organizacao.objects.get(pk=tmp_pk)
        except (ValueError, OverflowError, Organizacao.DoesNotExist):
            parceiro.organizacao = None
            mensagem += "Organização não encontrada.<br>"

        parceiro.principal_contato = "principal_contato" in request.POST

        parceiro.save()

        # Tipos individuais estão obsoletos, usar somente grupos !
        content_type = ContentType.objects.get_for_model(Parceiro)
        permission = Permission.objects.get(
            codename="change_parceiro",
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
    
