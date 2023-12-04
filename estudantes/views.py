"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

import datetime
from hashids import Hashids

from django.conf import settings

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseNotFound

from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from projetos.models import Projeto, Proposta, Configuracao, Area, AreaDeInteresse
from projetos.models import Encontro, Banca, Entidade, FeedbackEstudante, Evento, Documento

from .support import cria_area_estudante

from projetos.messages import email, message_agendamento, create_message

from users.models import PFEUser, Alocacao, Opcao, OpcaoTemporaria

from users.support import configuracao_estudante_vencida, configuracao_pares_vencida, adianta_semestre

from academica.models import Composicao

from .models import Relato, Pares

from administracao.support import get_limite_propostas, usuario_sem_acesso

from administracao.models import Carta

@login_required
def index_estudantes(request):
    """Mostra página principal do usuário estudante."""
    configuracao = get_object_or_404(Configuracao)

    context = {
        "configuracao": configuracao,
        "vencido": timezone.now().date() > get_limite_propostas(configuracao)
    }

    ano = configuracao.ano
    semestre = configuracao.semestre

    # Caso estudante
    if request.user.tipo_de_usuario == 1:

        projeto = Projeto.objects\
            .filter(alocacao__aluno=request.user.aluno).order_by("ano", "semestre").last()

        context["projeto"] = projeto

        # Estudantes de processos passados sempre terrão seleção vencida
        if semestre == 1:
            context["vencido"] |= request.user.aluno.anoPFE < ano
            context["vencido"] |= request.user.aluno.anoPFE == ano and \
                request.user.aluno.semestrePFE == 1
        else:
            context["vencido"] |= (request.user.aluno.anoPFE <= ano)

        if projeto:
            hoje = datetime.date.today()

            eventos = Evento.objects.filter(startDate__year=projeto.ano)
            if projeto.semestre == 1:
                banca_final = eventos.filter(tipo_de_evento=15, startDate__month__lt=7).last()
            else:
                banca_final = eventos.filter(tipo_de_evento=15, startDate__month__gt=6).last()

            if banca_final:
                context['fase_final'] = hoje > banca_final.endDate

        # Avaliações de Pares
        context["fora_fase_feedback_intermediario"], _, _ = configuracao_pares_vencida(request.user.aluno, 31) # 31, 'Avaliação de Pares Intermediária'
        context["fora_fase_feedback_final"], _, _ = configuracao_pares_vencida(request.user.aluno, 32) # 32, 'Avaliação de Pares Final'

    # Caso professor ou administrador
    elif request.user.tipo_de_usuario in (2, 4):
        context['fase_final'] = True

    # Caso parceiro
    else:
        return HttpResponse("Usuário sem acesso.", status=401)

    context["ano"], context["semestre"] = adianta_semestre(ano, semestre)
    context["limite_propostas"] = get_limite_propostas(configuracao)

    return render(request, 'estudantes/index_estudantes.html', context=context)


@login_required
def areas_interesse(request):
    """Para estudantes definirem suas áreas de interesse."""
    context = {'areast': Area.objects.filter(ativa=True),}

    # Caso seja estudante
    if request.user.tipo_de_usuario == 1:  # Estudante
        vencido = configuracao_estudante_vencida(request.user.aluno)
        if (not vencido) and request.method == 'POST':
            cria_area_estudante(request, request.user.aluno)
            return render(request, 'users/atualizado.html',)
        context['vencido'] = vencido
        context['estudante'] = request.user.aluno

    # caso Professores ou Administrador
    elif request.user.tipo_de_usuario in (2, 4):
        context['mensagem'] = "Você não está cadastrado como estudante."
        context['vencido'] = True

    # caso não seja Estudante, Professor ou Administrador (ou seja Parceiro)
    v = usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    if v: return v  # Prof, Adm

    return render(request, 'estudantes/areas_interesse.html', context=context)


@login_required
@transaction.atomic
def encontros_marcar(request):
    """Encontros a serem agendados pelos estudantes."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    aviso = None  # Mensagem de aviso caso algum problema

    hoje = datetime.date.today()
    encontros = Encontro.objects.filter(startDate__gt=hoje)\
        .order_by('startDate')

    if request.user.tipo_de_usuario == 1:  # Estudante
        projeto = Projeto.objects.filter(alocacao__aluno=request.user.aluno).\
            distinct().\
            filter(ano=ano).\
            filter(semestre=semestre).last()

    # caso Professor ou Administrador
    elif request.user.tipo_de_usuario in (2, 4):
        projeto = None
    else:
        return HttpResponse("Você não possui conta de estudante.", status=401)

    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        
        agendado = None
        cancelado = None

        if not check_values:
            aviso = "Selecione um horário."

        else:    
            for encontro in encontros:
                if str(encontro.id) == check_values[0]:
                    
                    if encontro.projeto is None or encontro.projeto == projeto:
                        # Se projeto estava sem seleção ainda, selecionar
                        encontro.projeto = projeto
                        encontro.save()
                        agendado = encontro

                    elif encontro.projeto != projeto:
                        # Se projeto foi selecionad por outro grupo
                        aviso = "Infelizmente nesse meio tempo algum grupo selecionou o horário indicado!\nPor favor, selecione outro horário."

                else:
                    # Limpa seleção caso haja uma mudança
                    if encontro.projeto == projeto:
                        cancelado = "dia " + str(encontro.startDate.strftime("%d/%m/%Y")) + " das " + str(encontro.startDate.strftime("%H:%M")) + ' às ' + str(encontro.endDate.strftime("%H:%M"))
                        encontro.projeto = None
                        encontro.save()

        if agendado:
            subject = 'Dinâmica PFE agendada'
            recipient_list = []
            alocacoes = Alocacao.objects.filter(projeto=projeto)
            for alocacao in alocacoes:
                # mandar para cada membro do grupo
                recipient_list.append(alocacao.aluno.user.email)
            
            # coordenadores do curso
            coordenacoes = PFEUser.objects.filter(coordenacao=True)
            for coordenador in coordenacoes:
                recipient_list.append(str(coordenador.email))

            # sempre mandar para a conta do gmail
            recipient_list.append('pfeinsper@gmail.com')

            message = message_agendamento(agendado, cancelado)
            check = email(subject, recipient_list, message)
            if check != 1:
                message = "Problema no envio, contacte:lpsoares@insper.edu.br"

            mensagem = "Agendado: " + str(agendado.startDate)
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        if not aviso:
            return HttpResponse("Problema! Por favor reportar.")

    context = {
        "encontros": encontros,
        "projeto": projeto,
        "aviso": aviso,
    }
    return render(request, 'estudantes/encontros_marcar.html', context)


def estudante_feedback_geral(request, usuario):
    """Para Feedback finais dos Estudantes."""
    mensagem = ""
    
    if usuario.tipo_de_usuario in (2, 4): # Caso professor ou administrador
        mensagem = "Você está acessando como administrador!<br>Esse formulário fica disponível para os estudantes após as bancas finais."
        projeto = None

    elif usuario.tipo_de_usuario == 1: # Estudante
        hoje = datetime.date.today()
        projeto = Projeto.objects.filter(alocacao__aluno=usuario.aluno).order_by("ano", "semestre").last()
        eventos = Evento.objects.filter(startDate__year=projeto.ano)
        if projeto.semestre == 1:
            banca_final = eventos.filter(tipo_de_evento=15, startDate__month__lt=7).last()
        else:
            banca_final = eventos.filter(tipo_de_evento=15, startDate__month__gt=6).last()

        if not banca_final or (banca_final and hoje <= banca_final.endDate):
            mensagem = "Fora do período de feedback do PFE!"
            context = {"mensagem": mensagem,}
            return render(request, 'generic.html', context=context)

    if request.method == 'POST':
        feedback = FeedbackEstudante.create()
        feedback.estudante = usuario.aluno
        feedback.projeto = projeto

        recomendaria = request.POST.get("recomendaria", None)
        if recomendaria:
            feedback.recomendaria = int(recomendaria[len("option"):])
            
        primeira_opcao = request.POST.get("primeira_opcao", None)
        if primeira_opcao:
            feedback.primeira_opcao = primeira_opcao[len("option"):] == "S"

        proposta = request.POST.get("proposta", None)
        if proposta:
            feedback.proposta = int(proposta[len("option"):])

        trabalhando = request.POST.get("trabalhando", None)
        if trabalhando:
            feedback.trabalhando = int(trabalhando[len("option"):])

        feedback.outros = request.POST.get("outros", "")

        feedback.save()

        mensagem = "Feedback recebido, obrigado!"
        context = {
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    context = {
        "usuario": usuario,
        "projeto": projeto,
        "mensagem": mensagem,
    }
    return render(request, 'estudantes/estudante_feedback.html', context)



@login_required
@transaction.atomic
def estudante_feedback(request):
    """Para Feedback finais dos Estudantes."""
    return estudante_feedback_geral(request, request.user)


@transaction.atomic
def estudante_feedback_hashid(request, hashid):
    """Para Feedback finais dos Estudantes."""
    hashids = Hashids(salt=settings.SALT, min_length=8)

    try:
        id = hashids.decode(hashid)[0]
        usuario = get_object_or_404(PFEUser, pk=id)
        return estudante_feedback_geral(request, usuario)

    except (ValueError, TypeError, PFEUser.DoesNotExist):
        return HttpResponseNotFound('<h1>Usuário não encontrado!</h1>')


@login_required
@transaction.atomic
def avaliacao_pares(request, momento):
    """Permite realizar a avaliação de pares."""
    configuracao = get_object_or_404(Configuracao)

    v = usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    if v: return v  # Prof, Adm

    estudante = None
    if request.user.tipo_de_usuario == 1:
        estudante = request.user.aluno

    # Avaliações de Pares
    # 31, 'Avaliação de Pares Intermediária'
    # 32, 'Avaliação de Pares Final'
    if momento=="intermediaria":
        prazo, inicio, fim = configuracao_pares_vencida(estudante, 31)
        tipo=0
    else:  # Final
        prazo, inicio, fim = configuracao_pares_vencida(estudante, 32)
        tipo=1

    if request.user.tipo_de_usuario == 1:
        projeto = Projeto.objects\
            .filter(alocacao__aluno=estudante, ano=configuracao.ano, semestre=configuracao.semestre).first()
        
        if not projeto:
            mensagem = "Você não está alocao em um projeto esse semestre!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        alocacao_de = Alocacao.objects.get(projeto=projeto, aluno=estudante)
        alocacoes = Alocacao.objects.filter(projeto=projeto).exclude(aluno=estudante)

        if (not prazo) and request.method == 'POST':

            for alocacao in alocacoes:

                (pares, _created) = Pares.objects.get_or_create(alocacao_de=alocacao_de,
                                                                alocacao_para=alocacao,
                                                                tipo=tipo)

                if _created:
                    pares.alocacao_de = alocacao_de
                    pares.alocacao_para = alocacao
                    pares.tipo=tipo

                pares.aprecia = request.POST.get("aprecia"+str(alocacao.id), None)
                pares.atrapalhando = request.POST.get("atrapalhando"+str(alocacao.id), None)
                pares.mudar = request.POST.get("mudar"+str(alocacao.id), None)

                entrega = request.POST.get("entrega"+str(alocacao.id), None)
                if entrega:
                    pares.entrega = int(entrega)

                iniciativa = request.POST.get("iniciativa"+str(alocacao.id), None)
                if iniciativa:
                    pares.iniciativa = int(iniciativa)

                comunicacao = request.POST.get("comunicacao"+str(alocacao.id), None)
                if comunicacao:
                    pares.comunicacao = int(comunicacao)

                pares.save()

            return render(request, 'users/atualizado.html',)
        
        pares = []
        for alocacao in alocacoes:
            par = Pares.objects.filter(alocacao_de=alocacao_de, alocacao_para=alocacao, tipo=tipo).first()
            pares.append(par)

        colegas = zip(alocacoes, pares)

        context = {
            "vencido": prazo,
            "colegas": colegas,
            "momento": momento,
            "inicio": inicio,
            "fim": fim,
            "configuracao": configuracao,
        }
    else:  # Supostamente professores
        context = {
            "mensagem": "Você não está cadastrado como estudante.",
            "vencido": prazo,
            "colegas": [[{"aluno":"Fulano (exemplo)",id:0},None],[{"aluno":"Beltrano (exemplo)",id:0},None]],
            "momento": momento,
            "inicio": inicio,
            "fim": fim,
            "configuracao": configuracao,
        }
    return render(request, 'estudantes/avaliacao_pares.html', context)


@login_required
@transaction.atomic
def informacoes_adicionais(request):
    """Perguntas aos estudantes de trabalho/entidades/social/familia."""
    v = usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    if v: return v  # Prof, Adm

    if request.user.tipo_de_usuario == 1:

        estudante = request.user.aluno

        vencido = configuracao_estudante_vencida(estudante)

        if (not vencido) and request.method == 'POST':

            estudante.trabalhou = request.POST.get("trabalhou", None)
            estudante.social = request.POST.get("social", None)
            estudante.entidade = request.POST.get("entidade", None)
            estudante.familia = request.POST.get("familia", None)

            estudante.user.linkedin = request.POST.get("linkedin", None)
            estudante.user.save()

            estudante.save()
            return render(request, "users/atualizado.html",)

        context = {
            "vencido": vencido,
            "estudante": estudante,
            "entidades": Entidade.objects.all(),
        }
    else:  # Supostamente professores
        context = {
            "mensagem": "Você não está cadastrado como estudante.",
            "vencido": True,
            "entidades": Entidade.objects.all(),
        }

    return render(request, "estudantes/informacoes_adicionais.html", context)


@login_required
def minhas_bancas(request):
    """Lista as bancas agendadas para um aluno."""
    configuracao = Configuracao.objects.get()
    if request.user.tipo_de_usuario == 1:
        if (request.user.aluno.anoPFE > configuracao.ano) or\
            (request.user.aluno.anoPFE == configuracao.ano and
            request.user.aluno.semestrePFE > configuracao.semestre):
            mensagem = "Projetos ainda não disponíveis para seu período PFE."
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        projetos = Projeto.objects.filter(alocacao__aluno=request.user.aluno)
        bancas = Banca.objects.filter(projeto__in=projetos).order_by("-startDate")
        context = {'bancas': bancas,}
    else:
        context = {'mensagem': "Você não está cadastrado como estudante.",}
    return render(request, 'estudantes/minhas_bancas.html', context)


@login_required
@transaction.atomic
def relato_quinzenal(request):
    """Perguntas aos estudantes de trabalho/entidades/social/familia."""
    v = usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    if v: return v  # Prof, Adm

    hoje = datetime.date.today()

    # (20, 'Relato quinzenal (Individual)', 'aquamarine'),
    prazo = Evento.objects.filter(tipo_de_evento=20, endDate__gte=hoje).order_by('endDate').first()

    context = {
        "prazo": prazo,
        "msg_relato_quinzenal": get_object_or_404(Carta, template="Mensagem de Relato Quinzenal").texto,
    }

    if request.user.tipo_de_usuario == 1:

        configuracao = get_object_or_404(Configuracao)

        alocacao = Alocacao.objects.filter(aluno=request.user.aluno,
                                           projeto__ano=configuracao.ano,
                                           projeto__semestre=configuracao.semestre).last()

        if not alocacao:
            context["prazo"] = None
            context["mensagem"] = "Você não está alocado em um projeto esse semestre."
            return render(request, "estudantes/relato_quinzenal.html", context)

        if request.method == "POST":
            texto_relato = request.POST.get("relato", None)
            relato = Relato.objects.create(alocacao=alocacao)
            relato.texto = texto_relato
            relato.save()
            return render(request, "users/atualizado.html",)

        relato_anterior = Evento.objects.filter(tipo_de_evento=20, endDate__lt=hoje).order_by("endDate").last()
        if not relato_anterior:
            return HttpResponseNotFound("<h1>Erro ao buscar prazos!</h1>")

        prazo_anterior = relato_anterior.endDate + datetime.timedelta(days=1)
        
        relato = Relato.objects.filter(alocacao=alocacao, momento__gt=prazo_anterior).order_by("momento").last()
        
        relatos = Relato.objects.filter(alocacao=alocacao).order_by("momento")
        context["relatos"] = relatos
        context["alocacao"] = alocacao
        context["relato"] = relato if relato else Relato

    else:  # Supostamente professores
        context["mensagem"] = "Você não está cadastrado como estudante."
        context["relato"] = Relato

    return render(request, "estudantes/relato_quinzenal.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def relato_visualizar(request, id):
    """Perguntas aos estudantes de trabalho/entidades/social/familia."""
    context = {"relato": get_object_or_404(Relato, pk=id),}
    return render(request, "estudantes/relato_visualizar.html", context)


def filtra_composicoes(composicoes, ano, semestre):
    """Filtra composições."""
    composicoes = composicoes.exclude(data_final__year__lt=ano)
    composicoes = composicoes.exclude(data_inicial__year__gt=ano)
    
    if semestre == 1:
        composicoes = composicoes.exclude(data_inicial__year=ano, data_final__month__gt=6)
    else:
        composicoes = composicoes.exclude(data_final__year=ano, data_final__month__lt=8)

    return composicoes


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def exames_pesos(request):
    """Submissão de documentos pelos estudantes."""
    
    semestres = {}
    semestres["2018.2"] = filtra_composicoes(Composicao.objects.all(), 2018, 2)
    for ano in range(2019, 2023):
        for semestre in range(1, 3):
            semestres[str(ano)+'.'+str(semestre)] = filtra_composicoes(Composicao.objects.all(), ano, semestre)

    context = {
        "semestres": semestres,
    }
    return render(request, 'academica/exames_pesos.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def submissao_documento(request):
    """Submissão de documentos pelos estudantes."""

    projeto = Projeto.objects.get(id=167)
    composicoes = filtra_composicoes(Composicao.objects.filter(entregavel=True), projeto.ano, projeto.semestre)
    
    itens = []
    for comp in composicoes:
        itens.append([comp.tipo_documento,
                      Documento.objects.filter(tipo_documento=comp.tipo_documento, projeto=projeto),

                      Evento.objects.filter(tipo_de_evento=comp.evento, 
                                            endDate__year=projeto.ano, endDate__month__lt=7).last()\
                      if projeto.semestre == 1 else \
                      Evento.objects.filter(tipo_de_evento=comp.evento, 
                                            endDate__year=projeto.ano, endDate__month__gt=6).last()])
        
    itens = sorted(itens, key=lambda t: (None if t[2] is None else t[2].endDate))

    context = {
        "projeto": projeto,
        "itens": itens,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, 'estudantes/submissao_documento.html', context)


@login_required
@transaction.atomic
def selecao_propostas(request):
    """Exibe todos os projetos para os estudantes aplicarem."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    min_props = configuracao.min_props

    liberadas_propostas = configuracao.liberadas_propostas

    # Vai para próximo semestre
    ano, semestre = adianta_semestre(ano, semestre)

    propostas = Proposta.objects\
        .filter(ano=ano)\
        .filter(semestre=semestre)\
        .filter(disponivel=True)

    warnings = ""

    vencido = True

    if request.user.tipo_de_usuario == 1:

        vencido = timezone.now().date() > get_limite_propostas(configuracao)

        aluno = request.user.aluno

        if configuracao.semestre == 1:
            vencido |= aluno.anoPFE < configuracao.ano
            vencido |= aluno.anoPFE == configuracao.ano and \
                aluno.semestrePFE == 1
        else:
            vencido |= aluno.anoPFE <= configuracao.ano

        if vencido:
            mensagem = "Prazo vencido para seleção de propostas de projetos!"
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
                if i < min_props+1 and list(prioridade.values()).count(str(i)) == 0:
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

                        else:
                            opcoes_tmp = Opcao.objects.filter(aluno=aluno, proposta=proposta)
                            if opcoes_tmp.count() > 1:  # Algum erro isso não deveria ter acontecido
                                opcoes_tmp.delete()  # apaga tudo e cria um novo
                                opc = Opcao.objects.create(aluno=aluno,
                                                           proposta=proposta,
                                                           prioridade=prio_int)
                                opc.save()
                            else:
                                opc = opcoes_tmp.last()
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

                context = {
                    'message': message,
                    "prazo": get_limite_propostas(configuracao),
                }
                return render(request, 'projetos/confirmacao.html', context)

            context = {
                'warnings': warnings,
            }
            return render(request, 'projetos/projetosincompleto.html', context)

        opcoes_temporarias = OpcaoTemporaria.objects.filter(aluno=aluno)

    elif request.user.tipo_de_usuario == 2 or request.user.tipo_de_usuario == 4:
        opcoes_temporarias = []

    v = usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    if v: return v  # Prof, Adm

    areas_normais = AreaDeInteresse.objects.filter(usuario=request.user, area__ativa=True).exists()
    areas_outras = AreaDeInteresse.objects.filter(usuario=request.user, area=None).exists()
    areas = areas_normais or areas_outras

    context = {
        'liberadas_propostas': liberadas_propostas,
        'vencido': vencido,
        'propostas': propostas,
        "min_props": min_props,
        'opcoes_temporarias': opcoes_temporarias,
        'ano': ano,
        'semestre': semestre,
        "prazo": get_limite_propostas(configuracao),
        "areas": areas,
        'warnings': warnings,
        "limite_propostas": get_limite_propostas(configuracao),
    }
    return render(request, 'estudantes/selecao_propostas.html', context)

@login_required
@transaction.atomic
def opcao_temporaria(request):
    """Ajax para definir opção temporária de seleção de proposta de projeto."""
    try:
        assert request.user.tipo_de_usuario == 1
        proposta_id = int(request.POST.get('proposta_id', None))
        prioridade = int(request.POST.get('prioridade', None))
        proposta = get_object_or_404(Proposta, id=proposta_id)
    except:
        return JsonResponse({'atualizado': False}, status=500)

    reg, _ = OpcaoTemporaria.objects.get_or_create(proposta=proposta, aluno=request.user.aluno)
    reg.prioridade = prioridade
    reg.save()

    return JsonResponse({'atualizado': True,})
