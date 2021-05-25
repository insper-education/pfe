"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from projetos.models import Projeto, Proposta, Configuracao, Area, AreaDeInteresse
from projetos.models import Encontro, Banca, Entidade

from projetos.support import cria_area_estudante

from projetos.messages import email, message_agendamento, create_message

from users.models import PFEUser, Aluno, Professor, Alocacao, Opcao, OpcaoTemporaria

from users.support import configuracao_estudante_vencida, adianta_semestre


@login_required
def index_estudantes(request):
    """Mostra página principal do usuário estudante."""
    usuario = get_object_or_404(PFEUser, pk=request.user.pk)
    configuracao = get_object_or_404(Configuracao)

    context = {
        'configuracao': configuracao,
        'vencido': timezone.now() > configuracao.prazo
    }

    ano = configuracao.ano
    semestre = configuracao.semestre

    # Caso estudante
    if usuario.tipo_de_usuario == 1:
        estudante = get_object_or_404(Aluno, pk=request.user.aluno.pk)
        # try:
        #     estudante = Aluno.objects.get(pk=request.user.aluno.pk)
        # except Aluno.DoesNotExist:
        #     return HttpResponse("Estudante não encontrado.", status=401)

        context['projeto'] = Projeto.objects\
            .filter(alocacao__aluno=estudante).last()

        # Estudantes de processos passados sempre terrão seleção vencida
        if semestre == 1:
            context['vencido'] |= estudante.anoPFE < ano
            context['vencido'] |= estudante.anoPFE == ano and \
                estudante.semestrePFE == 1
        else:
            context['vencido'] |= (estudante.anoPFE <= ano)

    # Caso professor ou administrador
    elif usuario.tipo_de_usuario == 2 or usuario.tipo_de_usuario == 4:
        context['professor_id'] = get_object_or_404(Professor, pk=request.user.professor.pk).id
        # try:
        #     context['professor_id'] = \
        #         Professor.objects.get(pk=request.user.professor.pk).id
        # except Professor.DoesNotExist:
        #     return HttpResponse("Professor não encontrado.", status=401)

    # Caso parceiro
    else:
        return HttpResponse("Usuário sem acesso.", status=401)

    context['ano'], context['semestre'] = adianta_semestre(ano, semestre)

    return render(request, 'estudantes/index_estudantes.html', context=context)


@login_required
def areas_interesse(request):
    """Para estudantes definirem suas áreas de interesse."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)

    areas = Area.objects.filter(ativa=True)
    context = {
        'areast': areas,
    }

    # Caso seja estudante
    if user.tipo_de_usuario == 1:  # Estudante
        estudante = get_object_or_404(Aluno, pk=request.user.aluno.pk)
        vencido = configuracao_estudante_vencida(estudante)

        if (not vencido) and request.method == 'POST':
            cria_area_estudante(request, estudante)
            return render(request, 'users/atualizado.html',)

        context['vencido'] = vencido
        context['estudante'] = estudante

    # caso Professores ou Administrador
    elif user.tipo_de_usuario == 2 or user.tipo_de_usuario == 4:
        context['mensagem'] = "Você não está cadastrado como estudante."
        context['vencido'] = True

    # caso não seja Estudante, Professor ou Administrador (ou seja Parceiro)
    else:
        mensagem = "Você não está cadastrado como estudante!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    return render(request, 'estudantes/areas_interesse.html', context=context)


@login_required
@transaction.atomic
def encontros_marcar(request):
    """Encontros a serem agendados pelos alunos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    hoje = datetime.date.today()
    encontros = Encontro.objects.filter(startDate__gt=hoje)\
        .order_by('startDate')

    usuario = get_object_or_404(PFEUser, pk=request.user.pk)

    if usuario.tipo_de_usuario == 1:  # Estudante
        estudante = get_object_or_404(Aluno, pk=request.user.aluno.pk)
        # try:
        #     estudante = Aluno.objects.get(pk=request.user.aluno.pk)
        # except Aluno.DoesNotExist:
        #     return HttpResponse("Estudante não encontrado.", status=401)

        projeto = Projeto.objects.filter(alocacao__aluno=estudante).\
            distinct().\
            filter(ano=ano).\
            filter(semestre=semestre).last()

    # caso Professor ou Administrador
    elif usuario.tipo_de_usuario == 2 or usuario.tipo_de_usuario == 4:
        projeto = None
    else:
        return HttpResponse("Você não possui conta de estudante.", status=401)

    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        agendado = None
        for encontro in encontros:
            if str(encontro.id) == check_values[0]:
                if encontro.projeto != projeto:
                    encontro.projeto = projeto
                    encontro.save()
                agendado = encontro
            else:
                if encontro.projeto == projeto:
                    encontro.projeto = None
                    encontro.save()

        if agendado:
            subject = 'Dinâmica PFE agendada'
            recipient_list = []
            alocacoes = Alocacao.objects.filter(projeto=projeto)
            for alocacao in alocacoes:
                # mandar para cada membro do grupo
                recipient_list.append(alocacao.aluno.user.email)
            # sempre mandar para a conta do gmail
            recipient_list.append('pfeinsper@gmail.com')

            message = message_agendamento(agendado)
            check = email(subject, recipient_list, message)
            if check != 1:
                message = "Problema no envio, contacte:lpsoares@insper.edu.br"

            mensagem = "Agendado: " + str(agendado.startDate)
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Problema! Por favor reportar.")

    else:
        context = {
            'encontros': encontros,
            'projeto': projeto,
        }
        return render(request, 'estudantes/encontros_marcar.html', context)


@login_required
@transaction.atomic
def informacoes_adicionais(request):
    """Perguntas aos estudantes de trabalho/entidades/social/familia."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)

    if user.tipo_de_usuario == 3:
        mensagem = "Você não está cadastrado como aluno!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    if user.tipo_de_usuario == 1:

        estudante = Aluno.objects.get(pk=request.user.aluno.pk)

        vencido = configuracao_estudante_vencida(estudante)

        if (not vencido) and request.method == 'POST':

            estudante.trabalhou = request.POST.get("trabalhou", None)
            estudante.social = request.POST.get("social", None)
            estudante.entidade = request.POST.get("entidade", None)
            estudante.familia = request.POST.get("familia", None)

            estudante.user.linkedin = request.POST.get("linkedin", None)
            estudante.user.save()

            estudante.save()
            return render(request, 'users/atualizado.html',)

        context = {
            'vencido': vencido,
            'trabalhou': estudante.trabalhou,
            'social': estudante.social,
            'entidade': estudante.entidade,
            'familia': estudante.familia,
            'linkedin': estudante.user.linkedin,
            'entidades': Entidade.objects.all(),
        }
    else:  # Supostamente professores
        context = {
            'mensagem': "Você não está cadastrado como estudante.",
            'vencido': True,
            'trabalhou': "",
            'social': "",
            'entidade': "",
            'familia': "",
            'linkedin': user.linkedin,
            'entidades': Entidade.objects.all(),
        }
    return render(request, 'estudantes/informacoes_adicionais.html', context)


@login_required
def minhas_bancas(request):
    """Lista as bancas agendadas para um aluno."""
    aluno = get_object_or_404(Aluno, pk=request.user.aluno.pk)

    configuracao = Configuracao.objects.get()
    if not configuracao.liberados_projetos:
        if aluno.anoPFE > configuracao.ano or\
          (aluno.anoPFE == configuracao.ano and
           aluno.semestrePFE > configuracao.semestre):
            mensagem = "Projetos ainda não disponíveis para seu período PFE."
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

    projetos = Projeto.objects.filter(alocacao__aluno=aluno)
    bancas = Banca.objects.filter(projeto__in=projetos).order_by("-startDate")

    context = {
        'bancas': bancas,
    }
    return render(request, 'estudantes/minhas_bancas.html', context)


@login_required
@transaction.atomic
def selecao_propostas(request):
    """Exibe todos os projetos para os alunos aplicarem."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    liberadas_propostas = configuracao.liberadas_propostas

    # Vai para próximo semestre
    if semestre == 1:
        semestre = 2
    else:
        ano += 1
        semestre = 1

    propostas = Proposta.objects\
        .filter(ano=ano)\
        .filter(semestre=semestre)\
        .filter(disponivel=True)

    warnings = ""

    vencido = True

    if user.tipo_de_usuario == 1:

        vencido = timezone.now() > configuracao.prazo

        aluno = get_object_or_404(Aluno, pk=request.user.aluno.pk)

        if configuracao.semestre == 1:
            vencido |= aluno.anoPFE < configuracao.ano
            vencido |= aluno.anoPFE == configuracao.ano and \
                aluno.semestrePFE == 1
        else:
            vencido |= aluno.anoPFE <= configuracao.ano

        if vencido:
            mensagem = "Prazo vencido para seleção de propostas de propostas!"
            context = {
                "area_aluno": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        if liberadas_propostas and request.method == 'POST':
            prioridade = {}
            for proposta in propostas:
                check_values = request.POST.get('selection'+str(proposta.pk),
                                                "0")
                prioridade[proposta.pk] = check_values
            for i in range(1, len(propostas)+1):
                if i < 6 and list(prioridade.values()).count(str(i)) == 0:
                    warnings += "Nenhuma proposta com prioridade "
                    warnings += str(i)+"\n"
                if list(prioridade.values()).count(str(i)) > 1:
                    warnings += "Mais de uma proposta com prioridade "
                    warnings += str(i)+"\n"
            if warnings == "":  # Submissão Completa
                for proposta in propostas:
                    if prioridade[proposta.pk] != "0":
                        prio_int = int(prioridade[proposta.pk])
                        # Se lista for vazia
                        if not aluno.opcoes.filter(pk=proposta.pk):
                            Opcao.objects\
                                .create(aluno=aluno,
                                        proposta=proposta,
                                        prioridade=prio_int)
                        elif Opcao.objects.get(aluno=aluno, proposta=proposta)\
                                .prioridade != prio_int:
                            opc = Opcao.objects.get(aluno=aluno,
                                                    proposta=proposta)
                            opc.prioridade = prio_int
                            opc.save()
                    else:
                        # Se lista não for vazia
                        if aluno.opcoes.filter(pk=proposta.pk):
                            Opcao.objects\
                                .filter(aluno=aluno, proposta=proposta)\
                                .delete()
                message = create_message(aluno, ano, semestre)

                subject = 'PFE : '+aluno.user.username
                recipient_list = ['pfeinsper@gmail.com', aluno.user.email, ]
                check = email(subject, recipient_list, message)
                if check != 1:
                    message = "Erro no envio contacte:lpsoares@insper.edu.br"

                context = {'message': message, }
                return render(request, 'projetos/confirmacao.html', context)

            context = {'warnings': warnings, }
            return render(request, 'projetos/projetosincompleto.html', context)

        opcoes_temporarias = OpcaoTemporaria.objects.filter(aluno=aluno)

    elif user.tipo_de_usuario == 2 or user.tipo_de_usuario == 4:
        opcoes_temporarias = []

    else:
        return HttpResponse("Acesso irregular.", status=401)

    areas_normais = AreaDeInteresse.objects.filter(usuario=user, area__ativa=True).exists()
    areas_outras = AreaDeInteresse.objects.filter(usuario=user, area=None).exists()
    areas = areas_normais or areas_outras

    context = {
        'liberadas_propostas': liberadas_propostas,
        'vencido': vencido,
        'propostas': propostas,
        'opcoes_temporarias': opcoes_temporarias,
        'ano': ano,
        'semestre': semestre,
        "prazo": configuracao.prazo,
        "areas": areas,
        'warnings': warnings,
    }
    return render(request, 'estudantes/selecao_propostas.html', context)

@login_required
@transaction.atomic
def opcao_temporaria(request):
    """Ajax para definir opção temporária."""

    try:
        proposta_id = int(request.POST.get('proposta_id', None))
        prioridade = int(request.POST.get('prioridade', None))
    except (ValueError, TypeError):
        # erro na conversao
        return JsonResponse({'atualizado': False}, status=500)

    user = get_object_or_404(PFEUser, pk=request.user.pk)
    if user.tipo_de_usuario != 1:
        return JsonResponse({'atualizado': False}, status=500)

    proposta = get_object_or_404(Proposta, id=proposta_id)

    (reg, _created) = OpcaoTemporaria.objects.get_or_create(proposta=proposta, aluno=user.aluno)

    reg.prioridade = prioridade
    reg.save()

    data = {
        'atualizado': True,
    }

    return JsonResponse(data)
