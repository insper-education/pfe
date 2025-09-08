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
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .support2 import calcula_media_notas_bancas, calcula_notas_bancas

from academica.models import Exame, Composicao
from academica.support import filtra_composicoes, filtra_entregas

#from documentos.models import TipoDocumento

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

        b_start = intersectadas.filter(Q(endDate__gt=intersectada.startDate) & Q(startDate__lte=intersectada.startDate)).exclude(id=intersectada.id)
        b_end = intersectadas.filter(Q(endDate__gt=intersectada.endDate) & Q(startDate__lte=intersectada.endDate)).exclude(id=intersectada.id)
        if banca:
            b_start = b_start.exclude(id=banca.id)
            b_end = b_end.exclude(id=banca.id)
        c_start = b_start.count() + 1  # Pelo menos coincide com a banca sendo agendada/reagendada
        c_end = b_end.count() + 1  # Pelo menos coincide com a banca sendo agendada/reagendada
        
        intersecta = max(intersecta, c_start, c_end)

    return intersecta >= configuracao.limite_salas_bancas


def editar_banca(banca, request):
    """Edita os valores de uma banca por um request Http."""

    if not request.user.eh_admin:  # Caso não Administrador
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
    
    if not exame.banca:
        return "Exame não é do tipo Banca!", None

    if exame.grupo:
        try:
            banca.projeto = Projeto.objects.get(id=request.POST.get("projeto"))
        except Projeto.DoesNotExist:
            return "Projeto não encontrado!", None
    else:  # Banca Probation
        try:
            banca.alocacao = Alocacao.objects.get(id=request.POST.get("alocacao"))
        except Alocacao.DoesNotExist:
            return "Alocação não encontrada!", None
    
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
    cor = 'b'
    itens = []
    atraso = 0
    today = datetime.date.today()

    evento = Evento.get_evento(sigla="IA", ano=ano, semestre=semestre)  # Início das aulas
    prazo = evento.endDate + datetime.timedelta(days=(PRAZO + 5))

    for projeto in projetos:
        documentos = Documento.objects.filter(tipo_documento__nome="Plano de Orientação", projeto=projeto)
        if not documentos.exists():
            itens.append(str(projeto))
            atraso = max(atraso, (today - prazo).days)
        else:
            documento = documentos.order_by("data").first()
            atraso_tmp = (documento.data.date() - prazo).days
            if documento.data.date() > prazo and atraso_tmp > atraso:
                atraso = atraso_tmp

    if not itens:
        cor = 'g'
    elif evento:
        if today < evento.endDate:
            cor = 'b'
        elif today > prazo:
            cor = 'r'
        else:
            cor = 'y'

    return {"planos_de_orientacao": {"cor": cor, "prazo": prazo, "itens": itens, "atraso": atraso}}


def check_relatos_quinzenais(projetos, ano, semestre, PRAZO):
    # Verifica se todos os projetos do professor orientador têm as avaliações dos relatos quinzenais
    cor = 'b'
    itens = []
    atraso = 0
    prazo = None
    today = datetime.date.today()
    for projeto in projetos:
        for evento, relatos, avaliados, _ in busca_relatos(projeto):
            if not evento or evento.em_prazo():  # Prazo para estudantes, assim ja deviam ter sido avaliados ou em vias de.
                continue
            if relatos:
                atraso_evento = 0
                for alocacao, relato in avaliados.items():
                    momento = relato[0].momento_avaliacao
                    prazo_evento = evento.endDate + datetime.timedelta(days=PRAZO)

                    atraso_tmp = ((momento.date() if momento else today) - prazo_evento).days
                    atraso_evento = max(atraso_evento, atraso_tmp)

                    if relato[0].avaliacao > -1 and cor not in ['r', 'y']:
                        cor = 'g'
                    elif relato[0].avaliacao < 0 and today > prazo_evento:
                        cor = 'r'
                        itens.append(f"{evento} - {projeto.get_titulo_org()} - {alocacao.aluno.user.get_full_name()}")
                        if not prazo or prazo_evento < prazo:
                            prazo = prazo_evento
                    elif cor != 'r':
                        cor = 'y'
                        itens.append(f"{evento} - {projeto.get_titulo_org()} - {alocacao.aluno.user.get_full_name()}")
                        if not prazo or prazo_evento < prazo:
                            prazo = prazo_evento

                atraso += atraso_evento

            elif cor not in ['r', 'y']:
                cor = 'g'
    return {"relatos_quinzenais": {"cor": cor, "prazo": prazo, "itens": itens, "atraso": atraso}}

def check_avaliar_entregas(projetos, ano, semestre, PRAZO):
    def process_item(item, avals, docs, dias_passados, evento):
        nonlocal avaliar_entregas_cor
        nonlocal atraso
        nonlocal prazo
        atraso_local = 0
        for documento in docs:
            if avals:
                atraso_tmp = (avals.first().primeiro_momento.date() - evento.data_aval()).days - PRAZO
                if atraso_tmp > atraso_local:
                    atraso_local = atraso_tmp

                diff_entrega = (documento.data - avals.first().momento)
                if diff_entrega.total_seconds() > 0:
                    if avaliar_entregas_cor not in ['r', 'y']:
                        avaliar_entregas_cor = 'p'  # Refazer a avaliação
                    avaliar_entregas_itens.append(item["evento"])
                else:
                    if avaliar_entregas_cor == 'b':
                        avaliar_entregas_cor = 'g'
            else:

                atraso_tmp = dias_passados - PRAZO
                if atraso_tmp > atraso_local:
                    atraso_local = atraso_tmp

                if dias_passados > PRAZO:
                    avaliar_entregas_cor = 'r'
                    avaliar_entregas_itens.append(item["evento"])
                    if not prazo or (evento.data_aval() + datetime.timedelta(days=PRAZO)) < prazo:
                        prazo = evento.data_aval() + datetime.timedelta(days=PRAZO)
                else:
                    if avaliar_entregas_cor != 'r':
                        avaliar_entregas_cor = 'y'
                    avaliar_entregas_itens.append(item["evento"])
                    if not prazo or (evento.data_aval() + datetime.timedelta(days=PRAZO)) < prazo:
                        prazo = evento.data_aval() + datetime.timedelta(days=PRAZO)
        atraso += atraso_local

    avaliar_entregas_cor = 'b'
    avaliar_entregas_itens = []
    atraso = 0
    prazo = None
    composicoes = filtra_composicoes(Composicao.objects.filter(entregavel=True), ano, semestre)
    for projeto in projetos:
        entregas = filtra_entregas(composicoes, projeto)
        for item in entregas:
            evento = item.get("evento")
            if evento and evento.endDate:
                dias_passados = (datetime.date.today() - evento.data_aval()).days
                

                if dias_passados > 0 and item.get("composicao") and item["composicao"].exame:
                    if item["composicao"].exame.grupo:
                        process_item(item, item.get("avaliacoes"), item.get("documentos", []), dias_passados, evento)
                    else:
                        for values in (item.get("alocacoes") or {}).values():
                            process_item(item, values.get("avaliacoes"), values.get("documentos", []), dias_passados, evento)
    return {"avaliar_entregas": {"cor": avaliar_entregas_cor, "prazo": prazo, "itens": avaliar_entregas_itens, "atraso": atraso}}


def check_bancas_index(projetos, ano, semestre, PRAZO):
    # Verifica se todos os projetos do professor orientador têm os agendamentos das bancas
    cor = 'b'
    itens = []
    atraso = 0
    prazo = None
    tipos_de_banca = [("ERI", "BI"), ("ERF", "BF")]
    today = datetime.date.today()

    for projeto in projetos:
        for sigla_e, sigla_b in tipos_de_banca:
            evento = Evento.get_evento(sigla=sigla_e, ano=ano, semestre=semestre)
            if not evento:
                continue

            banca = Banca.objects.filter(projeto=projeto, composicao__exame__sigla=sigla_b).first()
            if banca:
                atraso_local = (banca.data_marcacao - evento.startDate).days + (PRAZO // 2)
            else:
                atraso_local = (today - evento.startDate).days + (PRAZO // 2)
            if atraso_local > 0:
                atraso += atraso_local

            days_diff = (evento.startDate - today).days
            
            if days_diff > (2 * PRAZO):
                continue
            if banca and cor not in ['r', 'y']:
                cor = 'g'
            else:
                if days_diff > (PRAZO//2) and cor != 'r':
                    cor = 'y'
                    if not prazo or (evento.startDate + datetime.timedelta(days=PRAZO)) < prazo:
                        prazo = evento.startDate + datetime.timedelta(days=PRAZO)
                else:
                    cor = 'r'
                    if not prazo or (evento.startDate + datetime.timedelta(days=PRAZO)) < prazo:
                        prazo = evento.startDate + datetime.timedelta(days=PRAZO)
                
                itens.append(f"{sigla_b} -> {projeto}")  # Banca de Projeto não agendada

    return {"bancas_index": {"cor": cor, "prazo": prazo, "itens": itens, "atraso": atraso}}


def check_avaliacoes_pares(projetos, ano, semestre, PRAZO):
    def verifica_pares(sigla, tipo, cor_atual):
        nonlocal prazo
        evento = Evento.get_evento(sigla=sigla, ano=ano, semestre=semestre)
        if not evento or (datetime.date.today() <= evento.startDate):
            return cor_atual, [], 0
        pendentes = []
        atraso_local = 0
        for projeto in projetos:
            atraso_aloc = 0
            for alocacao in Alocacao.objects.filter(projeto=projeto):
                if Pares.objects.filter(alocacao_de=alocacao, tipo=tipo).exists():
                    momento = (alocacao.avaliacao_intermediaria if tipo == 0 else alocacao.avaliacao_final)
                    if not momento:
                        pendentes.append(sigla + " -> " + str(projeto))
                        atraso_tmp = (datetime.date.today() - evento.endDate).days
                        atraso_aloc = max(atraso_aloc, atraso_tmp)
                        break
                    else:
                        atraso_tmp = (momento.date() - evento.endDate).days - PRAZO
                        atraso_aloc = max(atraso_aloc, atraso_tmp)
            atraso_local += atraso_aloc
                
        if not pendentes and cor_atual not in ['r', 'y']:
            return 'g', [], atraso_local
        if (datetime.date.today() - evento.endDate).days > PRAZO:
            if not prazo or (evento.endDate + datetime.timedelta(days=PRAZO)) < prazo:
                prazo = evento.endDate + datetime.timedelta(days=PRAZO)
            return 'r', pendentes, atraso_local
        if cor_atual != 'r':
            if not prazo or (evento.endDate + datetime.timedelta(days=PRAZO)) < prazo:
                prazo = evento.endDate + datetime.timedelta(days=PRAZO)
            return 'y', pendentes, atraso_local
        return cor_atual, pendentes, atraso_local

    cor, itens, atraso, prazo = 'b', [], 0, None
    for sigla, tipo in [("API", 0), ("APF", 1)]:
        cor, new_itens, novo_atraso = verifica_pares(sigla, tipo, cor)
        itens += new_itens
        atraso += novo_atraso
    return {"avaliacoes_pares": {"cor": cor, "prazo": prazo, "itens": itens, "atraso": atraso}}


def check_avaliar_bancas(user, ano, semestre, PRAZO):
    # Verifica se todas as bancas do semestre foram avaliadas
    cor = 'b'
    itens = []
    atraso = 0
    prazo = None
    
    bancas_0_1 = Banca.objects.filter(projeto__ano=ano, projeto__semestre=semestre, composicao__exame__sigla__in=("BI", "BF")).\
        filter(Q(membro1=user) | Q(membro2=user) | Q(membro3=user) | Q(projeto__orientador=user.professor)) # Interm ou Final
    
    bancas_2 = Banca.objects.filter( projeto__ano=ano, projeto__semestre=semestre, composicao__exame__sigla="F").\
        filter(Q(membro1=user) | Q(membro2=user) | Q(membro3=user)) # Falconi

    bancas_3 = Banca.objects.filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre, composicao__exame__sigla="P").\
        filter(Q(membro1=user) | Q(membro2=user) | Q(membro3=user)) # Probation
    
    bancas = bancas_0_1 | bancas_2 | bancas_3


    for banca in bancas:

        if banca.alocacao:
            avaliacoes = Avaliacao2.objects.filter(alocacao=banca.alocacao, exame__sigla=banca.composicao.exame.sigla, avaliador=user)
        else:
            avaliacoes = Avaliacao2.objects.filter(projeto=banca.projeto, exame__sigla=banca.composicao.exame.sigla, avaliador=user)
        
        if not avaliacoes.exists():
            diff_data = (datetime.date.today() - banca.startDate.date()).days
            if banca.endDate and diff_data > PRAZO:
                cor = 'r'
                atraso += diff_data - PRAZO
                if not prazo or (banca.startDate.date() + datetime.timedelta(days=PRAZO)) < prazo:
                    prazo = banca.startDate.date() + datetime.timedelta(days=PRAZO)
            elif banca.endDate and diff_data >= 0 and cor != 'r':
                cor = 'y'
                if not prazo or (banca.startDate.date() + datetime.timedelta(days=PRAZO)) < prazo:
                    prazo = banca.startDate.date() + datetime.timedelta(days=PRAZO)
            itens.append(banca)
        elif cor not in ['r', 'y']:
            cor = 'g'
            atraso_local = (avaliacoes.first().primeiro_momento - banca.startDate).days - PRAZO
            if atraso_local > 0:
                atraso += atraso_local

    return {"avaliar_bancas": {"cor": cor, "prazo": prazo, "itens": itens, "atraso": atraso}}


def ver_pendencias_professor(user, ano, semestre):
    PRAZO = int(get_object_or_404(Configuracao).prazo_avaliar)  # prazo para preenchimentos de avaliações
    PRAZO_BANCA = int(get_object_or_404(Configuracao).prazo_avaliar_banca)  # prazo para preenchimento de avaliações de bancas
    context = {}
    if user.eh_prof_a:  # Professor ou Administrador
        projetos = Projeto.objects.filter(orientador=user.professor, ano=ano, semestre=semestre)
        if projetos:
            context.update(check_planos_de_orientacao(projetos, ano, semestre, PRAZO))
            context.update(check_relatos_quinzenais(projetos, ano, semestre, PRAZO))
            context.update(check_avaliar_entregas(projetos, ano, semestre, PRAZO))
            context.update(check_bancas_index(projetos, ano, semestre, PRAZO))
            context.update(check_avaliacoes_pares(projetos, ano, semestre, PRAZO))
        context.update(check_avaliar_bancas(user, ano, semestre, PRAZO_BANCA))
    return context


def mensagem_edicao_banca(banca, atualizada=False, excluida=False, enviar=False):

    subject = "Capstone | Banca - " + banca.composicao.exame.titulo + " "
    if excluida:
        subject += " - Cancelada"
    else:
        subject += " - Reagendada" if atualizada else "Agendada"

    projeto = banca.get_projeto()
    if banca.alocacao:
        subject += " - Estudante: " + banca.alocacao.aluno.user.get_full_name()
    subject += " [" + projeto.organizacao.nome + "] " + projeto.get_titulo()

    BLOQUEAR = True
    configuracao = get_object_or_404(Configuracao)
    interseccao = False
    if not excluida:
        if calcula_interseccao_bancas(banca, banca.startDate, banca.endDate):
            interseccao = True
            if BLOQUEAR:
                return "Mais de duas bancas agendadas para o mesmo horário! Agendamento não realizado."

    recipient_list = []
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
        "link": settings.SERVER + reverse("projeto_infos", args=[projeto.id]),
        "interseccao": interseccao,
        "orientador": projeto.orientador,
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
        avaliacoes = Avaliacao2.objects.filter(projeto=projeto, objetivo=objetivo, exame=exame).order_by("avaliador", "-momento")
        if banca.alocacao:  # Caso de probation
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
