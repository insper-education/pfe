#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import re
import string
import random
import tablib
import axes.utils
import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.core.exceptions import SuspiciousOperation  # Para erro 400
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import timezone

from axes.models import AccessAttempt, AccessLog

from documentos.support import render_to_pdf

from projetos.models import Configuracao, Organizacao, Proposta, Projeto
from projetos.models import Avaliacao2, Feedback, Disciplina
from projetos.messages import email

from .support import get_upload_path, registra_organizacao, registro_usuario

from projetos.support import simple_upload

from projetos.resources import DisciplinasResource
from projetos.resources import Avaliacoes2Resource
from projetos.resources import ProjetosResource
from projetos.resources import OrganizacoesResource
from projetos.resources import OpcoesResource
from projetos.resources import ProfessoresResource
from projetos.resources import EstudantesResource
from projetos.resources import ParceirosResource
from projetos.resources import ConfiguracaoResource
from projetos.resources import FeedbacksResource
from projetos.resources import UsuariosResource

from users.models import PFEUser, Aluno, Professor, Parceiro, Administrador
from users.models import Opcao, Alocacao

from users.support import adianta_semestre, adianta_semestre_conf

from propostas.support import ordena_propostas

from operacional.models import Curso

from .support import usuario_sem_acesso


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def index_administracao(request):
    """Mostra página principal para administração do sistema."""
    return render(request, "administracao/index_admin.html")


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def index_carregar(request):
    """Para carregar dados de arquivos para o servidor."""
    return render(request, "administracao/carregar.html")


@login_required
@transaction.atomic
@permission_required("projetos.add_disciplina", raise_exception=True)
def cadastrar_disciplina(request, proposta_id=None):
    """Cadastra Organização na base de dados."""
    context = {
        "disciplinas": Disciplina.objects.all().order_by("nome"),
        "Disciplina": Disciplina,
    }
    if request.method == "POST":
        try:
            assert "nome" in request.POST
            disciplina, _created = Disciplina.objects.get_or_create(nome=request.POST["nome"])
            if not _created:
                context["mensagem"] = "Conflito: Disciplina já cadastrada"
            else:
                disciplina.save()
                context["mensagem"] = "Disciplina cadastrada na base de dados."
        except:
            return HttpResponse("<h3 style='color:red'>Falha na inserção na base da dados.<br>"+settings.CONTATO+"<h3>")

    return render(request, "administracao/cadastra_disciplina.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def cadastrar_organizacao(request, proposta_id=None):
    """Cadastra Organização na base de dados."""
    if request.method == "POST":

        if "nome" in request.POST and "sigla" in request.POST:

            org_ja_existe = Organizacao.objects.filter(nome=request.POST["nome"]) | Organizacao.objects.filter(sigla=request.POST["sigla"])
            if org_ja_existe:
                context = {
                    "voltar": True,
                    "organizacao": org_ja_existe.last(),
                    "area_principal": True,
                    "mensagem": "<h3 style='color:red'>Conflito: Organização já cadastrada!</h3>",
                }

            else:
                organizacao, mensagem, codigo = registra_organizacao(request)
                if codigo != 200:
                    return HttpResponse(mensagem, status=codigo)

                context = {
                    "voltar": True,
                    "organizacao": organizacao,
                    "organizacoes_lista": True,
                    "area_principal": True,
                    "mensagem": "Organização inserida na base de dados.",
                }

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.<h3>",
            }

        return render(request, "generic.html", context=context)

    proposta = None
    if proposta_id:
        proposta = get_object_or_404(Proposta, id=proposta_id)

    context = {
        "proposta": proposta,
        "organizacao": Organizacao,
    }
    
    return render(request, "administracao/cadastra_organizacao.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def edita_organizacao(request, primarykey):
    """Edita Organização na base de dados."""

    organizacao = get_object_or_404(Organizacao, id=primarykey)

    if request.method == "POST":

        if "nome" in request.POST and "sigla" in request.POST:

            _, mensagem, codigo = registra_organizacao(request, organizacao)
            if codigo != 200:
                return HttpResponse(mensagem, status=codigo)

            context = {
                "voltar": True,
                "organizacao": organizacao,
                "organizacoes_lista": True,
                "area_principal": True,
                "mensagem": "Organização atualizada na base de dados.",
            }

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.<h3>",
            }

        return render(request, "generic.html", context=context)

    context = {
        "organizacao": organizacao,
        "edicao": True,
    }

    return render(request, "administracao/cadastra_organizacao.html", context=context)



def envia_senha_mensagem(user):

    # Atualizando senha do usuário.
    senha = ''.join(random.SystemRandom().
                    choice(string.ascii_lowercase + string.digits)
                    for _ in range(6))
    user.set_password(senha)
    user.save()

    configuracao = get_object_or_404(Configuracao)
    coordenacao = configuracao.coordenacao

    # USAR TEMPLATE ARMAZENADO E NÃO FAZER NA MÃO ESSE TEXTO

    # Preparando mensagem para enviar para usuário.
    message_email = user.get_full_name() + ",\n\n"
    message_email += "\tVocê está recebendo sua conta e senha para acessar o sistema do "
    message_email += "Projeto Final - Capstone."
    message_email += "\n\n"
    message_email += "\tO endereço do servidor é: "
    message_email += "<a href='https://pfe.insper.edu.br/'>https://pfe.insper.edu.br/</a>"
    message_email += "\n\n"

    message_email += "\tSua conta é: <b>" + user.username + "</b>\n"
    message_email += "\tSua senha é: <b>" + senha + "</b>\n"
    message_email += "\n"
    message_email += "\tQualquer dúvida, envie e-mail para: "
    message_email += coordenacao.user.get_full_name() + " <a href='mailto:" + coordenacao.user.email + "'>&lt;" + coordenacao.user.email + "&gt;</a>"
    message_email += "\n\n"
    message_email += "\t\tatenciosamente, coordenação do Capstone\n"
    message_email = message_email.replace('\n', "<br>\n")
    message_email = message_email.replace('\t', "&nbsp;&nbsp;&nbsp;&nbsp;\t")

    # Enviando e-mail com mensagem para usuário.
    subject = "Conta Capstone Insper: " + user.get_full_name()
    recipient_list = [user.email,]
    check = email(subject, recipient_list, message_email)
    if check != 1:
        mensagem = "Erro de conexão, contacte:lpsoares@insper.edu.br"
        codigo = 400
    else:
        mensagem = "<br><br>Enviado mensagem com senha para: "
        mensagem += user.get_full_name() + " " +\
                "&lt;" + user.email + "&gt;<br>\n"
        codigo = 200
    
    return mensagem, codigo


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def cadastrar_usuario(request):
    """Cadastra usuário na base de dados."""
    if request.method == "POST":

        if "email" in request.POST:

            usr_ja_existe = PFEUser.objects.filter(email=request.POST["email"])
            if usr_ja_existe:
                context = {
                    "voltar": True,
                    "usuario": usr_ja_existe.last(),
                    "area_principal": True,
                    "mensagem": "<h3 style='color:red'>Conflito: Usuário já cadastrada!</h3>",
                }

            else:
                mensagem, codigo, user = registro_usuario(request)

                if user is not None and "envia" in request.POST:
                    mensagem_email, codigo_email = envia_senha_mensagem(user)
                    mensagem += mensagem_email
                    if codigo_email != 200:
                        return HttpResponse(mensagem, status=codigo_email)

                if codigo != 200:
                    return HttpResponse(mensagem, status=codigo)

                context = {
                    "voltar": True,
                    "usuario": user,
                    "area_principal": True,
                    "mensagem": mensagem,
                }
        else:
            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.</h3>",
            }

        return render(request, "generic.html", context=context)

    context = {
        "organizacoes": Organizacao.objects.all().order_by(Lower("nome")),
        "cursos": Curso.objects.all().order_by("id"),
        "PFEUser": PFEUser,
        "Professor": Professor,
        "Parceiro": Parceiro,
        "Estudante": Aluno,
    }

    # Passado o tipo e nome da organização do parceiro (se o caso) a ser cadastrado
    tipo = request.GET.get("tipo", None)
    if tipo:
        if tipo == "parceiro":
            organizacao_str = request.GET.get("organizacao", None)
            if organizacao_str:
                try:
                    organizacao_id = int(organizacao_str)
                    organizacao_selecionada = Organizacao.objects.get(id=organizacao_id)
                except (ValueError, Organizacao.DoesNotExist):
                    return HttpResponseNotFound("<h1>Organização não encontrado!</h1>")
                context["organizacao_selecionada"] = organizacao_selecionada

        elif tipo == "professor":
            pass
        elif tipo == "estudante":
            pass
        else:
            return HttpResponseNotFound("<h1>Tipo não reconhecido!</h1>")
        context["tipo"] = tipo
    
    proposta_id = request.GET.get("proposta", None)
    if proposta_id:
        proposta = get_object_or_404(Proposta, id=proposta_id)
        mensagem = ""
        if proposta.contatos_tecnicos:
            mensagem += "<b>Contatos Técnicos apresentados na Propota: " + str(proposta.id) + "</b><br>"
            mensagem += proposta.contatos_tecnicos
            mensagem += "<br>"
        if proposta.contatos_administrativos:
            mensagem += "<b>Contatos Administrativos apresentados na Propota: " + str(proposta.id) + "</b><br>"
            mensagem += proposta.contatos_administrativos
            mensagem += "<br>"

        context["mensagem"] = mensagem

    return render(request, "administracao/cadastra_usuario.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def edita_usuario(request, primarykey):
    """Edita cadastro de usuário na base de dados."""
    user = get_object_or_404(PFEUser, id=primarykey)

    if request.method == "POST":

        if "email" in request.POST:
            mensagem, codigo, _ = registro_usuario(request, user)

            if user is not None and "envia" in request.POST:
                    mensagem_email, codigo_email = envia_senha_mensagem(user)
                    mensagem += mensagem_email
                    if codigo_email != 200:
                        return HttpResponse(mensagem, status=codigo_email)

            if codigo != 200:
                return HttpResponse(mensagem, status=codigo)

        else:
            mensagem = "<h3 style='color:red'>Falha na inserção na base da dados.<h3>"

        context = {
            "voltar": True,
            "cadastrar_usuario": True,
            "area_principal": True,
            "mensagem": mensagem,
        }

        return render(request, "generic.html", context=context)


    context = {
        "usuario": user,
        "organizacoes": Organizacao.objects.all().order_by(Lower("nome")),
        "cursos": Curso.objects.all().order_by("id"),
        "PFEUser": PFEUser,
        "Professor": Professor,
        "Parceiro": Parceiro,
        "Estudante": Aluno,
    }

    if user.tipo_de_usuario == 1:
        context["tipo"] = "estudante"
    elif user.tipo_de_usuario == 2:
        context["tipo"] = "professor"
    elif user.tipo_de_usuario == 3:
        context["tipo"] = "parceiro"
        if user.parceiro.organizacao:
            context["organizacao_selecionada"] = user.parceiro.organizacao
    else:
        return HttpResponse("Erro com tipo de usuário", status=401)

    return render(request, "administracao/cadastra_usuario.html", context)

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def carrega_arquivo(request, dado):
    """Faz o upload de arquivos CSV para o servidor."""
    if dado == "disciplinas":
        resource = DisciplinasResource()
    elif dado == "estudantes":
        resource = EstudantesResource()
    elif dado == "avaliacoes":
        resource = Avaliacoes2Resource()
    else:
        return HttpResponseNotFound("<h1>Tipo de dado não reconhecido!</h1>")

    # https://simpleisbetterthancomplex.com/packages/2016/08/11/django-import-export.html
    if request.method == "POST":

        dataset = tablib.Dataset()

        if "arquivo" in request.FILES:
            new_data = request.FILES["arquivo"].readlines()
            if ';' in str(new_data)[:32]:
                return HttpResponseNotFound("<h1>Arquivo de dados possui ponto e vírgula (;) !</h1>")
        else:
            return HttpResponseNotFound("<h1>Arquivo não reconhecido!</h1>")

        entradas = ""
        for i in new_data:
            texto = i.decode("utf-8")
            entradas += re.sub("[^A-Za-z0-9À-ÿ, \r\n@._]+", '', texto)  # Limpa caracteres especiais

        dataset.load(entradas, format="csv")
        dataset.insert_col(0, col=lambda row: None, header="id")

        result = resource.import_data(dataset, dry_run=True, raise_errors=True, before_import_kwargs={"dry_run": True})

        if result.has_errors():
            mensagem = "Erro ao carregar arquivo." + str(result)

            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }

            return render(request, "generic.html", context=context)

        resource.import_data(dataset, dry_run=False, collect_failed_rows=True, before_import_kwargs={"dry_run": False})  # importa os dados agora
        
        if hasattr(resource, "registros"):
            string_html = "<b>Importado ({0} registros novos): </b><br>".format(len(resource.registros["novos"]))
            for row_values in resource.registros["novos"]:
                string_html += str(row_values) + "<br>"
            string_html += "<br><br><b>Atualizando ({0} registros): </b><br>".format(len(resource.registros["atualizados"]))
            for row_values in resource.registros["atualizados"]:
                string_html += str(row_values) + "<br>"
        else:
            string_html = "Importado ({0} registros): <br>".format(len(dataset))
            for row_values in dataset:
                string_html += str(row_values) + "<br>"

        context = {
            "area_principal": True,
            "mensagem": string_html,
        }

        return render(request, "generic.html", context=context)

    context = {
        "campos_permitidos": resource.campos,
    }

    return render(request, "administracao/import.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def configurar(request):
    """Definir datas."""
    configuracao = get_object_or_404(Configuracao)

    if request.method == "POST":

        if "periodo_ano" and "periodo_semestre" in request.POST:
            try:
                
                configuracao.ano = int(request.POST["periodo_ano"])
                configuracao.semestre = int(request.POST["periodo_semestre"])

                configuracao.prazo_avaliar = int(request.POST["prazo_avaliar"])
                configuracao.prazo_preencher_banca = int(request.POST["prazo_preencher_banca"])

                configuracao.coordenacao = get_object_or_404(Administrador,
                                                             pk=int(request.POST["coordenacao"]))

                #configuracao.coordenador = request.POST["coordenador"]
                configuracao.coordenacao.nome_para_certificados = request.POST["nome_para_certificados"]
                if "assinatura" in request.FILES:
                    assinatura = simple_upload(request.FILES["assinatura"],
                                                path=get_upload_path(configuracao, ""))
                    configuracao.coordenacao.assinatura = assinatura[len(settings.MEDIA_URL):]

                configuracao.coordenacao.save()
                configuracao.save()
                context = {
                    "area_principal": True,
                    "mensagem": "Dados atualizados.",
                }
                return render(request, "generic.html", context=context)
            except (ValueError, OverflowError, MultiValueDictKeyError):
                return HttpResponse("Algum erro não identificado.", status=401)
        else:
            return HttpResponse("Algum erro ao passar parâmetros.", status=401)
    
    context = {
        "configuracao": configuracao,
        "administradores": Administrador.objects.all(),
        "administrador": Administrador,
    }

    return render(request, "administracao/configurar.html", context)


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def desbloquear_usuarios(request):
    """Desbloqueia todos os usuários."""
    if request.user.tipo_de_usuario == 4:
        axes.utils.reset()
        return redirect("/administracao/bloqueados/")
    return HttpResponse("Você não tem privilégios")


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def exportar(request, modo):
    """Exporta dados."""
    context = {"modo": modo,}
    return render(request, "administracao/exportar.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def propor(request):
    """Monta grupos."""

    if request.is_ajax():
        otimizar = True

        configuracao = get_object_or_404(Configuracao)
        ano = configuracao.ano
        semestre = configuracao.semestre
        ano, semestre = adianta_semestre(ano, semestre)

        lista_propostas = list(zip(*ordena_propostas(otimizar, ano, semestre)))
        if lista_propostas:
            propostas = lista_propostas[0]
        else:
            propostas = []

        alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
            filter(anoPFE=ano, semestrePFE=semestre, trancado=False).\
            order_by(Lower("user__first_name"), Lower("user__last_name"))
        
        # Calcula média dos CRs
        media_cr = 0
        for aluno in alunos:
            media_cr += aluno.cr
        media_cr /= len(alunos)

        # checa para empresas repetidas, para colocar um número para cada uma
        repetidas = {}
        for proposta in propostas:
            if proposta.organizacao:
                if proposta.organizacao.sigla in repetidas:
                    repetidas[proposta.organizacao.sigla] += 1
                else:
                    repetidas[proposta.organizacao.sigla] = 0
            else:
                if proposta.nome_organizacao in repetidas:
                    repetidas[proposta.nome_organizacao] += 1
                else:
                    repetidas[proposta.nome_organizacao] = 0
        repetidas_limpa = {}
        for repetida in repetidas:
            if repetidas[repetida] != 0:  # tira zerados
                repetidas_limpa[repetida] = repetidas[repetida]
        proposta_indice = {}
        for proposta in reversed(propostas):
            if proposta.organizacao:
                if proposta.organizacao.sigla in repetidas_limpa:
                    proposta_indice[proposta.id] = \
                        repetidas_limpa[proposta.organizacao.sigla] + 1
                    repetidas_limpa[proposta.organizacao.sigla] -= 1
            else:
                if proposta.nome_organizacao in repetidas_limpa:
                    proposta_indice[proposta.id] = \
                        repetidas_limpa[proposta.nome_organizacao] + 1
                    repetidas_limpa[proposta.nome_organizacao] -= 1

        def pega_opcoes(alunos, propostas):
            opcoes = []
            for aluno in alunos:
                opcoes_aluno = []
                for proposta in propostas:
                    opcao = Opcao.objects.filter(aluno=aluno, proposta=proposta).last()
                    if opcao:
                        opcoes_aluno.append(opcao)
                    else:
                        opcoes_aluno.append(None)
                opcoes.append(opcoes_aluno)
            return opcoes

        opcoes = pega_opcoes(alunos, propostas)

        def calcula_qtd(opcoes, propostas, alunos):
            finish = True
            qtd = []
            for count, proposta in enumerate(propostas):
                tmp = 0
                for linha in range(len(alunos)):
                    pre = alunos[linha].pre_alocacao
                    if pre:
                        if pre == proposta:
                            tmp += 1
                    else:
                        optmp = Opcao.objects.filter(aluno=alunos[linha], prioridade=1).last()
                        if optmp and optmp.proposta == proposta:
                            tmp += 1
                # Somente grupos de 3 ou 4 ou proposta sem ninguem
                if tmp != 4 or tmp != 3 or tmp != 0:
                    finish = False
                qtd.append(tmp)
            return qtd, finish

        qtd, finish = calcula_qtd(opcoes, propostas, alunos)

        user = request.user
        if otimizar:  # Quer dizer que é um POST
            if user.tipo_de_usuario != 4:  # admin
                return HttpResponse("Usuário sem privilégios de administrador.", status=403)

            ordem_propostas = {}
            contador = 0
            for proposta in propostas:
                ordem_propostas[proposta.id] = contador
                contador += 1

            # Removendo propostas com menos de 3 estudantes (prioridade <= 5)
            soma = []
            for count, proposta in enumerate(propostas):
                tmp = 0
                for linha in range(len(alunos)):
                    opcao = opcoes[linha][count] 
                    if opcao and opcao.prioridade <= 5:
                        tmp += 1
                soma.append(tmp)
            idx = None
            for count, proposta in enumerate(propostas):
                if soma[count] < 3:
                    idx = count
                    break
            propostas = propostas[:idx]
            for linha in range(len(alunos)):
                opcoes[linha] = opcoes[linha][:idx] 
            soma = soma[:idx]
        
            # Se estudante foi e voltou em um grupo, não mudar mais
            pula_estudante = {}

            # Pre alocando todos nas suas primeiras opções
            for aluno in alunos:
                tmp_prioridade = 9999
                tmp_proposta = None
                for proposta in propostas:
                    opcao = Opcao.objects.filter(aluno=aluno, proposta=proposta).last()
                    if opcao and opcao.prioridade < tmp_prioridade:
                        tmp_proposta = proposta
                        tmp_prioridade = opcao.prioridade
                if tmp_prioridade < 9999:
                    aluno.pre_alocacao = tmp_proposta
                    aluno.save()
                else:
                    pula_estudante[aluno]=0  # Todas as opções de {aluno} são inviáveis.

            reduz = 1
            contador = 0
            while not finish:
                
                trocou = False

                for count, proposta in enumerate(propostas):
                    if qtd[count] == reduz:
                        troca = None
                        for linha in range(len(alunos)):
                            opcao = opcoes[linha][count]
                            if opcao and (opcao.prioridade <= 10) and (opcao.aluno.pre_alocacao != proposta):
                                op_qtd = qtd[ordem_propostas[opcao.aluno.pre_alocacao.id]]
                                if (opcao.aluno not in pula_estudante) or (opcao.prioridade < pula_estudante[opcao.aluno]):
                                    if (3 > op_qtd) or (4 < op_qtd):
                                        if (not troca):
                                            troca = opcao
                                        elif (opcao.prioridade < troca.prioridade):
                                            troca = opcao
                                        elif (opcao.prioridade == troca.prioridade) and (opcao.aluno.cr < troca.aluno.cr):
                                            troca = opcao
                        if troca:
                            trocou = True
                            aluno = Aluno.objects.get(pk=troca.aluno.pk)
                            antiga_opcao = Opcao.objects.filter(aluno=aluno, proposta=aluno.pre_alocacao).last()
                            if troca.prioridade < antiga_opcao.prioridade:
                                pula_estudante[aluno]=troca.prioridade
                            Aluno.objects.filter(pk=troca.aluno.pk).update(pre_alocacao=troca.proposta)
                            reduz = 1 # Volta a busca do começo sempre que há alguma troca
                            break

                alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
                    filter(anoPFE=ano).\
                    filter(semestrePFE=semestre).\
                    filter(trancado=False).\
                    order_by(Lower("user__first_name"), Lower("user__last_name"))

                opcoes = pega_opcoes(alunos, propostas)
                qtd, finish = calcula_qtd(opcoes, propostas, alunos)

                if not trocou:
                    reduz += 1
                    if reduz == 4:
                        break

                # Para evitar travar totalmente
                contador += 1
                if contador > 50:
                    #"ESTOUROU"
                    break

        data = {
            "atualizado": True,
        }
        return JsonResponse(data)

    return HttpResponseNotFound("Requisição errada")



@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def montar_grupos(request):
    """Montar grupos para projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    ano, semestre = adianta_semestre(ano, semestre)

    propostas = Proposta.objects.filter(ano=ano, semestre=semestre, disponivel=True)

    estudantes = Aluno.objects.filter(trancado=False).\
        filter(anoPFE=ano, semestrePFE=semestre).\
        order_by(Lower("user__first_name"), Lower("user__last_name"))

    opcoes = []
    for estudante in estudantes:
        opcao = Opcao.objects.filter(aluno=estudante).\
                              filter(proposta__ano=ano, proposta__semestre=semestre).\
                              order_by("prioridade")
        opcoes.append(opcao)

        # Caso haja um pré-alocação de anos anteriores, limpar a pré-alocação
        if estudante.pre_alocacao and estudante.pre_alocacao not in propostas:
            estudante.pre_alocacao = None

    estudantes_opcoes = zip(estudantes, opcoes)

    # Checa se usuário é administrador ou professor
    user = request.user

    mensagem = ""

    if request.method == "POST" and user and request.user.tipo_de_usuario == 4:  # admin

        if "limpar" in request.POST:
            for estudante in estudantes:
                estudante.pre_alocacao = None
                estudante.save()

        if "fechar" in request.POST:
            for proposta in propostas:
                alocados = []
                for estudante in estudantes:
                    if estudante.pre_alocacao:
                        if estudante.pre_alocacao.id == proposta.id:
                            alocados.append(estudante)
                    else:
                        op_aloc = Opcao.objects.filter(aluno=estudante).\
                                    filter(proposta__ano=ano, proposta__semestre=semestre).\
                                    filter(prioridade=1).first()
                        if op_aloc and op_aloc.proposta == proposta:
                            alocados.append(estudante)
                if alocados:  # pelo menos um estudante no projeto
                    try:
                        projeto = Projeto.objects.get(proposta=proposta, avancado=None)
                    except Projeto.DoesNotExist:
                        projeto = Projeto.create(proposta)

                    if not projeto.organizacao:
                        projeto.organizacao = proposta.organizacao

                    projeto.ano = proposta.ano
                    projeto.semestre = proposta.semestre

                    projeto.save()

                    alocacoes = Alocacao.objects.filter(projeto=projeto)
                    for alocacao in alocacoes:  # Apaga todas alocacoes que não tiverem nota
                        avals = list(Avaliacao2.objects.filter(alocacao=alocacao))
                        if not avals:
                            alocacao.delete()
                        else:
                            mensagem += "- "+str(alocacao.aluno)+"\n"

                    for alocado in alocados:  # alocando estudantes no projeto
                        alocacao = Alocacao.create(alocado, projeto)
                        alocacao.save()

                else:
                    projetos = Projeto.objects.filter(proposta=proposta, avancado=None)
                    if not projetos:
                        continue

                    for projeto in projetos:
                        alocacoes = Alocacao.objects.filter(projeto=projeto)
                        for alocacao in alocacoes:  # Apaga todas alocacoes que não tiverem nota
                            alocacao.delete()

                        projeto.delete()

            if mensagem:
                request.session["mensagem"] = "Estudantes possuiam alocações com notas:\n" + mensagem

            return redirect("/administracao/selecionar_orientadores/")

    if user and user.tipo_de_usuario != 4:  # admin
        mensagem = "Sua conta não é de administrador, "
        mensagem += "você pode mexer na tela, contudo suas modificações não serão salvas."

    context = {
        "mensagem": mensagem,
        "configuracao": configuracao,
        "propostas": propostas,
        "estudantes_opcoes": estudantes_opcoes,
        "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"), 
    }

    return render(request, "administracao/montar_grupos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def selecionar_orientadores(request):
    """Selecionar Orientadores para os Projetos."""

    mensagem = request.session["mensagem"] if "mensagem" in request.session else ""
    if request.user.tipo_de_usuario != 4:  # Checa se usuário é administrador
        mensagem += "Sua conta não é de administrador, você pode mexer na tela, contudo suas modificações não serão salvas."

    ano, semestre = adianta_semestre_conf(get_object_or_404(Configuracao))

    context = {
        "mensagem": mensagem,
        "projetos": Projeto.objects.filter(ano=ano, semestre=semestre),
        "orientadores": PFEUser.objects.filter(tipo_de_usuario__in=[2, 4])  #2prof 4adm,
    }

    return render(request, "administracao/selecionar_orientadores.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def fechar_conexoes(request):
    """Fechar conexões com Organizações."""
    
    mensagem = request.session["mensagem"] if "mensagem" in request.session else ""
    if request.user.tipo_de_usuario != 4:  # Checa se usuário é administrador
        mensagem += "Sua conta não é de administrador, você pode mexer na tela, contudo suas modificações não serão salvas."

    ano, semestre = adianta_semestre_conf(get_object_or_404(Configuracao))

    context = {
        "mensagem": mensagem,
        "projetos": Projeto.objects.filter(ano=ano, semestre=semestre),
    }

    return render(request, "administracao/fechar_conexoes.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def servico(request):
    """Caso servidor esteja em manutenção."""
    if request.method == "POST":
        check_values = request.POST.getlist("selection")
        settings.MAINTENANCE_MODE = 1 if "manutencao" in check_values else 0
        return redirect("/administracao")
    context = {"manutencao": settings.MAINTENANCE_MODE, }
    return render(request, "administracao/servico.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def pre_alocar_estudante(request):
    """Ajax para pre-alocar estudates em propostas."""
    if request.user.tipo_de_usuario == 4:  # admin

        estudante = request.GET.get("estudante", None)
        estudante_id = int(estudante[len("estudante"):])
        estudante = get_object_or_404(Aluno, id=estudante_id)

        proposta = request.GET.get("proposta", None)
        proposta_id = int(proposta[len("proposta"):])
        proposta = get_object_or_404(Proposta, id=proposta_id)

        estudante.pre_alocacao = proposta
        estudante.save()

    elif request.user.tipo_de_usuario == 2:  # professor
        # atualizações não serão salvas
        pass

    else:
        return HttpResponseNotFound("<h1>Usuário sem privilérios!</h1>")

    return JsonResponse({"atualizado": False,})


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def definir_orientador(request):
    """Ajax para definir orientadores de projetos."""
    
    if request.user.tipo_de_usuario == 4:  # admin
        # Código só se usuário é administrador

        orientador_get = request.POST.get("orientador", None)
        orientador_id = int(orientador_get[len("orientador"):]) if orientador_get else None
        orientador = get_object_or_404(Professor, user_id=orientador_id) if orientador_id else None

        projeto_get = request.POST.get("projeto", None)        
        projeto_id = int(projeto_get[len("projeto"):]) if projeto_get else None
        projeto = get_object_or_404(Projeto, id=projeto_id)

        projeto.orientador = orientador
        projeto.save()

    elif request.user.tipo_de_usuario == 2:  # professor
        pass

    else:
        return HttpResponseNotFound("<h1>Usuário sem privilérios!</h1>")

    return JsonResponse({"atualizado": True,})


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def excluir_disciplina(request):
    """Remove Disciplina Recomendada."""
    
    if request.is_ajax() and "disciplina_id" in request.POST:
        disciplina_id = int(request.POST["disciplina_id"])
        instance = Disciplina.objects.get(id=disciplina_id)
        instance.delete()

        return JsonResponse({"atualizado": True})

    return HttpResponseNotFound("Requisição errada")


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def export(request, modelo, formato):
    """Exporta dados direto para o navegador nos formatos CSV, XLS e JSON."""
    if modelo == "projetos":
        resource = ProjetosResource()
    elif modelo == "organizacoes":
        resource = OrganizacoesResource()
    elif modelo == "opcoes":
        resource = OpcoesResource()
    elif modelo == "avaliacoes":
        resource = Avaliacoes2Resource()
    elif modelo == "usuarios":
        resource = UsuariosResource()
    elif modelo == "estudantes":
        resource = EstudantesResource()
    elif modelo == "professores":
        resource = ProfessoresResource()
    elif modelo == "parceiros":
        resource = ParceirosResource()
    elif modelo == "configuracao":
        resource = ConfiguracaoResource()
    elif modelo == "feedbacks":
        resource = FeedbacksResource()
    # elif modelo == "comite":
    #     resource = ComiteResource()
    else:
        mensagem = "Chamada irregular: Base de dados desconhecida = " + modelo
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    dataset = resource.export()

    databook = tablib.Databook()

    databook.add_sheet(dataset)

    if formato in ("xls", "xlsx"):
        response = HttpResponse(databook.xlsx, content_type="application/ms-excel")
        formato = "xlsx"
    elif formato == "json":
        response = HttpResponse(dataset.json, content_type="application/json")
    elif formato == "csv":
        response = HttpResponse(dataset.csv, content_type="text/csv")
    else:
        mensagem = "Chamada irregular : Formato desconhecido = " + formato
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    response["Content-Disposition"] = 'attachment; filename="'+modelo+'.'+formato+'"'

    return response


def create_backup():
    """Rotina para criar um backup."""
    databook = tablib.Databook()

    data_projetos = ProjetosResource().export()
    data_projetos.title = "Projetos"
    databook.add_sheet(data_projetos)

    data_organizacoes = OrganizacoesResource().export()
    data_organizacoes.title = "Organizacoes"
    databook.add_sheet(data_organizacoes)

    data_opcoes = OpcoesResource().export()
    data_opcoes.title = "Opcoes"
    databook.add_sheet(data_opcoes)

    data_avaliacoes = Avaliacoes2Resource().export()
    data_avaliacoes.title = "Avaliações"
    databook.add_sheet(data_avaliacoes)

    data_usuarios = UsuariosResource().export()
    data_usuarios.title = "Usuarios"
    databook.add_sheet(data_usuarios)

    data_alunos = EstudantesResource().export()
    data_alunos.title = "Alunos"
    databook.add_sheet(data_alunos)

    data_professores = ProfessoresResource().export()
    data_professores.title = "Professores"
    databook.add_sheet(data_professores)

    data_configuracao = ConfiguracaoResource().export()
    data_configuracao.title = "Configuracao"
    databook.add_sheet(data_configuracao)

    return databook


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def backup(request, formato):
    """Gera um backup de tudo."""
    databook = create_backup()
    if formato in ("xls", "xlsx"):
        response = HttpResponse(databook.xlsx, content_type="application/ms-excel")
        formato = "xlsx"
    elif formato == "json":
        response = HttpResponse(databook.json, content_type="application/json")
    else:
        mensagem = "Chamada irregular : Formato desconhecido = " + formato
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    response["Content-Disposition"] = 'attachment; filename="backup.'+formato+'"'

    return response


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def relatorio(request, modelo, formato):
    """Gera relatorios em html e PDF."""
    configuracao = get_object_or_404(Configuracao)
    context = {"configuracao": configuracao}

    if modelo == "propostas":
        context["propostas"] = Proposta.objects.all()
        arquivo = "administracao/relatorio_propostas.html"

    elif modelo == "projetos":
        context["projetos"] = Projeto.objects.all()
        arquivo = "administracao/relatorio_projetos.html"

    elif modelo == "estudantes" or modelo == "alunos":
        context["alunos"] = Aluno.objects.all().filter(anoPFE=configuracao.ano,
                                                       semestrePFE=configuracao.semestre)
        arquivo = "administracao/relatorio_alunos.html"

    elif modelo == "feedbacks":
        context["feedbacks"] = Feedback.objects.all()
        arquivo = "administracao/relatorio_feedbacks.html"

    else:
        context = {
            "area_principal": True,
            "mensagem": "Chamada irregular: Base de dados desconhecida = " + modelo,
        }
        return render(request, "generic.html", context=context)

    if formato in ("html", "HTML"):
        return render(request, arquivo, context)

    if formato in ("pdf", "PDF"):
        pdf = render_to_pdf(arquivo, context)
        return HttpResponse(pdf.getvalue(), content_type="application/pdf")

    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def dados_backup(request, modo):
    """Envia e-mails de backup de segurança."""
    
    if request.method == "POST" and "email" in request.POST and "sigla" in request.POST:

        subject = "RELATÓRIOS"
        message = "Relatórios"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [request.POST["email"],]
        mail = EmailMessage(subject, message, email_from, recipient_list)
        
        if modo == "relatorios":
            configuracao = get_object_or_404(Configuracao)
            context = {
                "projetos": Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre),
                "alunos": Aluno.objects.filter(anoPFE=configuracao.ano, semestrePFE=configuracao.semestre),
                "configuracao": configuracao,
            }
            pdf_proj = render_to_pdf("administracao/relatorio_projetos.html", context)
            pdf_alun = render_to_pdf("administracao/relatorio_alunos.html", context)
            mail.attach("projetos.pdf", pdf_proj.getvalue(), "application/pdf")
            mail.attach("alunos.pdf", pdf_alun.getvalue(), "application/pdf")

        elif modo=="dados":
            databook = create_backup()
            mail.attach("backup.xlsx", databook.xlsx, "application/ms-excel")
            mail.attach("backup.json", databook.json, "application/json")
            
        mail.send()
        
        context = {
            "area_principal": True,
            "mensagem": "E-mail enviado.",
        }

        return render(request, "generic.html", context=context)
    
    else:
        raise SuspiciousOperation(f"Chamada irregular.")


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def logs(request, dias=30):
    """Alguns logs de Admin."""
    usuario_sem_acesso(request, (4,)) # Soh Adm

    thirty_days_ago = timezone.now() - datetime.timedelta(days=dias)
    message = "As seguintes alterações foram realizadas pela interface de administrador:<br>"
    message += "(mostrando os últimos " + str(dias) + " dias)<br><br>"
    #for log in LogEntry.objects.all():
    for log in LogEntry.objects.filter(action_time__gte=thirty_days_ago):
        message += "&bull; " + str(log.user) + " [" + str(log.action_time) + "]: " + str(log)+"<br>\n"

    message += "<br><a href=' " + str(dias+30) + "'>Mostrar último " + str(dias+30) + " dias</a>"
    
    return HttpResponse(message)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def conexoes_estabelecidas(request):
    """Mostra usuários conectados."""
    usuario_sem_acesso(request, (4,)) # Soh Adm
    
    mensagem = ""
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    usuarios = []
    for session in sessions:
        data = session.get_decoded()
        user_id = data.get("_auth_user_id", None)
        try:
            user = PFEUser.objects.get(id=user_id)
            usuario = {}
            usuario["usuario"] = user
            usuario["autenticado"] = user.is_authenticated
            usuario["desde"] = user.last_login
            usuario["permissoes"] = str(user.get_all_permissions())[:120]
            usuarios.append(usuario)
        except PFEUser.DoesNotExist:
            mensagem += "User ID não identificado = " + str(user_id) + "<br>\n"
            # mensagem += "; Data = " + str(data) + "<br>\n"

    context = {
        "mensagem": mensagem,
        "usuarios": usuarios,
    }

    return render(request, "administracao/conexoes_estabelecidas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bloqueados(request):
    """Mostra usuários e ips bloqueados."""
    if request.user.tipo_de_usuario != 4:
        return HttpResponse("Você não tem privilégios")

    mes_atras = timezone.now() - datetime.timedelta(days=30)
    
    context = {
        "access_logs": AccessLog.objects.all().filter(attempt_time__gte=mes_atras),
        "access_attempts": AccessAttempt.objects.all(),
    }
    return render(request, "administracao/bloqueados.html", context=context)
