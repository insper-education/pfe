#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 4 de Janeiro de 2025
"""

import datetime

from django.shortcuts import get_object_or_404


from .models import Area, AreaDeInteresse, Observacao, Coorientador, Conexao
from .models import Participante, ReuniaoParticipante, EncontroParticipante, Desconto

from academica.models import Exame

from estudantes.models import Pares, Relato, FeedbackPares

from operacional.models import Curso

from users.models import Alocacao, PFEUser, Alocacao, Associado


def get_areas_estudantes(alunos):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    usuarios = [aluno.user for aluno in alunos]

    todas_areas = Area.objects.filter(ativa=True)
    areaspfe = {
        area: (AreaDeInteresse.objects.filter(usuario__in=usuarios, area=area), area.descricao)
        for area in todas_areas
    }

    outras = AreaDeInteresse.objects.filter(usuario__in=usuarios, area__isnull=True)

    return areaspfe, outras

def get_areas_propostas(propostas):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    areaspfe = {
        area: (AreaDeInteresse.objects.filter(proposta__in=propostas, area=area), area.descricao)
        for area in Area.objects.filter(ativa=True)
    }

    outras = AreaDeInteresse.objects.filter(proposta__in=propostas, area__isnull=True)

    return areaspfe, outras

def get_alocacoes(projeto):
    """Retorna todas as alocações do projeto."""
    if projeto.time_misto:
        # Em caso de time misto, estudantes de fora da instituição não são listados
        cursos_do_insper = Curso.objects.filter(curso_do_insper=True)
        return Alocacao.objects.filter(projeto=projeto, aluno__curso2__in=cursos_do_insper)
    return Alocacao.objects.filter(projeto=projeto)

def get_pares_colegas(projeto, tipo=0):
    alocacoes = Alocacao.objects.filter(projeto=projeto)
    pares = []
    feedbacks = []
    for alocacao in alocacoes:
        pares.append(Pares.objects.filter(alocacao_de__projeto=projeto, alocacao_para=alocacao, tipo=tipo))
        feedbacks.append(FeedbackPares.objects.filter(alocacao=alocacao, tipo=tipo).last())
    colegas = zip(alocacoes, pares, feedbacks)
    return colegas

def get_nativamente(self):
    """Retorna em string com curso mais nativo da proposta."""

    # Initialize count dictionary for all cursos
    count = {curso: 0 for curso in Curso.objects.all()}
    total = 0

    # Count occurrences of each curso in perfis
    for perfil in self.perfis():
        for curso in perfil.all():
            count[curso] += 1
            total += 1

    if total == 0:
        return " "

    # Find the curso with the maximum count
    keymax = max(count, key=count.get)
    if count[keymax] > total // 2:
        return keymax
    return "?"

def busca_relatos(self):
    """Retorna todos os possiveis relatos quinzenais para o projeto."""
    
    proximo = datetime.date.today() + datetime.timedelta(days=14)

    eventos = self.tem_relatos().filter(startDate__lt=proximo).order_by("endDate")

    relatos = []
    avaliados = []  # se o orientador fez alguma avaliação dos relatos
    observacoes = []  # observações do orientador

    exame = Exame.objects.get(titulo="Relato Quinzenal")

    for index in range(len(eventos)):
    
        if not index: # index == 0:
            relatos_evento = Relato.objects.filter(alocacao__projeto=self,
                                                   momento__lte=eventos[0].endDate + datetime.timedelta(days=1))

            obs = Observacao.objects.filter(projeto=self, exame=exame,
                                            momento__lte=eventos[0].endDate + datetime.timedelta(days=1)).last()
        else:
            relatos_evento = Relato.objects.filter(alocacao__projeto=self,
                                                   momento__gt=eventos[index-1].endDate + datetime.timedelta(days=1), 
                                                   momento__lte=eventos[index].endDate + datetime.timedelta(days=1))

            obs = Observacao.objects.filter(projeto=self, exame=exame,
                                            momento__gt=eventos[index-1].endDate + datetime.timedelta(days=1), 
                                            momento__lte=eventos[index].endDate + datetime.timedelta(days=1)).last()

        avaliado = {}
        for relato in relatos_evento:
            if relato.alocacao not in avaliado:
                avaliado[relato.alocacao] = []
            avaliado[relato.alocacao].append(relato)

        relatos.append(relatos_evento)
        avaliados.append(avaliado)
        observacoes.append(obs)

    return zip(eventos, relatos, avaliados, observacoes)


def recupera_envolvidos(projeto, reuniao=None, encontro=None, filtro=['E', 'O', 'C', 'P', 'A']):
    """Recupera os envolvidos em uma reunião de um projeto."""
    pessoas = []
    integrantes = []
    if 'E' in filtro:
        integrantes = [alocacao.aluno.user for alocacao in Alocacao.objects.filter(projeto=projeto).order_by("aluno__user__full_name")]
        pessoas.extend(integrantes)
    if 'A' in filtro:
        for associado in Associado.objects.filter(projeto=projeto).order_by("estudante__user__full_name"):
            pessoas.append(associado.estudante.user)
    if 'O' in filtro:
        if projeto.orientador:
            pessoas.append(projeto.orientador.user)
    if 'C' in filtro:
        for coorientador in Coorientador.objects.filter(projeto=projeto).order_by("usuario__full_name"):
            pessoas.append(coorientador.usuario)
    if 'P' in filtro:
        for conexao in Conexao.objects.filter(projeto=projeto).order_by("parceiro__user__full_name"):
            pessoas.append(conexao.parceiro.user)


    envolvidos = []
    if reuniao:
        participantes_reuniao = {rp.participante: rp for rp in ReuniaoParticipante.objects.filter(reuniao=reuniao)}
        envolvidos = [
            participantes_reuniao.get(pessoa) or {"participante": pessoa, "situacao": 0}
            for pessoa in pessoas
        ]
        # Adiciona os participantes que estavam marcados na reunião, mas não estão mais no projeto
        extras = ReuniaoParticipante.objects.filter(reuniao=reuniao).exclude(participante__in=pessoas)
        envolvidos.extend(extras)

    elif encontro:
        participantes_encontro = {ep.participante: ep for ep in EncontroParticipante.objects.filter(encontro=encontro)}
        envolvidos = [
            participantes_encontro.get(pessoa) or {"participante": pessoa, "situacao": 0}
            for pessoa in pessoas
        ]
        # Adiciona os participantes que estavam marcados no encontro, mas não estão mais no projeto
        extras = EncontroParticipante.objects.filter(encontro=encontro).exclude(participante__in=pessoas)
        envolvidos.extend(extras)

    else:
        for pessoa in pessoas:
            if pessoa in integrantes:
                situacao = 1  # Presente
                integrante = True
            else:
                situacao = 0  # Não convocado
                integrante = False
            envolvidos.append({"participante": pessoa,"situacao": situacao, "integrante": integrante})

    return envolvidos


def anota_participacao(POST, reuniao=None, encontro=None):
    """Salva a participação dos envolvidos em uma reunião ou encontro."""
    if not (reuniao or encontro):
        return

    if reuniao:
        parent = reuniao
        parent_field = "reuniao"
        participante_model = ReuniaoParticipante
        desconto_filter = {"reuniao": reuniao}
        projeto = reuniao.projeto
    else:
        parent = encontro
        parent_field = "encontro"
        participante_model = EncontroParticipante
        desconto_filter = {"encontro": encontro}
        projeto = encontro.projeto

    participantes = []

    for key, value in POST.items():
        if key.startswith("envolvido_"):
            _, projeto_id, participante_id = key.split("_", 2)
            if projeto_id == str(projeto.id):
                situacao = int(value)
                participante = get_object_or_404(PFEUser, id=participante_id)
                filter_kwargs = {parent_field: parent, "participante": participante}
                if situacao != 0:
                    participante_model.objects.update_or_create(**filter_kwargs, defaults={"situacao": situacao})
                    participantes.append( (participante, dict(Participante.TIPO_PARTICIPANTE).get(situacao, "")) )
                else:
                    participante_model.objects.filter(**filter_kwargs).delete()

                # Lógica para estudantes
                if getattr(participante, "eh_estud", False):
                    alocacao = Alocacao.objects.get(aluno=participante.aluno, projeto=projeto)
                    desconto_filter_with_aloc = dict(desconto_filter, alocacao=alocacao)
                    if situacao == 2:  # Faltou sem justificativa
                        Desconto.objects.update_or_create(
                            **desconto_filter_with_aloc,
                            defaults={"nota": 0.25}
                        )
                    else:
                        Desconto.objects.filter(**desconto_filter_with_aloc).delete()
    return participantes