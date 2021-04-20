#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import string
import random

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import html
from django.views import generic

from projetos.models import Configuracao, Projeto, Conexao, ObjetivosDeAprendizagem
from projetos.models import Banca, Area, Coorientador, Avaliacao2, Observacao

from projetos.messages import email
from projetos.support import calcula_objetivos

from .forms import PFEUserCreationForm
from .models import PFEUser, Aluno, Professor, Parceiro, Opcao, Administrador
from .models import Alocacao
from .support import get_edicoes


@login_required
def user_detail(request, primarykey):
    """Retorna a página conforme o perfil do usuário."""
    user = get_object_or_404(PFEUser, pk=primarykey)
    # try:
    #     user = PFEUser.objects.get(pk=primarykey)
    # except PFEUser.DoesNotExist:
    #     return HttpResponse("Usuário não encontrado.", status=401)

    if user.tipo_de_usuario == 1:  # aluno
        return redirect('estudante_detail', user.aluno.id)

    elif user.tipo_de_usuario == 2:  # professor
        return redirect('professor_detail', user.professor.id)

    elif user.tipo_de_usuario == 3:  # parceiro
        return redirect('parceiro_detail', user.parceiro.id)

    return HttpResponse("Usuário não encontrado.", status=401)


@login_required
def perfil(request):
    """Retorna a página conforme o perfil do usuário."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)
    # try:
    #     user = PFEUser.objects.get(pk=request.user.pk)
    # except PFEUser.DoesNotExist:
    #     return HttpResponse("Usuário não encontrado.", status=401)

    context = {
        'aluno': False,
        'professor': False,
        'parceiro': False,
        'administrador': False,
    }

    if user.tipo_de_usuario == 1:  # aluno
        context['aluno'] = get_object_or_404(Aluno, pk=request.user.aluno.pk)
        # try:
        #     context['aluno'] = Aluno.objects.get(pk=request.user.aluno.pk)
        # except Aluno.DoesNotExist:
        #     return HttpResponse("Estudante não encontrado.", status=401)

    elif user.tipo_de_usuario == 2:  # professor
        context['professor'] = get_object_or_404(Professor, pk=request.user.professor.pk)
        # try:
        #     context['professor'] = Professor.objects\
        #         .get(pk=request.user.professor.pk)
        # except Professor.DoesNotExist:
        #     return HttpResponse("Professor não encontrado.", status=401)

    elif user.tipo_de_usuario == 3:  # parceiro
        context['parceiro'] = get_object_or_404(Parceiro, pk=request.user.parceiro.pk)
        # try:
        #     context['parceiro'] = Parceiro.objects\
        #         .get(pk=request.user.parceiro.pk)
        # except Parceiro.DoesNotExist:
        #     return HttpResponse("Parceiro não encontrado.", status=401)

    elif user.tipo_de_usuario == 4:  # administrador
        context['administrador'] = get_object_or_404(Administrador, pk=request.user.administrador.pk)
        # try:
        #     context['administrador'] = Administrador.objects\
        #         .get(pk=request.user.administrador.pk)
        # except Administrador.DoesNotExist:
        #     return HttpResponse("Administrador não encontrado.", status=401)

    else:
        mensagem = "Seu perfil não foi encontrado!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    return render(request, 'users/profile_detail.html', context=context)


class SignUp(generic.CreateView):
    """Rotina para fazer o login."""

    form_class = PFEUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'


class Usuario(generic.DetailView):
    """Usuário."""

    model = Aluno


@login_required
@permission_required("users.altera_professor", login_url='/')
def estudantes_lista(request):
    """Gera lista com todos os alunos já registrados."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            if edicao == 'todas':
                anosemestre = "todos"
            elif edicao == 'trancou':
                anosemestre = "trancou"
            else:
                anosemestre = edicao

            # Conta soh alunos
            alunos_list = Aluno.objects\
                .filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])\
                .order_by(Lower("user__first_name"), Lower("user__last_name"))

            ano = 0
            semestre = 0

            tabela_alunos = {}

            totais = {}
            totais["computação"] = 0
            totais["mecânica"] = 0
            totais["mecatrônica"] = 0

            if anosemestre not in ("todos", "trancou"):
                ano = int(anosemestre.split(".")[0])
                semestre = int(anosemestre.split(".")[1])

                alunos_list = alunos_list.filter(trancado=False)

                alunos_semestre = alunos_list\
                    .filter(alocacao__projeto__ano=ano,
                            alocacao__projeto__semestre=semestre)\
                    .distinct()

                tabela_alunos[ano] = {}
                tabela_alunos[ano][semestre] = {}

                tabela_alunos[ano][semestre]["computação"] =\
                    alunos_semestre.filter(curso__exact='C').count()
                totais["computação"] += tabela_alunos[ano][semestre]["computação"]
                tabela_alunos[ano][semestre]["mecânica"] =\
                    alunos_semestre.filter(curso__exact='M').count()
                totais["mecânica"] += tabela_alunos[ano][semestre]["mecânica"]
                tabela_alunos[ano][semestre]["mecatrônica"] =\
                    alunos_semestre.filter(curso__exact='X').count()
                totais["mecatrônica"] += tabela_alunos[ano][semestre]["mecatrônica"]
                tabela_alunos[ano][semestre]["total"] =\
                    alunos_semestre.count()

                alunos_list = alunos_semestre |\
                    alunos_list.filter(anoPFE=ano, semestrePFE=semestre).distinct()

            else:

                if anosemestre == "todos":
                    alunos_list = alunos_list.filter(trancado=False)
                else:
                    alunos_list = alunos_list.filter(trancado=True)
                    ano = "trancou"

                ano_tmp = 2018
                semestre_tmp = 2
                while True:
                    alunos_semestre = alunos_list\
                        .filter(alocacao__projeto__ano=ano_tmp,
                                alocacao__projeto__semestre=semestre_tmp)\
                        .distinct()
                    if ano_tmp not in tabela_alunos:
                        tabela_alunos[ano_tmp] = {}
                    if semestre_tmp not in tabela_alunos[ano_tmp]:
                        tabela_alunos[ano_tmp][semestre_tmp] = {}

                    tabela_alunos[ano_tmp][semestre_tmp]["computação"] =\
                        alunos_semestre.filter(curso__exact='C').count()
                    totais["computação"] += \
                        tabela_alunos[ano_tmp][semestre_tmp]["computação"]
                    tabela_alunos[ano_tmp][semestre_tmp]["mecânica"] =\
                        alunos_semestre.filter(curso__exact='M').count()
                    totais["mecânica"] += \
                        tabela_alunos[ano_tmp][semestre_tmp]["mecânica"]
                    tabela_alunos[ano_tmp][semestre_tmp]["mecatrônica"] =\
                        alunos_semestre.filter(curso__exact='X').count()
                    totais["mecatrônica"] += \
                        tabela_alunos[ano_tmp][semestre_tmp]["mecatrônica"]
                    tabela_alunos[ano_tmp][semestre_tmp]["total"] =\
                        alunos_semestre.count()

                    if (ano_tmp == configuracao.ano) and \
                    (semestre_tmp == configuracao.semestre):
                        break

                    if semestre_tmp == 1:
                        semestre_tmp = 2
                    else:
                        ano_tmp += 1
                        semestre_tmp = 1

            num_alunos = alunos_list.count()

            # Conta alunos computacao
            num_alunos_comp = alunos_list.filter(curso__exact='C').count()

            # Conta alunos mecatrônica
            num_alunos_mxt = alunos_list.filter(curso__exact='X').count()

            # Conta alunos mecânica
            num_alunos_mec = alunos_list.filter(curso__exact='M').count()

            # Estudantes masculino
            num_alunos_masculino = alunos_list.filter(user__genero='M').count()

            # Estudantes feminino
            num_alunos_feminino = alunos_list.filter(user__genero='F').count()

            totais["total"] = (totais["computação"] +
                            totais["mecânica"] +
                            totais["mecatrônica"])

            context = {
                'alunos_list': alunos_list,
                'num_alunos': num_alunos,
                'num_alunos_comp': num_alunos_comp,
                'num_alunos_mxt': num_alunos_mxt,
                'num_alunos_mec': num_alunos_mec,
                'num_alunos_masculino': num_alunos_masculino,
                'num_alunos_feminino': num_alunos_feminino,
                'configuracao': configuracao,
                'tabela_alunos': tabela_alunos,
                'totais': totais,
                'ano': ano,
                'semestre': semestre,
                'ano_semestre': str(ano)+"."+str(semestre),
                'loop_anos': range(2018, configuracao.ano+1),
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Aluno)
        context = {
                'edicoes': edicoes,
            }

    return render(request, 'users/estudantes_lista.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def estudantes_notas(request):
    """Gera lista com todos os alunos já registrados."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if 'edicao' in request.POST:

            anosemestre = request.POST['edicao']
            ano = int(anosemestre.split(".")[0])
            semestre = int(anosemestre.split(".")[1])

            # Conta soh alunos
            alunos_list = Aluno.objects\
                .filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])\
                .order_by(Lower("user__first_name"), Lower("user__last_name"))

            alunos_list = alunos_list.filter(trancado=False)

            alunos_semestre = alunos_list\
                .filter(alocacao__projeto__ano=ano,
                        alocacao__projeto__semestre=semestre)\
                .distinct()

            alunos_list = alunos_semestre |\
                alunos_list.filter(anoPFE=ano, semestrePFE=semestre).distinct()

            context = {
                'alunos_list': alunos_list,
                'configuracao': configuracao,
                'ano': ano,
                'semestre': semestre,
                'ano_semestre': str(ano)+"."+str(semestre),
                'loop_anos': range(2018, configuracao.ano+1),
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Aluno)
        context = {
                'edicoes': edicoes,
            }

    return render(request, 'users/estudantes_notas.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def estudantes_inscritos(request):
    """Mostra todos os alunos que estão se inscrevendo em projetos."""
    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']

            ano = int(edicao.split(".")[0])
            semestre = int(edicao.split(".")[1])

            alunos_se_inscrevendo = Aluno.objects.filter(trancado=False)\
                .filter(anoPFE=ano, semestrePFE=semestre)\
                .order_by(Lower("user__first_name"), Lower("user__last_name"))

            # Conta soh alunos
            alunos = alunos_se_inscrevendo\
                .filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])

            num_alunos = alunos.count()

            # Conta alunos computacao
            num_alunos_comp = alunos.filter(curso__exact='C').count()

            # Conta alunos mecatrônica
            num_alunos_mxt = alunos.filter(curso__exact='X').count()

            # Conta alunos mecânica
            num_alunos_mec = alunos.filter(curso__exact='M').count()

            inscritos = 0
            ninscritos = 0
            opcoes = []
            for aluno in alunos:
                opcao = Opcao.objects.filter(aluno=aluno)\
                    .filter(proposta__ano=ano, proposta__semestre=semestre)
                opcoes.append(opcao)
                if opcao.count() >= 5:
                    inscritos += 1
                else:
                    ninscritos += 1
            alunos_list = zip(alunos, opcoes)

            context = {
                'alunos_list': alunos_list,
                'num_alunos': num_alunos,
                'num_alunos_comp': num_alunos_comp,
                'num_alunos_mxt': num_alunos_mxt,
                'num_alunos_mec': num_alunos_mec,
                'inscritos': inscritos,
                'ninscritos': ninscritos,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Aluno)
        context = {
                'edicoes': edicoes,
            }

    return render(request, 'users/estudantes_inscritos.html', context=context)

@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
def edita_notas(request, primarykey):
    """Edita as notas do estudante."""
    alocacao = get_object_or_404(Alocacao, pk=primarykey)
    # try:
    #     alocacao = Alocacao.objects.get(pk=primarykey)
    # except Alocacao.DoesNotExist:
    #     return HttpResponse("Alocação não encontrada.", status=401)

    objetivos = ObjetivosDeAprendizagem.objects.all()

    # (10, 'Relatório de Planejamento'),
    rpl = Avaliacao2.objects.filter(tipo_de_avaliacao=10,
                                    projeto=alocacao.projeto)

    # (10, 'Relatório de Planejamento'),
    rpl_obs = Observacao.objects.filter(tipo_de_avaliacao=10,
                                        projeto=alocacao.projeto)

    # (21, 'Relatório Intermediário Individual'),
    rii = Avaliacao2.objects.filter(tipo_de_avaliacao=21,
                                    alocacao=alocacao)

    # (21, 'Relatório Intermediário Individual'),
    rii_obs = Observacao.objects.filter(tipo_de_avaliacao=21,
                                        alocacao=alocacao)

    # (11, 'Relatório Intermediário de Grupo'),
    rig = Avaliacao2.objects.filter(tipo_de_avaliacao=11,
                                    projeto=alocacao.projeto)

    # (11, 'Relatório Intermediário de Grupo'),
    rig_obs = Observacao.objects.filter(tipo_de_avaliacao=11,
                                        projeto=alocacao.projeto)

    # (22, 'Relatório Final Individual'),
    rfi = Avaliacao2.objects.filter(tipo_de_avaliacao=22,
                                    alocacao=alocacao)

    # (22, 'Relatório Final Individual'),
    rfi_obs = Observacao.objects.filter(tipo_de_avaliacao=22,
                                        alocacao=alocacao)

    # (12, 'Relatório Final de Grupo'),
    rfg = Avaliacao2.objects.filter(tipo_de_avaliacao=12,
                                    projeto=alocacao.projeto)

    # (12, 'Relatório Final de Grupo'),
    rfg_obs = Observacao.objects.filter(tipo_de_avaliacao=12,
                                        projeto=alocacao.projeto)

    # ( 1, 'Banca Intermediária'),
    bi = Avaliacao2.objects.filter(tipo_de_avaliacao=1,
                                   projeto=alocacao.projeto)

    # ( 2, 'Banca Final'),
    bf = Avaliacao2.objects.filter(tipo_de_avaliacao=2,
                                   projeto=alocacao.projeto)

    if request.method == 'POST':

        # RPL
        nota = request.POST.get('rpl_nota', "")
        peso = request.POST.get('rpl_peso', "")
        if nota != "":
            (reg, _created)  = rpl.get_or_create(projeto=alocacao.projeto)
            if _created:
                reg.tipo_de_avaliacao = 10
                if alocacao.projeto.orientador:
                    reg.avaliador = alocacao.projeto.orientador.user
            reg.peso = float(peso)
            reg.nota = float(nota)
            reg.save()

        for objetivo in objetivos:

            # RII
            if objetivo.avaliacao_aluno:
                nota = request.POST.get('rii_nota_'+str(objetivo), "")
                peso = request.POST.get('rii_peso_'+str(objetivo), "")
                if nota != "":
                    (reg, _created)  = rii.get_or_create(objetivo=objetivo)
                    if _created:
                        reg.tipo_de_avaliacao = 21
                        reg.alocacao = alocacao
                        if alocacao.projeto.orientador:
                            reg.avaliador = alocacao.projeto.orientador.user
                        reg.projeto = alocacao.projeto
                    reg.peso = float(peso)
                    reg.nota = float(nota)
                    reg.save()

            # RIG
            if objetivo.avaliacao_grupo:
                nota = request.POST.get('rig_nota_'+str(objetivo), "")
                peso = request.POST.get('rig_peso_'+str(objetivo), "")
                if nota != "":
                    (reg, _created)  = rig.get_or_create(objetivo=objetivo)
                    if _created:
                        reg.tipo_de_avaliacao = 11
                        if alocacao.projeto.orientador:
                            reg.avaliador = alocacao.projeto.orientador.user
                        reg.projeto = alocacao.projeto
                    reg.peso = float(peso)
                    reg.nota = float(nota)
                    reg.save()

            # RFI
            if objetivo.avaliacao_aluno:
                nota = request.POST.get('rfi_nota_'+str(objetivo), "")
                peso = request.POST.get('rfi_peso_'+str(objetivo), "")
                if nota != "":
                    (reg, _created)  = rfi.get_or_create(objetivo=objetivo)
                    if _created:
                        reg.tipo_de_avaliacao = 22
                        reg.alocacao = alocacao
                        if alocacao.projeto.orientador:
                            reg.avaliador = alocacao.projeto.orientador.user
                        reg.projeto = alocacao.projeto
                    reg.peso = float(peso)
                    reg.nota = float(nota)
                    reg.save()

            # RFG
            if objetivo.avaliacao_grupo:
                nota = request.POST.get('rfg_nota_'+str(objetivo), "")
                peso = request.POST.get('rfg_peso_'+str(objetivo), "")
                if nota != "":
                    (reg, _created)  = rfg.get_or_create(objetivo=objetivo)
                    if _created:
                        reg.tipo_de_avaliacao = 12
                        if alocacao.projeto.orientador:
                            reg.avaliador = alocacao.projeto.orientador.user
                        reg.projeto = alocacao.projeto
                    reg.peso = float(peso)
                    reg.nota = float(nota)
                    reg.save()

        # RPL
        obs = request.POST.get('rpl_obs', "")
        if obs:
            reg  = rpl_obs.last()
            if not reg:
                reg = Observacao.create(projeto=alocacao.projeto)
                reg.tipo_de_avaliacao = 10
                if alocacao.projeto.orientador:
                    reg.avaliador = alocacao.projeto.orientador.user
            reg.observacoes = obs
            reg.save()

        # RII
        obs = request.POST.get('rii_obs', "")
        if obs:
            reg  = rii_obs.last()
            if not reg:
                reg = Observacao.create(projeto=alocacao.projeto)
                reg.tipo_de_avaliacao = 21
                reg.alocacao = alocacao
                if alocacao.projeto.orientador:
                    reg.avaliador = alocacao.projeto.orientador.user
            reg.observacoes = obs
            reg.save()

        # RIG
        obs = request.POST.get('rig_obs', "")
        if obs:
            reg  = rig_obs.last()
            if not reg:
                reg = Observacao.create(projeto=alocacao.projeto)
                reg.tipo_de_avaliacao = 11
                if alocacao.projeto.orientador:
                    reg.avaliador = alocacao.projeto.orientador.user
            reg.observacoes = obs
            reg.save()

        # RFI
        obs = request.POST.get('rfi_obs', "")
        if obs:
            reg  = rfi_obs.last()
            if not reg:
                reg = Observacao.create(projeto=alocacao.projeto)
                reg.tipo_de_avaliacao = 22
                reg.alocacao = alocacao
                if alocacao.projeto.orientador:
                    reg.avaliador = alocacao.projeto.orientador.user
            reg.observacoes = obs
            reg.save()

        # RFG
        obs = request.POST.get('rfg_obs', "")
        if obs:
            reg  = rfg_obs.last()
            if not reg:
                reg = Observacao.create(projeto=alocacao.projeto)
                reg.tipo_de_avaliacao = 12
                if alocacao.projeto.orientador:
                    reg.avaliador = alocacao.projeto.orientador.user
            reg.observacoes = obs
            reg.save()


        mensagem = "Notas atualizadas<br>\n"
        mensagem += "Peso Final = " + str(alocacao.get_media["pesos"]*100) + "% <br>\n"
        mensagem += "Média = " + str(alocacao.get_media["media"]) + "<br>\n"
        mensagem = html.urlize(mensagem)
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)


    rpl_nota = None
    rpl_peso = None
    rpl_existe = False
    if (alocacao.projeto.ano < 2020) or (alocacao.projeto.ano == 2020 and alocacao.projeto.semestre == 1):
        rpl_existe = True
        if rpl:
            rpl_nota = rpl.last().nota
            rpl_peso = rpl.last().peso

    rii_peso = {}
    rii_nota = {}
    for registro in rii:
        rii_nota[registro.objetivo] = registro.nota 
        rii_peso[registro.objetivo] = registro.peso

    rig_peso = {}
    rig_nota = {}
    for registro in rig:
        rig_nota[registro.objetivo] = registro.nota 
        rig_peso[registro.objetivo] = registro.peso

    rfi_peso = {}
    rfi_nota = {}
    for registro in rfi:
        rfi_nota[registro.objetivo] = registro.nota 
        rfi_peso[registro.objetivo] = registro.peso

    rfg_peso = {}
    rfg_nota = {}
    for registro in rfg:
        rfg_nota[registro.objetivo] = registro.nota 
        rfg_peso[registro.objetivo] = registro.peso


    context = {
        'alocacao': alocacao,
        'objetivos': objetivos,
        'rpl': rpl_existe,
        'rpl_nota': rpl_nota,
        'rpl_peso': rpl_peso,
        'rpl_obs': rpl_obs.last(),
        'rii_nota': rii_nota,
        'rii_peso': rii_peso,
        'rii_obs': rii_obs.last(),
        'rig_nota': rig_nota,
        'rig_peso': rig_peso,
        'rig_obs': rig_obs.last(),
        'rfi_nota': rfi_nota,
        'rfi_peso': rfi_peso,
        'rfi_obs': rfi_obs.last(),
        'rfg_nota': rfg_nota,
        'rfg_peso': rfg_peso,
        'rfg_obs': rfg_obs.last(),
        'bi': bi,
        'bf': bf,
    }

    return render(request, 'users/edita_nota.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def estudante_detail(request, primarykey):
    """Mostra detalhes sobre o estudante."""
    aluno = Aluno.objects.filter(pk=primarykey).first()
    areas = Area.objects.filter(ativa=True)

    alocacoes = Alocacao.objects.filter(aluno=aluno)

    context = calcula_objetivos(alocacoes)

    media_individual = {}
    media_grupo = {}

    for media in context["medias_geral"]:

        count = 0
        media_individual[media] = {}
        media_individual[media]["cor"] = context["medias_geral"][media]["cor"]
        media_individual[media]["media"] = 0
        if media.avaliacao_aluno:
            media_individual[media]["media"] += context["medias_rii"][media]["media"]
            count += 1
        if media.avaliacao_aluno:
            media_individual[media]["media"] += context["medias_rfi"][media]["media"]
            count += 1
        if count > 0:
            media_individual[media]["media"] /= count
        else:
            media_individual[media]["media"] = -1

        count = 0
        media_grupo[media] = {}
        media_grupo[media]["cor"] = context["medias_geral"][media]["cor"]
        media_grupo[media]["media"] = 0
        if media.avaliacao_grupo:
            media_grupo[media]["media"] += context["medias_rig"][media]["media"]
            count += 1
        if media.avaliacao_grupo:
            media_grupo[media]["media"] += context["medias_rfg"][media]["media"]
            count += 1
        if media.avaliacao_banca:
            media_grupo[media]["media"] += context["medias_bi"][media]["media"]
            count += 1
        if media.avaliacao_banca:
            media_grupo[media]["media"] += context["medias_bf"][media]["media"]
            count += 1
        if count > 0:
            media_grupo[media]["media"] /= count
        else:
            media_grupo[media]["media"] = -1

    context['media_individual'] = media_individual
    context['media_grupo'] = media_grupo
    context['aluno'] = aluno
    context['areast'] = areas
    
    return render(request, 'users/estudante_detail.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def professor_detail(request, primarykey):
    """Mostra detalhes sobre o professor."""
    professor = get_object_or_404(Professor, pk=primarykey)
    # try:
    #     professor = Professor.objects.get(pk=primarykey)
    # except Professor.DoesNotExist:
    #     return HttpResponse("Professor não encontrado.", status=401)

    projetos = Projeto.objects.filter(orientador=professor)\
        .order_by("ano", "semestre", "titulo")

    coorientacoes = Coorientador.objects.filter(usuario=professor.user)\
        .order_by("projeto__ano",
                  "projeto__semestre",
                  "projeto__titulo")

    bancas = (Banca.objects.filter(membro1=professor.user) |
              Banca.objects.filter(membro2=professor.user) |
              Banca.objects.filter(membro3=professor.user))

    bancas = bancas.order_by("startDate")

    context = {
        'professor': professor,
        'projetos': projetos,
        'coorientacoes': coorientacoes,
        'bancas': bancas,
    }

    return render(request, 'users/professor_detail.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def parceiro_detail(request, primarykey):
    """Mostra detalhes sobre o parceiro."""
    parceiro = get_object_or_404(Parceiro, pk=primarykey)

    conexoes = Conexao.objects.filter(parceiro=parceiro)

    context = {
        'parceiro': parceiro,
        'conexoes': conexoes,
    }
    return render(request, 'users/parceiro_detail.html', context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", login_url='/')
def contas_senhas(request, anosemestre):
    """Envia conta e senha para todos os estudantes que estão no semestre."""
    configuracao = get_object_or_404(Configuracao)
    # configuracao = Configuracao.objects.get()

    ano = int(anosemestre.split(".")[0])
    semestre = int(anosemestre.split(".")[1])

    estudantes = Aluno.objects.filter(trancado=False)\
        .filter(anoPFE=ano, semestrePFE=semestre)\
        .filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])\
        .order_by(Lower("user__first_name"), Lower("user__last_name"))

    if request.method == 'POST':
        mensagem = "Enviado para:<br>\n<br>\n"
        for estudante in estudantes:
            mensagem += estudante.user.get_full_name() + " " +\
                        "&lt;" + estudante.user.email + "&gt;<br>\n"

            # Atualizando senha do usuário.
            senha = ''.join(random.SystemRandom().
                            choice(string.ascii_lowercase + string.digits)
                            for _ in range(6))
            estudante.user.set_password(senha)
            estudante.user.save()

            # Preparando mensagem para enviar para usuário.
            message_email = estudante.user.get_full_name() + ",\n\n\n"
            message_email += "Você está recebendo sua conta e senha para acessar o sistema do "
            message_email += "Projeto Final de Engenharia (PFE)."
            message_email += "\n\n"
            message_email += "O endereço do servidor é: "
            message_email += "<a href='http://pfe.insper.edu.br/'>http://pfe.insper.edu.br/</a>"
            message_email += "\n\n"
            message_email += "Preencha os formulários de suas áreas de interesse "
            message_email += "e de informações adicionais sobre você.\n"
            message_email += "Faça sua seleção de propostas de projetos "
            message_email += "conforme sua ordem de interesse.\n"
            message_email += "\n"
            message_email += "O prazo para a escolha de projetos é: "
            message_email += configuracao.prazo.strftime("%d/%m/%Y %H:%M") + "\n"
            message_email += "Você pode alterar quantas vezes desejar suas escolhas "
            message_email += "até a data limite.\n"
            message_email += "\n\n"
            message_email += "Sua conta é: <b>" + estudante.user.username + "</b>\n"
            message_email += "Sua senha é: <b>" + senha + "</b>\n"
            message_email += "\n\n"
            message_email += "Qualquer dúvida, envie e-mail para: "
            message_email += "<a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>"
            message_email += "\n\n"
            message_email += "Nos próximos dias o departamento de carreiras entrará em contato "
            message_email += "com datas de reuniões para maiores esclarecimentos dos projetos."
            message_email += "\n\n"
            message_email += "&nbsp;&nbsp;&nbsp;&nbsp;atenciosamente, coordenação do PFE\n"
            message_email = message_email.replace('\n', '<br>\n')

            # Enviando e-mail com mensagem para usuário.
            subject = 'Conta PFE : ' + estudante.user.get_full_name()
            recipient_list = [estudante.user.email, 'pfeinsper@gmail.com', ]
            check = email(subject, recipient_list, message_email)
            if check != 1:
                mensagem = "Erro de conexão, contacte:lpsoares@insper.edu.br"

        mensagem = html.urlize(mensagem)
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    context = {
        'estudantes': estudantes,
        'ano': ano,
        'semestre': semestre,
        'loop_anos': range(2018, configuracao.ano+1),
    }

    return render(request, 'users/contas_senhas.html', context=context)
