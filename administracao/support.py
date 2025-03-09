#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 13 de Junho de 2023
"""

import os
import re
import datetime
import dateutil.parser
import string
import random

from git import Repo

from django.conf import settings
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied  # Para erro 400
from django.shortcuts import get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError

from projetos.messages import email, render_message
from projetos.models import Organizacao, Evento
from projetos.models import Configuracao
from projetos.support import get_upload_path, simple_upload

from operacional.models import Curso

from users.models import PFEUser, Aluno, Professor, Parceiro

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
    return (liberacao and hoje >= liberacao)

def usuario_sem_acesso(request, acessos):
    """Verifica se o usuário tem acesso a determinada área."""
    if (not request.user.is_authenticated) or (request.user is None):
        raise PermissionDenied("Você não está autenticado!")
    if request.user.tipo_de_usuario not in acessos:
        raise PermissionDenied("Você não tem privilégios de acesso a essa área!")

def registra_organizacao(request, organizacao=None):
    """Rotina para cadastrar organizacao no sistema."""

    if organizacao is None:
        organizacao = Organizacao()
    
    organizacao.nome = request.POST.get("nome", "").strip()
    organizacao.sigla = request.POST.get("sigla", "").strip()
    organizacao.endereco = request.POST.get("endereco", None)
    organizacao.informacoes = request.POST.get("informacoes", None)

    website = request.POST.get("website", "").strip()
    if website:
        if website[:4] == "http":
            organizacao.website = website
        else:
            organizacao.website = "http://" + website
    else:
        organizacao.website = None

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
    usuario = PFEUser() if not user else user  # Cria um usuário novo ou atualiza um existente

    usuario.email = request.POST.get("email", "").strip()

    tipo_de_usuario = request.POST.get("tipo_de_usuario", None)
    if usuario.tipo_de_usuario == 4:  # Administrador
        pass # Não mudar status de administrador por aqui
    else:
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
        if request.POST["genero"] == "masculino":
            usuario.genero = 'M'
        elif request.POST["genero"] == "feminino":
            usuario.genero = 'F'
    else:
        usuario.genero = 'X'

    usuario.telefone = limpa_texto(request.POST.get("telefone", None))
    usuario.celular = limpa_texto(request.POST.get("celular", None))
    usuario.instant_messaging = limpa_texto(request.POST.get("instant_messaging", None))
    usuario.linkedin = limpa_texto(request.POST.get("linkedin", None))
    usuario.tipo_lingua = limpa_texto(request.POST.get("lingua", None))
    usuario.conta_github = limpa_texto(request.POST.get("conta_github", None))
    usuario.observacoes = limpa_texto(request.POST.get("observacao", None))

    if "ativo" in request.POST:
        if request.POST["ativo"] == '1':
            usuario.is_active = True
        else:
            usuario.is_active = False

    if "comite" in request.POST:
        if request.POST["comite"] == '1':
            usuario.membro_comite = True
        else:
            usuario.membro_comite = False

    usuario.save()

    # Agora que o usuario foi criado, criar o tipo para não gerar inconsistências
    mensagem = ""

    if tipo_de_usuario == "estudante":  # estudante
        estudante, _ = Aluno.objects.get_or_create(user=usuario)
        estudante.matricula = request.POST.get("matricula", None)
        estudante.curso2 = Curso.objects.filter(sigla=request.POST.get("curso", None)).last()
        try:
            estudante.ano = int(request.POST["ano"])
            estudante.semestre = int(request.POST["semestre"])
        except (ValueError, OverflowError, MultiValueDictKeyError):
            estudante.ano = None
            estudante.semestre = None
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


    elif tipo_de_usuario == "professor" or tipo_de_usuario == "funcionario":  # professor

        professor, _ = Professor.objects.get_or_create(user=usuario)
        
        if tipo_de_usuario == "funcionario":
            professor.dedicacao = "O"  # ("O", "Outro"),
            professor.departamento = limpa_texto(request.POST.get("departamento", None))

        else:
            dedicacao = request.POST.get("dedicacao", None)
            if dedicacao in [subl[0] for subl in Professor.TIPO_DEDICACAO]:
                professor.dedicacao = dedicacao
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


    elif tipo_de_usuario == "parceiro":  # Parceiro
        parceiro, _ = Parceiro.objects.get_or_create(user=usuario)

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
    

def envia_senha_mensagem(user):

    # Atualizando senha do usuário.
    senha = ''.join(random.SystemRandom().
                    choice(string.ascii_lowercase + string.digits)
                    for _ in range(6))
    user.set_password(senha)
    user.save()

    context_carta = {
        "user": user,
        "senha": senha,
        "coordenacao": get_object_or_404(Configuracao).coordenacao,
    }
    message_email = render_message("Envio Senha", context_carta)

    # Enviando e-mail com mensagem para usuário.
    subject = "Capstone | Conta de Usuário: " + user.get_full_name()
    recipient_list = [user.email,]

    email(subject, recipient_list, message_email)
    mensagem = "<br><br>Enviado mensagem com senha para: "
    mensagem += user.get_full_name() + " " + "&lt;" + user.email + "&gt;<br>\n"
    codigo = 200
    
    return mensagem, codigo


def puxa_github(projeto):
    """Detecta repositorios github no projeto."""    

    if not projeto.pastas_do_projeto:
        return []

    pastas_do_projeto = re.split(r'[ ,;\n\t]+', projeto.pastas_do_projeto)

    repositorios = []
    for pasta in pastas_do_projeto:
        pasta = pasta.strip()
        if "https://github.com/" == pasta[:19] or "git@github.com:" == pasta[:15]:
            if pasta[-1] == '/':
                pasta = pasta[:-1]
            repositorios.append(pasta)
    return repositorios


def backup_github(projeto):
    """Faz backup dos repositórios github no projeto."""

    repositorios = puxa_github(projeto)
    if not repositorios:
        return

    path = get_upload_path(projeto, "")
    full_path = os.path.join(settings.MEDIA_ROOT, path, "git")
    if not os.path.exists(full_path):
        os.makedirs(full_path)

    token = settings.GITHUB_TOKEN
    for repo_url in repositorios:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_dir = os.path.join(full_path, repo_name)

        repo_url_with_token = repo_url.replace("https://", f"https://{token}@")

        try:
            if os.path.exists(repo_dir):
                # Updating repository
                repo = Repo(repo_dir)
                repo.remotes.origin.set_url(repo_url_with_token)
                repo.remotes.origin.pull()
            else:
                # Cloning repository
                Repo.clone_from(repo_url_with_token, repo_dir)
        except Exception as e:
            # Erro ao clonar repositório
            pass
