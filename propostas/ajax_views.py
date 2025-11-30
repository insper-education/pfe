#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 30 de Novembro de 2025
"""

import logging

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import PerguntasRespostas
#from projetos.models import Projeto, Area
from projetos.models import Proposta, Configuracao,  Recomendada, Organizacao, Disciplina
from projetos.messages import email

#from users.models import Opcao, Aluno, Alocacao
from users.models import PFEUser
from operacional.models import Curso

logger = logging.getLogger("django")


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def atualiza_proposta(request, primarykey=None):
    """Atualiza uma proposta (AJAX)."""

    if primarykey is None:
        return HttpResponse("Erro não identificado.", status=401)
    
    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":  # Ajax check
        return HttpResponse("Erro não identificado.", status=401)

    proposta = get_object_or_404(Proposta, pk=primarykey)

    # Troca Conformidade de Proposta
    for dict in request.POST:
        if dict[0:5] == "dict[":
            tmp = request.POST[dict] == "true"
            setattr(proposta, dict[5:-1], tmp)

    # Define analisador
    if "autorizador" in request.POST:
        try:
            if request.POST["autorizador"] == "0":
                proposta.autorizado = None
            else:
                proposta.autorizado = PFEUser.objects.get(pk=request.POST["autorizador"])
        except PFEUser.DoesNotExist:
            return HttpResponse("Analisador não encontrado.", status=401)
    
    # Disponibiliza proposta
    if "disponibilizar" in request.POST:
        proposta.disponivel = request.POST["disponibilizar"] == "sim"

    # Anotações internas
    if "anotacoes" in request.POST:
        proposta.anotacoes = request.POST["anotacoes"]

    proposta.save()
    return JsonResponse({"atualizado": True})


@login_required
@transaction.atomic
def proposta_pergunta(request, primarykey=None):
    """Cria uma pergunta sobre uma proposta (AJAX)."""

    if primarykey is None:
        return HttpResponse("Erro não identificado.", status=401)
    
    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":  # Ajax check
        return HttpResponse("Erro não identificado.", status=401)

    proposta = get_object_or_404(Proposta, pk=primarykey)
    
    if "pergunta" in request.POST:
        pergunta_resposta = PerguntasRespostas(
            proposta=proposta,
            pergunta=request.POST["pergunta"],
            quem_perguntou=request.user,
        )
        pergunta_resposta.save()

        # Enviando e-mail com mensagem para usuários.
        mensagem = (
            f"O estudante: <b>{request.user.get_full_name()}</b>, fez uma pergunta sobre a proposta: <b>{proposta.titulo}</b>."
        )
        mensagem += f"\n\n<br><br>Pergunta: <i>{pergunta_resposta.pergunta}</i>"
        mensagem += (
            f"\n\n<br><br>Link para a proposta: {request.scheme}://{request.get_host()}/propostas/proposta_completa/{proposta.id}"
        )
        subject = "Capstone | Pergunta sobre proposta de projeto"
        configuracao = get_object_or_404(Configuracao)
        recipient_list = [str(configuracao.coordenacao.user.email)]
        if proposta.autorizado:
            recipient_list.append(str(proposta.autorizado.email))

        email(subject, recipient_list, mensagem)
        data = {
            "atualizado": True,
            "data_hora": pergunta_resposta.data_pergunta.strftime("%d/%m/%Y %H:%M"),
        }
        return JsonResponse(data)

    return HttpResponse("Pergunta não informada.", status=401)


@login_required
@transaction.atomic
def proposta_resposta(request, primarykey=None):
    """Responde uma pergunta sobre uma proposta (AJAX)."""

    if primarykey is None:
        return HttpResponse("Erro não identificado.", status=401)

    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":  # Ajax check
        return HttpResponse("Erro não identificado.", status=401)

    proposta = get_object_or_404(Proposta, pk=primarykey)
    
    if "pergunta_id" in request.POST and "resposta" in request.POST:
        pergunta_resposta = get_object_or_404(PerguntasRespostas, pk=request.POST["pergunta_id"])
        pergunta_resposta.resposta = request.POST["resposta"]
        pergunta_resposta.quem_respondeu = request.user

        if "em_nome" in request.POST and request.POST["em_nome"]:
            pergunta_resposta.em_nome_de = PFEUser.objects.get(pk=int(request.POST["em_nome"]))
        else:
            pergunta_resposta.em_nome_de = None

        pergunta_resposta.data_resposta = timezone.now()
        pergunta_resposta.save()

        # Enviando e-mail com mensagem para usuários.
        mensagem = f"Sua pergunta sobre a proposta <b>[{proposta.organizacao.sigla}] {proposta.titulo}</b> foi respondida."
        mensagem += f"\n\n<br><br>Pergunta: <i>{pergunta_resposta.pergunta}</i>"
        mensagem += f"\n\n<br><br>Resposta: <i>{pergunta_resposta.resposta}</i>"
        mensagem += f"\n\n<br><br>Link para a proposta: {request.scheme}://{request.get_host()}/propostas/proposta_detalhes/{proposta.id}"
        subject = "Capstone | Pergunta sobre proposta de projeto"
        configuracao = get_object_or_404(Configuracao)
        recipient_list = [
            str(pergunta_resposta.quem_perguntou.email),
            str(configuracao.coordenacao.user.email),
        ]

        email(subject, recipient_list, mensagem)
        return JsonResponse({"atualizado": True})

    return HttpResponse("Parâmetros incompletos.", status=401)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def validate_alunos(request):
    """Ajax para validar vaga de estudantes em propostas."""
    try:
        proposta_id = int(request.GET.get("proposta"))
        vaga = request.GET.get("vaga", " - ").split('-')
        checked = request.GET.get("checked") == "true"
        proposta = Proposta.objects.select_for_update().get(id=proposta_id)
        curso = Curso.objects.get(sigla_curta=vaga[0])
        perfil_num = vaga[1]
        if perfil_num in {'1', '2', '3', '4'}:
            perfil_attr = f'perfil{perfil_num}'
            perfil = getattr(proposta, perfil_attr)
            if checked:
                perfil.add(curso)
            else:
                perfil.remove(curso)
            proposta.save()
            return JsonResponse({"atualizado": True})
        else:
            return HttpResponse("Perfil inválido.", status=400)
    except (Proposta.DoesNotExist, Curso.DoesNotExist, ValueError, TypeError):
        return HttpResponseNotFound("Erro ao validar vaga.")


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def link_organizacao(request, proposta_id):
    """Cria um anotação para uma organização parceira (AJAX)."""
    proposta = get_object_or_404(Proposta, id=proposta_id)

    if request.method == "POST" and "organizacao_id" in request.POST:

        organizacao = get_object_or_404(Organizacao, id=request.POST["organizacao_id"])

        proposta.organizacao = organizacao

        proposta.save()

        data = {
            "organizacao": str(organizacao),
            "organizacao_id": organizacao.id,
            "organizacao_sigla": organizacao.sigla,
            "organizacao_endereco": organizacao.endereco,
            "organizacao_logotipo_url": (organizacao.logotipo.url if organizacao.logotipo else None),
            "organizacao_website": organizacao.website,
            "proposta": proposta_id,
            "atualizado": True,
        }

        return JsonResponse(data)

    context = {
        "organizacoes": Organizacao.objects.all().order_by(Lower("sigla")),
        "proposta": proposta,
        "url": request.get_full_path(),
    }
    return render(request, "propostas/organizacao_view.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def link_disciplina(request, proposta_id):
    """Adicionar Disciplina Recomendada (AJAX)."""
    proposta = get_object_or_404(Proposta, id=proposta_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" and request.method == "POST":  # Ajax check

        if "disciplina_id" not in request.POST:
            return HttpResponse("Algum erro ao passar parâmetros.", status=401)

        disciplina_id = int(request.POST["disciplina_id"])
        disciplina = get_object_or_404(Disciplina, id=disciplina_id)

        ja_existe = Recomendada.objects.filter(proposta=proposta, disciplina=disciplina)

        if ja_existe:
            return HttpResponseNotFound("Já existe")

        recomendada = Recomendada()
        recomendada.proposta = proposta
        recomendada.disciplina = disciplina
        recomendada.save()

        data = {
            "disciplina": str(disciplina),
            "disciplina_id": disciplina.id,
            "proposta_id": proposta_id,
            "atualizado": True,
        }

        return JsonResponse(data)

    context = {
        "disciplinas": Disciplina.objects.all().order_by("nome"),
        "proposta": proposta,
        "url": request.get_full_path(),
    }
 
    return render(request, "propostas/disciplina_view.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def remover_disciplina(request):
    """Remove Disciplina Recomendada (AJAX)."""
    if request.headers.get("X-Requested-With") != "XMLHttpRequest" or request.method != "POST":  # Ajax check
        return HttpResponse("Erro não identificado.", status=401)
    if "disciplina_id" not in request.POST or "proposta_id" not in request.POST:
        return HttpResponse("Algum erro ao passar parâmetros.", status=401)

    try:
        proposta_id = int(request.POST["proposta_id"])
        disciplina_id = int(request.POST["disciplina_id"])
    except Exception:
        return HttpResponse("Erro ao recuperar proposta e disciplinas.", status=401)

    instances = Recomendada.objects.filter(proposta__id=proposta_id, disciplina__id=disciplina_id)
    for instance in instances:
        instance.delete()

    return JsonResponse({"atualizado": True})
