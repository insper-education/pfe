#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import datetime
import dateutil.parser
import logging

from django.conf import settings
from django.db.models import Q
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404
from django.http import Http404

from .support2 import calcula_media_notas_bancas, calcula_notas_bancas

from academica.models import Exame, Composicao
from academica.support import filtra_composicoes, filtra_entregas

from documentos.models import TipoDocumento

from estudantes.models import Pares

from projetos.messages import email, render_message
from projetos.models import Organizacao, Projeto, Banca, Encontro
from projetos.models import ObjetivosDeAprendizagem, Avaliacao2, Observacao
from projetos.models import Avaliacao_Velha, Observacao_Velha
from projetos.models import Configuracao, Documento, Evento
from projetos.support2 import busca_relatos

from users.models import PFEUser, Professor, Aluno, Alocacao
from users.support import adianta_semestre, ordena_nomes


logger = logging.getLogger("django")  # Para marcar mensagens de log

def calcula_interseccao_bancas(banca, startDate, endDate):
    """Calcula se a banca intersecta com outras bancas (e trata se for criada ou editada)."""
    configuracao = get_object_or_404(Configuracao)
    intersecta = 0

    intersectadas = Banca.objects.filter(Q(endDate__gt=startDate) & Q(startDate__lt=endDate))
    if banca is not None:                
        # Pega todas as bancas que intersectam com o período informado
        intersectadas = intersectadas.exclude(id=banca.id)

    # Verifica entre as bancas intersectadas se elas também se intersectam
    for intersectada in intersectadas:
        b_start = Banca.objects.filter(Q(endDate__gt=intersectada.startDate) & Q(startDate__lte=intersectada.startDate))
        b_end = Banca.objects.filter(Q(endDate__gt=intersectada.endDate) & Q(startDate__lte=intersectada.endDate))
        if banca:
            b_start = b_start.exclude(id=banca.id)
            b_end = b_end.exclude(id=banca.id)
        intersecta = max(intersecta, b_start.count(), b_end.count())

    return intersecta >= configuracao.limite_salas_bancas


def editar_banca(banca, request):
    """Edita os valores de uma banca por um request Http."""

    if request.user.tipo_de_usuario != 4:  # Caso não Administrador
        # Verifica se a banca não intersecta com outras bancas
        if "inicio" in request.POST and "fim" in request.POST:
            startDate = dateutil.parser.parse(request.POST["inicio"])
            endDate = dateutil.parser.parse(request.POST["fim"])
            if calcula_interseccao_bancas(banca, startDate, endDate):
                return "Mais de duas bancas agendadas para o mesmo horário! Agendamento não realizado.", None
        else:
            return "Data de início ou fim não informada!", None

    if banca is None:
        banca = Banca()

    if "tipo" in request.POST and request.POST["tipo"] != "":
        exame = get_object_or_404(Exame, sigla=request.POST["tipo"])
        composicao = Composicao.objects.filter(exame=exame, data_inicial__lte=banca.startDate).order_by("-data_inicial").first()
        banca.composicao = composicao
    else:
        return "Tipo de banca não informado!", None
    
    if banca.alocacao:  # Banca Probation      
        try:
            banca.alocacao = Alocacao.objects.get(id=int(request.POST.get("alocacao")))
        except Alocacao.DoesNotExist:
            return "Alocação não encontrada!", None
    else:
        try:
            banca.projeto = Projeto.objects.get(id=int(request.POST.get("projeto")))
        except Projeto.DoesNotExist:
            return "Projeto não encontrado!", None
    
    try:
        banca.startDate = dateutil.parser.parse(request.POST.get("inicio"))
    except (ValueError, OverflowError):
        banca.startDate = None
    try:
        banca.endDate = dateutil.parser.parse(request.POST.get("fim"))
    except (ValueError, OverflowError):
        banca.endDate = None

    banca.location = request.POST.get("local")
    banca.link = request.POST.get("link")

    try:
        if "membro1" in request.POST and request.POST["membro1"].isnumeric():
            banca.membro1 = PFEUser.objects.get(id=int(request.POST["membro1"]))
        else:
            banca.membro1 = None
        if "membro2" in request.POST and request.POST["membro2"].isnumeric():
            banca.membro2 = PFEUser.objects.get(id=int(request.POST["membro2"]))
        else:
            banca.membro2 = None
        if "membro3" in request.POST and request.POST["membro3"].isnumeric():
            banca.membro3 = PFEUser.objects.get(id=int(request.POST["membro3"]))
        else:
            banca.membro3 = None
    except PFEUser.DoesNotExist:
        return "Membro da banca não encontrado!", None

    banca.save()

    return None, banca


def coleta_membros_banca(banca=None):
    # Se banca informada, retorna todas as pessoas para a Banca e os membros da banca
    # senão retorna todos os professores e todos os falconis
    sigla = banca.composicao.exame.sigla if banca else None
    id_membros = []

    if (banca is None) or sigla in ["BF", "BI", "P"]:  # Banca Final, Intermediária e Probation
        academicos = PFEUser.objects.filter(tipo_de_usuario__in=[2, 4])

    if (banca is None) or sigla == "F":  # Banca Falconi
        try:
            organizacao = Organizacao.objects.get(sigla="Falconi")
            falconis = PFEUser.objects.filter(parceiro__organizacao=organizacao)
        except Organizacao.DoesNotExist:
            raise Http404("Organização Falconi não encontrada!")

    if banca:
        id_membros.extend(membro.id for membro in banca.membros())
        if sigla == "F":    
            pessoas = ordena_nomes(falconis)
            membros = ordena_nomes(falconis.filter(pk__in=id_membros))
        else:
            pessoas = ordena_nomes(academicos)
            membros = ordena_nomes(academicos.filter(pk__in=id_membros))
        return pessoas, membros
    else:
        academicos = ordena_nomes(academicos)
        falconis = ordena_nomes(falconis)
        return academicos, falconis


def recupera_orientadores_por_semestre(configuracao):
    """Recupera listas de orientadores de projetos ordenadas por semestre."""
    professores_pfe = []
    periodo = []

    ano = 2018    # Ano de início do programa
    semestre = 2  # Semestre de início do programa
    while True:
        professores = []
        grupos = []
        for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                          Lower("user__last_name")):
            count_grupos = []
            grupos_pfe = Projeto.objects.filter(orientador=professor, ano=ano, semestre=semestre)
            if grupos_pfe:
                for grupo in grupos_pfe:  # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe:
                        count_grupos.append(grupo)
                if count_grupos:
                    professores.append(professor)
                    grupos.append(count_grupos)

        if professores:  # Se não houver nenhum orientador não cria entrada na lista
            professores_pfe.append(zip(professores, grupos))
            periodo.append(str(ano)+"."+str(semestre))

        # Para de buscar depois do semestre atual
        if ((semestre == configuracao.semestre + 1) and (ano == configuracao.ano)) or \
           (ano > configuracao.ano):
            break

        # Avança um semestre
        ano, semestre = adianta_semestre(ano, semestre)

    return zip(professores_pfe[::-1], periodo[::-1])  # inverti lista deixando os mais novos primeiro


def recupera_coorientadores_por_semestre(configuracao):
    """Recupera listas de coorientadores de projetos ordenadas por semestre."""
    professores_pfe = []
    periodo = []

    ano = 2018    # Ano de início do Capstone
    semestre = 2  # Semestre de início do Capstone

    while True:
        professores = []
        grupos = []
        for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                          Lower("user__last_name")):
            count_grupos = []
            grupos_pfe = Projeto.objects.filter(coorientador__usuario__professor=professor, ano=ano, semestre=semestre)
            if grupos_pfe:
                for grupo in grupos_pfe:  # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe:
                        count_grupos.append(grupo)
                if count_grupos:
                    professores.append(professor)
                    grupos.append(count_grupos)
        if professores: # Se não houver nenhum co-orientador não cria entrada na lista
            professores_pfe.append(zip(professores, grupos))
            periodo.append(str(ano)+"."+str(semestre))

        # Para de buscar depois do semestre atual
        if ((semestre == configuracao.semestre + 1) and (ano == configuracao.ano)) or \
           (ano > configuracao.ano):
            break

        # Avança um semestre
        ano, semestre = adianta_semestre(ano, semestre)

    return zip(professores_pfe[::-1], periodo[::-1])  # inverti lista deixando os mais novos primeiro


def recupera_avaliadores_bancas(exame, ano, semestre):
    """Recupera listas de todos os membros das bancas especificadas."""
    pessoas = []
    bancas = []
    bancas_f = Banca.objects.filter(projeto__ano=ano, projeto__semestre=semestre, composicao__exame=exame)
    for banca in bancas_f:
        for membro in banca.membros():
            #if membro:
            pessoas.append(membro)
            bancas.append(banca)
    return zip(pessoas, bancas)


def recupera_mentorias(ano, semestre):
    """Recupera listas de todos os mentores das dinâmicas no semestre."""
    membros = []
    grupos = []

    mentores = PFEUser.objects.all()
    for mentor in mentores:

        count_encontros = []

        encontros = Encontro.objects.filter(facilitador=mentor)
        
        if int(semestre) == 2:
            encontros = encontros.filter(startDate__year=ano, startDate__month__gte=7)
        else:
            encontros = encontros.filter(startDate__year=ano, startDate__month__lte=7)
            
        if encontros:
            for encontro in encontros:
                count_encontros.append(encontro)
            if count_encontros:
                membros.append(mentor)
                grupos.append(count_encontros)

    return zip(membros, grupos)


def move_avaliacoes(avaliacoes_anteriores=[], observacoes_anteriores=[]):
    """Move avaliações anteriores para base de dados de Avaliações Velhas."""
    for avaliacao_velha in avaliacoes_anteriores:
        copia_avaliacao = Avaliacao_Velha()
        for field in avaliacao_velha.__dict__.keys():
            copia_avaliacao.__dict__[field] = avaliacao_velha.__dict__[field]
        copia_avaliacao.id = None
        copia_avaliacao.save()
        avaliacao_velha.delete()
    for observacao_velha in observacoes_anteriores:
        copia_observacao = Observacao_Velha()
        for field in observacao_velha.__dict__.keys():
            copia_observacao.__dict__[field] = observacao_velha.__dict__[field]
        copia_observacao.id = None
        copia_observacao.save()
        observacao_velha.delete()

def check_planos_de_orientacao(projetos, ano, semestre, PRAZO):
    # Verifica se todos os projetos do professor orientador têm o plano de orientação
    tipo_documento = TipoDocumento.objects.get(nome="Plano de Orientação")
    feito = all(Documento.objects.filter(tipo_documento=tipo_documento, projeto=projeto).exists() for projeto in projetos)
    planos_de_orientacao__prazo = None
    planos_de_orientacao = 'b'
    if feito:
        planos_de_orientacao = 'g'
    else:
        evento = Evento.get_evento(sigla="IA", ano=ano, semestre=semestre)  # Início das aulas
        if evento:
            planos_de_orientacao__prazo = evento.endDate + datetime.timedelta(days=(PRAZO+5))
            if datetime.date.today() < evento.endDate:
                planos_de_orientacao = 'b'
            elif datetime.date.today() > planos_de_orientacao__prazo:
                planos_de_orientacao = 'r'
            else:
                planos_de_orientacao = 'y'
    return {"planos_de_orientacao": (planos_de_orientacao, planos_de_orientacao__prazo)}


def check_relatos_quinzenais(projetos, ano, semestre, PRAZO):
    # Verifica se todos os projetos do professor orientador têm as avaliações dos relatos quinzenais
    relatos_quinzenais = 'b'
    for projeto in projetos:
        for evento, relatos, avaliados, _ in busca_relatos(projeto):
            if evento and (not evento.em_prazo()):  # Prazo para estudantes, assim ja deviam ter sido avaliados ou em vias de.
                if relatos:
                    if avaliados and relatos_quinzenais not in ['r', 'y']:
                        relatos_quinzenais = 'g'
                    elif datetime.date.today() > evento.endDate + datetime.timedelta(days=PRAZO):
                        relatos_quinzenais = 'r'
                    elif relatos_quinzenais != 'r':
                        relatos_quinzenais = 'y'
                elif relatos_quinzenais not in ['r', 'y']:
                    relatos_quinzenais = 'g'
    return {"relatos_quinzenais": (relatos_quinzenais, None)}


def check_avaliar_entregas(projetos, ano, semestre, PRAZO):
    # Verifica se todos os projetos do professor orientador têm as avaliações das entregas
    avaliar_entregas = 'b'
    composicoes = filtra_composicoes(Composicao.objects.filter(entregavel=True), ano, semestre)
    for projeto in projetos:
        entregas = filtra_entregas(composicoes, projeto)
        for item in entregas:
            if item["evento"] and item["evento"].endDate:
                dias_passados = (datetime.date.today() - item["evento"].data_aval()).days
                if dias_passados > 0:
                    if item["composicao"] and item["composicao"].exame:
                        if item["composicao"].exame.grupo:
                            for documento in item["documentos"]:
                                if item["avaliacoes"]:
                                    diff_entrega = (documento.data - item["avaliacoes"].first().momento)
                                    if diff_entrega.days > PRAZO:
                                        avaliar_entregas = 'r'  # Nova avaliação urgente!
                                    elif diff_entrega.total_seconds() > 0:
                                        if avaliar_entregas != 'r':
                                            avaliar_entregas = 'y'  # Nova avaliação pendente!
                                    else:
                                        if avaliar_entregas not in ['r', 'y']:
                                            avaliar_entregas = 'g'  # Avaliação feita!
                                else:
                                    if dias_passados > PRAZO:
                                        avaliar_entregas = 'r'  # Avaliação urgente!
                                    else:
                                        if avaliar_entregas != 'r':
                                            avaliar_entregas = 'y'  # Avaliação pendente!
                        else:
                            if item["alocacoes"]:
                                for _, values in item["alocacoes"].items():
                                    for documento in values["documentos"]:
                                        if values["avaliacoes"]:
                                            diff_entrega = (documento.data - values["avaliacoes"].first().momento)
                                            if diff_entrega.days > PRAZO:
                                                avaliar_entregas = 'r'  # Nova avaliação urgente!
                                            elif diff_entrega.total_seconds() > 0:
                                                if avaliar_entregas != 'r':
                                                    avaliar_entregas = 'y'  # Nova avaliação pendente!
                                            else:
                                                if avaliar_entregas != 'r' and avaliar_entregas != 'y':
                                                    avaliar_entregas = 'g'  # Avaliação feita!
                                        else:
                                            if dias_passados > PRAZO:
                                                avaliar_entregas = 'r'  # Avaliação urgente!
                                            else:
                                                if avaliar_entregas != 'r':
                                                    avaliar_entregas = 'y'  # Avaliação pendente!
    return {"avaliar_entregas": (avaliar_entregas, None)}


def check_bancas_index(projetos, ano, semestre, PRAZO):
    # Verifica se todos os projetos do professor orientador têm os agendamentos das bancas
    bancas_index = 'b'
    tipos_de_banca = [("BI", "BI"), ("BF", "BF")]  # (sigla banca, sigla evento)

    for projeto in projetos:
        for sigla_b, sigla_e in tipos_de_banca:
            banca_exists = Banca.objects.filter(projeto=projeto, composicao__exame__sigla=sigla_b).exists()
            evento = Evento.get_evento(sigla=sigla_e, ano=ano, semestre=semestre)
            if evento:
                days_diff = (datetime.date.today() - evento.startDate).days
                if days_diff > -16:
                    if banca_exists and bancas_index != 'r' and bancas_index != 'y':
                        bancas_index = 'g'
                    else:
                        if days_diff > -9:
                            bancas_index = 'r'
                        elif bancas_index != 'r':
                            bancas_index = 'y'
    return {"bancas_index": (bancas_index, None)}


def check_avaliacoes_pares(projetos, ano, semestre, PRAZO):
    # Verifica se todos os projetos do professor orientador têm as avaliações de pares conferidas
    avaliacoes_pares = 'b'
    evento = Evento.get_evento(sigla="API", ano=ano, semestre=semestre)  # "Avaliação de Pares Intermediária"
    if evento and (datetime.date.today() - evento.startDate).days > 0:
        feito = True
        for projeto in projetos:
            for alocacao in Alocacao.objects.filter(projeto=projeto):
                if Pares.objects.filter(alocacao_de=alocacao, tipo=0).first():  # Intermediaria
                    feito = feito and alocacao.avaliacao_intermediaria
        if feito and avaliacoes_pares != 'r' and avaliacoes_pares != 'y':
            avaliacoes_pares = 'g'
        else:
            if evento and (datetime.date.today() - evento.endDate).days > PRAZO:
                avaliacoes_pares = 'r'
            elif avaliacoes_pares != 'r':
                avaliacoes_pares = 'y'
    evento = Evento.get_evento(sigla="APF", ano=ano, semestre=semestre)  #"Avaliação de Pares Final"
    if evento and (datetime.date.today() - evento.startDate).days > 0:
        feito = True
        for projeto in projetos:
            for alocacao in Alocacao.objects.filter(projeto=projeto):
                if Pares.objects.filter(alocacao_de=alocacao, tipo=1).first():  # Final
                    feito = feito and alocacao.avaliacao_final
        if feito and avaliacoes_pares != 'r' and avaliacoes_pares != 'y':
            avaliacoes_pares = 'g'
        else:
            if evento and (datetime.date.today() - evento.endDate).days > PRAZO:
                avaliacoes_pares = 'r'
            elif avaliacoes_pares != 'r':
                avaliacoes_pares = 'y'
    return {"avaliacoes_pares": (avaliacoes_pares, None)}


def check_avaliar_bancas(user, ano, semestre, PRAZO):
    # Verifica se todas as bancas do semestre foram avaliadas
    avaliar_bancas = 'b'
    
    bancas_0_1 = Banca.objects.filter(projeto__ano=ano, projeto__semestre=semestre, composicao__exame__sigla__in=("BI", "BF")).\
        filter(Q(membro1=user) | Q(membro2=user) | Q(membro3=user) | Q(projeto__orientador=user.professor)) # Interm ou Final
    
    bancas_2 = Banca.objects.filter( projeto__ano=ano, projeto__semestre=semestre, composicao__exame__sigla="F").\
        filter(Q(membro1=user) | Q(membro2=user) | Q(membro3=user)) # Falconi

    bancas_3 = Banca.objects.filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre, composicao__exame__sigla="P").\
        filter(Q(membro1=user) | Q(membro2=user) | Q(membro3=user)) # Probation
    
    bancas = bancas_0_1 | bancas_2 | bancas_3

    if bancas.exists():
        avaliar_bancas = 'g'

    exame_titles = {
        "BF": "Banca Final",
        "BI": "Banca Intermediária",
        "F": "Certificação Falconi",
        "P": "Probation"
    }

    for banca in bancas:
        exame_title = exame_titles.get(banca.composicao.exame.sigla)
        if exame_title:
            exame = Exame.objects.filter(titulo=exame_title).first()
            if banca.alocacao:
                avaliacoes = Avaliacao2.objects.filter(alocacao=banca.alocacao, exame=exame, avaliador=user)
            else:
                avaliacoes = Avaliacao2.objects.filter(projeto=banca.projeto, exame=exame, avaliador=user)
        else:
            avaliacoes = None

        if not avaliacoes:
            if banca.endDate and (datetime.date.today() - banca.endDate.date()).days > 2:
                avaliar_bancas = 'r'
            else:
                avaliar_bancas = 'y'         
    return {"avaliar_bancas": (avaliar_bancas, None)}


def ver_pendencias_professor(user, ano, semestre):
    PRAZO = int(get_object_or_404(Configuracao).prazo_avaliar)  # prazo para preenchimentos de avaliações
    context = {}
    if user.tipo_de_usuario in [2,4]:  # Professor ou Administrador
        projetos = Projeto.objects.filter(orientador=user.professor, ano=ano, semestre=semestre)
        if projetos:
            context.update(check_planos_de_orientacao(projetos, ano, semestre, PRAZO))
            context.update(check_relatos_quinzenais(projetos, ano, semestre, PRAZO))
            context.update(check_avaliar_entregas(projetos, ano, semestre, PRAZO))
            context.update(check_bancas_index(projetos, ano, semestre, PRAZO))
            context.update(check_avaliacoes_pares(projetos, ano, semestre, PRAZO))
        context.update(check_avaliar_bancas(user, ano, semestre, PRAZO))
    return context


def mensagem_edicao_banca(banca, atualizada=False, excluida=False, enviar=False):

    subject = "Capstone | Banca - "
    subject += banca.composicao.exame.titulo + " "
    if excluida:
        subject += " - Cancelada"
    else:
        subject += " - Reagendada" if atualizada else "Agendada"

    projeto = banca.get_projeto()
    if banca.alocacao:
        subject += " - Estudante: " + banca.alocacao.aluno.user.get_full_name()
    subject += " [" + projeto.organizacao.nome + "] " + projeto.get_titulo()

    mensagem = ''
    
    BLOQUEAR = True
    configuracao = get_object_or_404(Configuracao)
    interseccao = False
    if not excluida:
        if calcula_interseccao_bancas(banca, banca.startDate, banca.endDate):
            interseccao = True
            if BLOQUEAR:
                return "Mais de duas bancas agendadas para o mesmo horário! Agendamento não realizado."

    configuracao = get_object_or_404(Configuracao)
    recipient_list = []
    orientador = projeto.orientador
    membros = banca.membros()

    recipient_list.extend(membro.email for membro in membros)
    if banca.alocacao:  # Probation
        recipient_list.append(banca.alocacao.aluno.user.email)
    else:
        recipient_list.extend(alocacao.aluno.user.email for alocacao in projeto.alocacao_set.all())
    if configuracao.coordenacao:
        recipient_list.append(configuracao.coordenacao.user.email)
    if configuracao.operacao:
        recipient_list.append(configuracao.operacao.email)

    context_carta = {
        "banca": banca,
        "atualizada": atualizada,
        "excluida": excluida,
        "enviar": enviar,
        "projeto": projeto,
        "link": settings.SERVER + "/projetos/projeto/" + str(projeto.id),
        "interseccao": interseccao,
        "orientador": orientador,
        "membros": membros
    }

    mensagem = render_message("Agendamento Banca", context_carta, urlize=False)

    if enviar:
        email(subject, recipient_list, mensagem)


# Mensagem preparada para o orientador/coordenador
def mensagem_orientador(banca, geral=False):
    objetivos = ObjetivosDeAprendizagem.objects.all()  
    exame = banca.composicao.exame
    projeto = banca.get_projeto()

    # Buscando Avaliadores e Avaliações
    avaliadores = {}
    for objetivo in objetivos:
        avaliacoes = Avaliacao2.objects.filter(projeto=projeto, objetivo=objetivo, exame=exame)\
                .order_by("avaliador", "-momento")
        if banca.alocacao:
            avaliacoes = avaliacoes.filter(alocacao=banca.alocacao)

        for avaliacao in avaliacoes:
            if avaliacao.avaliador not in avaliadores:
                avaliadores[avaliacao.avaliador] = {}
            if objetivo not in avaliadores[avaliacao.avaliador]:
                avaliadores[avaliacao.avaliador][objetivo] = avaliacao
                avaliadores[avaliacao.avaliador]["momento"] = avaliacao.momento

    observacoes = Observacao.objects.filter(projeto=projeto, exame=exame).order_by("avaliador", "-momento")
    if banca.alocacao:
        observacoes = observacoes.filter(alocacao=banca.alocacao)

    for observacao in observacoes:
        if observacao.avaliador not in avaliadores:
            avaliadores[observacao.avaliador] = {}  # Não devia acontecer isso
        if "observacoes_orientador" not in avaliadores[observacao.avaliador]:
            avaliadores[observacao.avaliador]["observacoes_orientador"] = observacao.observacoes_orientador
        if "observacoes_estudantes" not in avaliadores[observacao.avaliador]:
            avaliadores[observacao.avaliador]["observacoes_estudantes"] = observacao.observacoes_estudantes

    message3, obj_avaliados = calcula_notas_bancas(avaliadores)
    message2 = calcula_media_notas_bancas(obj_avaliados)

    context_carta = {
        "banca": banca,
        "objetivos": objetivos,
        "projeto": projeto,
    }
    if geral:
        message = render_message("Informe Geral de Avaliação de Banca", context_carta)
    else:
        message = render_message("Informe de Avaliação de Banca", context_carta)
    
    return message+message2+message3
