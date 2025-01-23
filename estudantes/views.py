"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

import datetime
import logging
import json

from hashids import Hashids

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from .models import Relato, Pares, EstiloComunicacao
from .support import cria_area_estudante, ver_pendencias_estudante
from .support2 import estudante_feedback_geral

from academica.models import Composicao
from academica.support import filtra_composicoes, filtra_entregas, get_respostas_estilos

from administracao.models import Carta, TipoEvento
from administracao.support import propostas_liberadas
from administracao.support import get_limite_propostas, get_limite_propostas2, usuario_sem_acesso

from projetos.models import Projeto, Proposta, Configuracao, Area, AreaDeInteresse
from projetos.models import Encontro, Banca, Entidade, Evento

from projetos.messages import email, message_agendamento, create_message, message_cancelamento

from users.models import PFEUser, Aluno, Alocacao, Opcao, OpcaoTemporaria
from users.models import UsuarioEstiloComunicacao
from users.support import configuracao_estudante_vencida, configuracao_pares_vencida, adianta_semestre
from users.support import adianta_semestre_conf


# Get an instance of a logger
logger = logging.getLogger("django")


@login_required
def index_estudantes(request):
    """Mostra página principal do usuário estudante."""
    configuracao = get_object_or_404(Configuracao)

    context = {
        "configuracao": configuracao,
        "liberadas_propostas": propostas_liberadas(configuracao),
        "vencido": timezone.now().date() > get_limite_propostas(configuracao)
    }

    ano = configuracao.ano
    semestre = configuracao.semestre

    # Caso estudante
    if request.user.tipo_de_usuario == 1:

        projeto = Projeto.objects.filter(alocacao__aluno=request.user.aluno).last()
        context["projeto"] = projeto

        # Estudantes de processos passados sempre terrão seleção vencida
        if request.user.aluno.anoPFE and request.user.aluno.semestrePFE:
            if semestre == 1:
                context["vencido"] |= request.user.aluno.anoPFE < ano
                context["vencido"] |= request.user.aluno.anoPFE == ano and \
                    request.user.aluno.semestrePFE == 1
            else:
                context["vencido"] |= (request.user.aluno.anoPFE <= ano)
        else:
            context["vencido"] = True

        if projeto:
            evento_banca_final = Evento.get_evento(nome="Bancas Finais", ano=projeto.ano, semestre=projeto.semestre)
            if evento_banca_final:
                hoje = datetime.date.today()
                context["fase_final"] = hoje > evento_banca_final.endDate

        # Avaliações de Pares
        context["fora_fase_feedback_intermediario"], _, _ = configuracao_pares_vencida(request.user.aluno, "API") # Avaliação de Pares Intermediária
        context["fora_fase_feedback_final"], _, _ = configuracao_pares_vencida(request.user.aluno, "APF") # Avaliação de Pares Final

        # Só verifica se está no semestre corrente
        if request.user.aluno.anoPFE == configuracao.ano and request.user.aluno.semestrePFE == configuracao.semestre:
            context_pend = ver_pendencias_estudante(request.user, configuracao.ano, configuracao.semestre)
            context.update(context_pend)

    # Caso professor ou administrador
    elif request.user.tipo_de_usuario in (2, 4):
        context["fase_final"] = True

    else:  # Caso parceiro
        return HttpResponse("Usuário sem acesso.", status=401)

    context["ano"], context["semestre"] = adianta_semestre(ano, semestre)

    #get_limite_propostas2 return None caso não haja limite
    context["limite_propostas"] = get_limite_propostas2(configuracao)

    tenevento = TipoEvento.objects.get(nome="Apresentação das propostas disponíveis para estudantes")
    context["liberacao_visualizacao"] = Evento.objects.filter(tipo_evento=tenevento).last().startDate
    context["titulo"] = {"pt": "Área dos Estudantes", "en": "Students Area"}

    if "/estudantes/estudantes" in request.path:
        return render(request, "estudantes/estudantes.html", context=context)
    else:
        return render(request, "estudantes/index_estudantes.html", context=context)
    

@login_required
def alinhamentos_gerais(request):
    """Para passar links de alinhamentos gerais de início de semestre."""
    context = {"titulo": {"pt": "Alinhamentos Gerais", "en": "General Alignments"},}
    return render(request, "estudantes/alinhamentos_gerais.html", context)

@login_required
def alocacao_semanal(request):
    """Para passar links de alinhamentos gerais de início de semestre."""
    configuracao = get_object_or_404(Configuracao)
    if request.user.tipo_de_usuario == 1:  # Estudante
        projeto = Projeto.objects.filter(alocacao__aluno=request.user.aluno, ano=configuracao.ano , semestre=configuracao.semestre).last()
        if not projeto:
            mensagem = "Você não está alocado em um projeto esse semestre."
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)
    elif request.user.tipo_de_usuario in (2, 4):
        projeto = Projeto.objects.filter(orientador=request.user.professor, ano=configuracao.ano , semestre=configuracao.semestre).last()
    else:
        mensagem = "Você não possui conta de estudante."
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)
    
    horarios = json.loads(configuracao.horarios_semanais) if configuracao.horarios_semanais else None
    
    context = {
        "titulo": {"pt": "Alocação Semanal", "en": "Weekly Allocation"},
        "projeto": projeto,
        "horarios": horarios,
    }
    return render(request, "estudantes/alocacao_semanal.html", context)

@login_required
def alocacao_hora(request):
    """Ajax para definir horarios dos estudantes."""
    if request.user.tipo_de_usuario == 1:
        configuracao = get_object_or_404(Configuracao)
        alocacao = Alocacao.objects.filter(aluno=request.user.aluno, projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre).last()
        alocacao.horarios = json.loads(request.POST.get("horarios", None))
        alocacao.save()
    else:
        return JsonResponse({"atualizado": False}, status=500)
    return JsonResponse({"atualizado": True,})

@login_required
def refresh_hora(request):
    """Ajax para definir horarios dos estudantes."""
    if request.user.tipo_de_usuario == 3:
        return HttpResponse("Você não possui acesso.", status=401)
    
    projeto_id = request.GET.get("projeto_id", None)
    projeto = get_object_or_404(Projeto, pk=projeto_id)

    alocacoes = Alocacao.objects.filter(projeto=projeto)
    if not alocacoes:
        return HttpResponse("Alocações não encontrada.", status=404)

    todos_horarios = {alocacao.id: alocacao.horarios for alocacao in alocacoes}
    return JsonResponse({"todos_horarios": todos_horarios})


@login_required
@transaction.atomic
def encontros_marcar(request):
    """Encontros a serem agendados pelos estudantes."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    aviso = None  # Mensagem de aviso caso algum problema

    hoje = datetime.date.today()
    encontros = Encontro.objects.filter(startDate__gt=hoje).order_by("startDate")

    if request.user.tipo_de_usuario == 1:  # Estudante
        projeto = Projeto.objects.filter(alocacao__aluno=request.user.aluno, ano=ano, semestre=semestre).last()

    # caso Professor ou Administrador
    elif request.user.tipo_de_usuario in (2, 4):
        projeto = None
    else:
        return HttpResponse("Você não possui conta de estudante.", status=401)

    if request.method == "POST":
        check_values = request.POST.getlist("selection")
        
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
            subject = "Capstone | Dinâmica agendada"
            recipient_list = []
            alocacoes = Alocacao.objects.filter(projeto=projeto)
            for alocacao in alocacoes:
                # mandar para cada membro do grupo
                recipient_list.append(alocacao.aluno.user.email)
            
            # coordenadoção
            recipient_list.append(str(configuracao.coordenacao.user.email))

            message = message_agendamento(agendado, cancelado)
            email(subject, recipient_list, message)
            horario = "dia " + str(agendado.startDate.strftime("%d/%m/%Y")) + " das " + str(agendado.startDate.strftime("%H:%M")) + ' às ' + str(agendado.endDate.strftime("%H:%M"))
            mensagem = "Dinâmica agendada: " + horario

            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

        if not aviso:
            return HttpResponse("Problema! Por favor reportar.")

    agendado = encontros.filter(projeto=projeto).last()

    context = {
        "titulo": {"pt": "Agendar Mentorias", "en": "Schedule Mentoring"},
        "encontros": encontros,
        "projeto": projeto,
        "aviso": aviso,
        "agendado": agendado,
    }
    return render(request, "estudantes/encontros_marcar.html", context)


@login_required
@transaction.atomic
def encontros_cancelar(request, evento_id):
    """Cancela encontro agendado por estudantes."""
    configuracao = get_object_or_404(Configuracao)

    if request.user.tipo_de_usuario == 1:  # Estudante
        projeto = Projeto.objects.filter(alocacao__aluno=request.user.aluno).\
            distinct().filter(ano=configuracao.ano).\
            filter(semestre=configuracao.semestre).last()
    else:
        return HttpResponse("Você não possui conta de estudante.", status=401)

    encontro = get_object_or_404(Encontro, pk=evento_id, projeto=projeto)
    
    subject = "Capstone | Dinâmica cancelada"
    recipient_list = []
    alocacoes = Alocacao.objects.filter(projeto=projeto)
    for alocacao in alocacoes:
        recipient_list.append(alocacao.aluno.user.email)
    
    # coordenadoção
    recipient_list.append(str(configuracao.coordenacao.user.email))

    message = message_cancelamento(encontro)
    email(subject, recipient_list, message)
    encontro.projeto = None
    encontro.save()

    horario = "dia " + str(encontro.startDate.strftime("%d/%m/%Y")) + " das " + str(encontro.startDate.strftime("%H:%M")) + ' às ' + str(encontro.endDate.strftime("%H:%M"))
    mensagem = "Mentoria/Dinâmica cancelada: " + horario
    
    context = {
        "area_principal": True,
        "mensagem": mensagem,
    }
    return render(request, "generic.html", context=context)


@login_required
def estilo_comunicacao(request):
    """Para passar links de alinhamentos gerais de início de semestre."""

    if request.method == "POST":
        for estilo in EstiloComunicacao.objects.all():

            if all(f"prioridade_resposta{i}_{estilo.id}" in request.POST for i in range(1, 5)):
                prioridade_resposta1 = request.POST.get(f"prioridade_resposta1_{estilo.id}")
                prioridade_resposta2 = request.POST.get(f"prioridade_resposta2_{estilo.id}")
                prioridade_resposta3 = request.POST.get(f"prioridade_resposta3_{estilo.id}")
                prioridade_resposta4 = request.POST.get(f"prioridade_resposta4_{estilo.id}")

                usuario_estilo, created = UsuarioEstiloComunicacao.objects.update_or_create(
                    usuario=request.user,
                    estilo_comunicacao=estilo,
                    defaults={
                        "prioridade_resposta1": prioridade_resposta1,
                        "prioridade_resposta2": prioridade_resposta2,
                        "prioridade_resposta3": prioridade_resposta3,
                        "prioridade_resposta4": prioridade_resposta4,
                    }
                )

        respostas = get_respostas_estilos(request.user)
        if respostas:

            mensagem = "Opções submetidas com sucesso!<br>"
            mensagem_resposta = "<br><h4>Tabela de Estilo de Comunicação</h4>"
            mensagem_resposta += "<br><b>Respostas:</b>"
            for key, value in respostas.items():
                mensagem_resposta += f"<br>&nbsp;&nbsp;&nbsp;&nbsp;{key}: {value}"

            subject = "Capstone | Estilo de Comunicação"
            recipient_list = [request.user.email, ]
            email(subject, recipient_list, mensagem_resposta)
            mensagem += mensagem_resposta

        else:
            mensagem = "Erro na submissão das opções."


        context = {
            "voltar": True,
            "area_principal": True,
            "mensagem": mensagem,
        }

        return render(request, "generic.html", context=context)

    texto_estilo = {
        "pt": """
            Para cada um dos blocos, ordene na coluna de respostas as afirmações especificadas na coluna pergunta.<br>
            Para isso considere a sua autoperpção em relação a cada afirmação. <br>
            Mova para a parte superior a afirmacao que mais te representa e para a parte inferior a que menos te representa.<br>
            Lembre-se que este assessment é confidencial e particular, portanto foque em responder de forma sincera e honesta.<br>
            Ao concluir, você receberá um relatório com os resultados por e-mail.<br>
            Leve para a aula o seu resultado.<br>""",
                "en": """
            For each block, order in the answers column the statements specified in the question column.<br>
            Consider your self-perception in relation to each statement. <br>
            Move to the top the statement that best represents you and to the bottom the one that least represents you.<br>
            Remember that this assessment is confidential and private, so focus on answering sincerely and honestly.<br>
            Upon completion, you will receive a report with the results by email.<br>
            Take your result to class.<br>""",
        }
    
    context = {
        "titulo": {"pt": "Estilo de Comunicação", "en": "Communication Style"},
        "estilos": EstiloComunicacao.objects.all(),
        "texto_estilo": texto_estilo,
    }

    return render(request, "estudantes/estilo_comunicacao.html", context)


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
        return HttpResponseNotFound("<h1>Usuário não encontrado!</h1>")


@login_required
@transaction.atomic
def avaliacao_pares(request, momento):
    """Permite realizar a avaliação de pares."""
    usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    configuracao = get_object_or_404(Configuracao)

    estudante = request.user.aluno if request.user.tipo_de_usuario == 1 else None

    if momento=="intermediaria":
        prazo, inicio, fim = configuracao_pares_vencida(estudante, "API")  # Avaliação de Pares Intermediária
        tipo=0
    else:  # Final
        prazo, inicio, fim = configuracao_pares_vencida(estudante, "APF")  # Avaliação de Pares Final
        tipo=1

    context = {
            "titulo": {"pt": "Avaliação de Pares" + (" Intermediária" if momento=="intermediaria" else " Final"), 
                       "en": (" Intermediate" if momento=="intermediaria" else " Final") + " Peer Evaluation"},
        }

    if request.user.tipo_de_usuario == 1:
        projeto = Projeto.objects\
            .filter(alocacao__aluno=estudante, ano=configuracao.ano, semestre=configuracao.semestre).first()
        
        if not projeto:
            mensagem = "Você não está alocao em um projeto esse semestre!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

        alocacao_de = Alocacao.objects.get(projeto=projeto, aluno=estudante)
        alocacoes = Alocacao.objects.filter(projeto=projeto).exclude(aluno=estudante)

        if (not prazo) and request.method == "POST":

            for alocacao in alocacoes:

                (par, _created) = Pares.objects.get_or_create(alocacao_de=alocacao_de,
                                                                alocacao_para=alocacao,
                                                                tipo=tipo)

                if _created:
                    par.alocacao_de = alocacao_de
                    par.alocacao_para = alocacao
                    par.tipo=tipo

                par.aprecia = request.POST.get("aprecia"+str(alocacao.id), None)
                par.atrapalhando = request.POST.get("atrapalhando"+str(alocacao.id), None)
                par.mudar = request.POST.get("mudar"+str(alocacao.id), None)

                entrega = request.POST.get("entrega"+str(alocacao.id), None)
                if entrega:
                    par.entrega = int(entrega)

                iniciativa = request.POST.get("iniciativa"+str(alocacao.id), None)
                if iniciativa:
                    par.iniciativa = int(iniciativa)

                comunicacao = request.POST.get("comunicacao"+str(alocacao.id), None)
                if comunicacao:
                    par.comunicacao = int(comunicacao)

                par.save()

            alocacoes_so_Insper = Alocacao.objects.filter(projeto=projeto, aluno__externo__isnull=True)
            alocacoes_ids = list(alocacoes_so_Insper.values_list("id", flat=True))
            count_pares = Pares.objects.filter(alocacao_de__id__in=alocacoes_ids, alocacao_para__id__in=alocacoes_ids, tipo=tipo).count()
            tot_est = len(alocacoes_ids)
            if count_pares == tot_est*(tot_est-1):
                if projeto and projeto.organizacao and projeto.orientador:
                    subject = "Capstone | Avaliação de Pares " + ("Intermediária" if momento=="intermediaria" else "Final")
                    subject += " - [" + projeto.organizacao.sigla + "] " + projeto.get_titulo()
                    
                    recipient_list = [projeto.orientador.user.email]
                    
                    message = "Caro Orientador(a),<br><br>"
                    message += "Todas as avaliações de pares " + ("intermediárias" if momento=="intermediaria" else "finais")
                    message += " do projeto que você está orientando<br>"
                    message += "<b>[" + projeto.organizacao.sigla + "] " + projeto.get_titulo() + "</b><br>"
                    message += "foram realizadas.<br><br>"
                    message += "Acesse o sistema para visualizar as avaliações.<br>"
                    message += "<a href='https://pfe.insper.edu.br/professores/avaliacoes_pares/'>https://pfe.insper.edu.br/professores/avaliacoes_pares/</a><br><br>"
                    
                    email(subject, recipient_list, message)

            return render(request, "users/atualizado.html",)
        
        pares = []
        for alocacao in alocacoes:
            par = Pares.objects.filter(alocacao_de=alocacao_de, alocacao_para=alocacao, tipo=tipo).first()
            pares.append(par)

        colegas = zip(alocacoes, pares)
        context["colegas"] = colegas

    else:  # Supostamente professores
        context["mensagem_aviso"] = "Você não está cadastrado como estudante."
        context["colegas"] = [[{"aluno":"Fulano (exemplo)",id:0},None],[{"aluno":"Beltrano (exemplo)",id:0},None]],

    context["vencido"] = prazo
    context["momento"] = momento
    context["inicio"] = inicio
    context["fim"] = fim
    context["configuracao"] = configuracao

    context["TIPO_ENTREGA"] = Pares.TIPO_ENTREGA
    context["TIPO_INICIATIVA"] = Pares.TIPO_INICIATIVA
    context["TIPO_COMUNICACAO"] = Pares.TIPO_COMUNICACAO

    return render(request, "estudantes/avaliacao_pares.html", context)


@login_required
@transaction.atomic
def informacoes_adicionais(request):
    """Perguntas aos estudantes de áreas de interesse, trabalho/entidades/social/familia, telefone."""
    usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    
    if request.user.tipo_de_usuario == 1:

        estudante = request.user.aluno

        vencido = configuracao_estudante_vencida(request.user.aluno)

        if (not vencido) and request.method == "POST":

            cria_area_estudante(request, request.user.aluno)

            request.user.aluno.trabalhou = request.POST.get("trabalhou", None)
            request.user.aluno.social = request.POST.get("social", None)
            request.user.aluno.entidade = request.POST.get("entidade", None)
            request.user.aluno.familia = request.POST.get("familia", None)

            link = request.POST.get("linkedin", "").strip()
            if not (link and link != ""):
                link = None
            if link:
                if link[:4] != "http":
                    link = "https://" + link

                max_length = PFEUser._meta.get_field("linkedin").max_length
                if len(link) > max_length:
                    raise ValidationError("<h1>Erro: link do LinkedIn informado maior que " + str(max_length) + " caracteres.</h1>")

            request.user.linkedin = link

            request.user.celular = request.POST.get("celular", None)

            request.user.save()
            request.user.aluno.save()
            return render(request, "users/atualizado.html",)

        context = {
            "vencido": vencido,
            "estudante": estudante,
        }
    else:  # Supostamente professores
        context = {
            "mensagem_aviso": "Você não está cadastrado como estudante.",
            "vencido": True,
        }
    
    context["entidades"] = Entidade.objects.all()
    context["areast"] = Area.objects.filter(ativa=True)
    context["Aluno"] = Aluno
    context["PFEUser"] = PFEUser
    context["titulo"] = {"pt": "Interesses e Experiências", "en": "Interests and Experiences"}

    return render(request, "estudantes/informacoes_adicionais.html", context)


@login_required
def minhas_bancas(request):
    """Lista as bancas agendadas para um aluno."""
    configuracao = Configuracao.objects.get()
    context = {"titulo": {"pt": "Minhas Bancas", "en": "My Examining Boards"},}
    if request.user.tipo_de_usuario == 1:
        if (request.user.aluno.anoPFE > configuracao.ano) or\
            (request.user.aluno.anoPFE == configuracao.ano and
            request.user.aluno.semestrePFE > configuracao.semestre):
            mensagem = "Fora do período de avaliação de bancas."
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

        alocacao = Alocacao.objects.filter(aluno=request.user.aluno,
                                           projeto__ano=configuracao.ano,
                                           projeto__semestre=configuracao.semestre).last()
        
        if not alocacao:
            mensagem = "Você não está alocado em um projeto esse semestre."
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)
        
        # Banca do projeto (grupo, não probation)
        bancag = Banca.objects.filter(projeto=alocacao.projeto).order_by("-startDate")

        # Banca do aluno (probation)
        bancai = Banca.objects.filter(alocacao=alocacao).order_by("-startDate")
        
        context["bancas"] =  bancag | bancai
    else:
        context["mensagem_aviso"] = "Você não está cadastrado como estudante."
    return render(request, "estudantes/minhas_bancas.html", context)


@login_required
@transaction.atomic
def relato_quinzenal(request):
    """Perguntas aos estudantes de trabalho/entidades/social/familia."""
    usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    configuracao = get_object_or_404(Configuracao)
    hoje = datetime.date.today()
    tevento = TipoEvento.objects.get(nome="Relato quinzenal (Individual)")
    prazo = Evento.objects.filter(tipo_evento=tevento, endDate__gte=hoje).order_by("endDate").first()

    if prazo:
        # Só mostra o relato N (config.periodo_relato) dias antes do prazo
        fora_periodo = prazo.endDate - hoje > datetime.timedelta(days=configuracao.periodo_relato)
        inicio_periodo = prazo.endDate - datetime.timedelta(days=configuracao.periodo_relato)
    else:
        fora_periodo = True
        inicio_periodo = None

    context = {
        "titulo": {"pt": "Formulário de Relato Quinzenal", "en": "Biweekly Report Form"},
        "prazo": prazo,
        "msg_relato_quinzenal": get_object_or_404(Carta, template="Mensagem de Relato Quinzenal").texto,
        "Relato": Relato,
        "fora_periodo": fora_periodo,
        "inicio_periodo": inicio_periodo,
    }

    if request.user.estud:  # Estudante

        alocacao = Alocacao.objects.filter(aluno=request.user.aluno,
                                           projeto__ano=configuracao.ano,
                                           projeto__semestre=configuracao.semestre).last()

        if not alocacao:
            context["prazo"] = None
            context["mensagem_aviso"] = "Você não está alocado em um projeto esse semestre."

            return render(request, "estudantes/relato_quinzenal.html", context)

        if request.method == "POST":

            # Só mostra o relato N (config.periodo_relato) dias antes do prazo
            if fora_periodo:
                return HttpResponseNotFound("<h1>Relato quinzenal não disponível!</h1>")

            texto_relato = request.POST.get("relato", None)
            relato = Relato.objects.create(alocacao=alocacao)
            relato.texto = texto_relato
            relato.save()
            
            if prazo:
                mensagem = "<h5>Relato submetido com sucesso<br><br></h5>"
            else:
                mensagem = "<h1 style='color: red;'>Erro na submissão do Relato<br>"
                mensagem += "Não foi encontrado um prazo de entrega válido para o relato.</h1>"

            mensagem += "<div style='max-width: 1400px; border: 1px solid black; padding: 4px;'>"
            mensagem += "<b>Horário de recebimento:</b> " + relato.momento.strftime('%d/%m/%Y, %H:%M:%S') + "<br><hr>"
            mensagem += "<b>Relato:</b> " + texto_relato.replace('\n', "<br>\n") + "<br>"
            mensagem += "</div>"

            context = {
                "area_aluno": True,
                "area_principal": True,
                "voltar": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

        tevento = TipoEvento.objects.get(nome="Relato quinzenal (Individual)")
        relato_anterior = Evento.objects.filter(tipo_evento=tevento, endDate__lt=hoje).order_by("endDate").last()
        
        if not relato_anterior:
            return HttpResponseNotFound("<h1>Erro ao buscar prazos!</h1>")

        prazo_anterior = relato_anterior.endDate + datetime.timedelta(days=1)
        
        context["relatos"] = Relato.objects.filter(alocacao=alocacao).order_by("-momento")
        context["alocacao"] = alocacao
        context["texto_relato"] = Relato.objects.filter(alocacao=alocacao, momento__gt=prazo_anterior).order_by("momento").last()

    else:  # Supostamente professores
        context["mensagem_aviso"] = "Você não está cadastrado como estudante."

    return render(request, "estudantes/relato_quinzenal.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def relato_visualizar(request, id):
    """Perguntas aos estudantes de trabalho/entidades/social/familia."""
    context = {
        "titulo": {"pt": "Visualização de Relato Quinzenal", "en": "Biweekly Report Visualization"},
        "relato": get_object_or_404(Relato, pk=id),
        }
    return render(request, "estudantes/relato_visualizar.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def exames_pesos(request):
    """Exibe os exames e pessos por semestre."""
    configuracao = get_object_or_404(Configuracao)
    semestres = []
    semestres.append(["2018", "2", filtra_composicoes(Composicao.objects.all(), 2018, 2)])
    for ano in range(2019, configuracao.ano+2):
        for semestre in range(1, 3):
            semestres.append([str(ano), str(semestre), filtra_composicoes(Composicao.objects.all(), ano, semestre)])

    cabecalhos = [
        {"pt": "Semestre", "en": "Semester", "tsort": "1"},
        {"pt": "Exames", "en": "Evaluation"},
        {"pt": "Peso", "en": "Weight", "esconder": True},
    ]

    context = {
        "titulo": {"pt": "Exames e Pesos", "en": "Exams and Weights"},
        "semestres": semestres,
        "cabecalhos": cabecalhos,
    }

    return render(request, "academica/exames_pesos.html", context)


@login_required
def submissao_documento(request):
    """Submissão de documentos pelos estudantes."""

    configuracao = get_object_or_404(Configuracao)

    context = {"titulo": {"pt": "Submissão de Documentos", "en": "Document Submission"},}

    if request.user.tipo_de_usuario != 1:  # Não é Estudante
         if request.user.tipo_de_usuario == 2 or request.user.tipo_de_usuario == 4:  # Professor
            projeto = Projeto.objects.filter(orientador=request.user.professor).last()
            context["mensagem_aviso"] = "Professor, esse é somente um exemplo do que os estudantes visualizam. Não envie documentos por essa página."
    else:
        alocacao = Alocacao.objects.filter(aluno=request.user.aluno, projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre).last()
        projeto = alocacao.projeto if alocacao else None
        
    if not projeto:
        return HttpResponse("Você não está alocado em um projeto esse semestre.", status=401)

    composicoes = filtra_composicoes(Composicao.objects.filter(entregavel=True), projeto.ano, projeto.semestre)
    entregas = filtra_entregas(composicoes, projeto, request.user)

    context["projeto"] = projeto
    context["entregas"] = entregas

    return render(request, "estudantes/submissao_documento.html", context)


@login_required
@transaction.atomic
def selecao_propostas(request):
    """Exibe todos os projetos para os estudantes aplicarem."""
    configuracao = get_object_or_404(Configuracao)

    min_props = configuracao.min_props

    liberadas_propostas = propostas_liberadas(configuracao)
    ano, semestre = adianta_semestre_conf(configuracao)

    propostas = Proposta.objects.filter(ano=ano, semestre=semestre, disponivel=True)

    warnings = ""

    vencido = True

    if request.user.tipo_de_usuario == 1:

        vencido = timezone.now().date() > get_limite_propostas(configuracao)

        aluno = request.user.aluno

        if configuracao.semestre == 1:
            vencido |= aluno.anoPFE < configuracao.ano
            vencido |= aluno.anoPFE == configuracao.ano and aluno.semestrePFE == 1
        else:
            vencido |= aluno.anoPFE <= configuracao.ano

        if vencido:
            mensagem = "Prazo vencido para seleção de propostas de projetos!"
            context = {
                "area_aluno": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

        if liberadas_propostas and request.method == "POST":
            prioridade = {}
            for proposta in propostas:
                check_values = request.POST.get("selection"+str(proposta.pk), "0")
                prioridade[proposta.pk] = check_values
            for i in range(1, len(propostas)+1):
                if i < min_props+1 and list(prioridade.values()).count(str(i)) == 0:
                    warnings += "Nenhuma proposta com prioridade " + str(i) + "\n"
                if list(prioridade.values()).count(str(i)) > 1:
                    warnings += "Mais de uma proposta com prioridade " + str(i) + "\n"
            if warnings == "":  # Submissão Completa
                for proposta in propostas:
                    if prioridade[proposta.pk] != "0":
                        prio_int = int(prioridade[proposta.pk])
                        # Se lista for vazia
                        if not aluno.opcoes.filter(pk=proposta.pk):
                            Opcao.objects.create(aluno=aluno, proposta=proposta, prioridade=prio_int)
                        else:
                            opcoes_tmp = Opcao.objects.filter(aluno=aluno, proposta=proposta)
                            if opcoes_tmp.count() > 1:  # Algum erro isso não deveria ter acontecido
                                opcoes_tmp.delete()  # apaga tudo e cria um novo
                                opc = Opcao.objects.create(aluno=aluno, proposta=proposta, prioridade=prio_int)
                                opc.save()
                            else:
                                opc = opcoes_tmp.last()
                                opc.prioridade = prio_int
                                opc.save()

                    else:  # Se lista não for vazia

                        if aluno.opcoes.filter(pk=proposta.pk):
                            Opcao.objects.filter(aluno=aluno, proposta=proposta).delete()
                message = create_message(aluno, ano, semestre)

                subject = "Capstone | Propostas Selecionadas: " + aluno.user.username
                recipient_list = [aluno.user.email, ]
                email(subject, recipient_list, message)

                context = {
                    "message": message,
                    "prazo": get_limite_propostas(configuracao),
                }
                return render(request, "projetos/confirmacao.html", context)

            context = {
                "warnings": warnings,
            }
            return render(request, "projetos/projetosincompleto.html", context)

        opcoes_t = OpcaoTemporaria.objects.filter(aluno=aluno)
        opcoes_temporarias = { opcao.proposta.id: opcao.prioridade for opcao in opcoes_t }

    elif request.user.tipo_de_usuario == 2 or request.user.tipo_de_usuario == 4:
        opcoes_temporarias = {}

    usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    
    areas_normais = AreaDeInteresse.objects.filter(usuario=request.user, area__ativa=True).exists()
    areas_outras = AreaDeInteresse.objects.filter(usuario=request.user, area=None).exists()
    areas = areas_normais or areas_outras

    context = {
        "titulo": {"pt": "Seleção de Propostas de Projetos", "en": "Project Proposal Selection"},
        "liberadas_propostas": liberadas_propostas,
        "vencido": vencido,
        "propostas": propostas,
        "min_props": min_props,
        "opcoes_temporarias": opcoes_temporarias,
        "ano": ano,
        "semestre": semestre,
        "prazo": get_limite_propostas(configuracao),
        "areas": areas,
        "warnings": warnings,
        "limite_propostas": get_limite_propostas(configuracao),
    }
    return render(request, "estudantes/selecao_propostas.html", context)

@login_required
@transaction.atomic
def opcao_temporaria(request):
    """Ajax para definir opção temporária de seleção de proposta de projeto."""
    try:
        assert request.user.tipo_de_usuario == 1
        proposta_id = int(request.POST.get("proposta_id", None))
        prioridade = int(request.POST.get("prioridade", None))
        proposta = get_object_or_404(Proposta, id=proposta_id)
    except:
        return JsonResponse({"atualizado": False}, status=500)

    if prioridade == 0:
        regs = OpcaoTemporaria.objects.filter(proposta=proposta, aluno=request.user.aluno)
        for reg in regs:
            reg.delete()
    else:    
        reg, _ = OpcaoTemporaria.objects.get_or_create(proposta=proposta, aluno=request.user.aluno)
        reg.prioridade = prioridade
        reg.save()

    return JsonResponse({"atualizado": True,})
