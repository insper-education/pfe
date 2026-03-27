#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 4 de Janeiro de 2025
"""

import datetime
from collections import defaultdict

from django.db.models import Q
from django.shortcuts import get_object_or_404


from .models import Area, AreaDeInteresse, Observacao, Coorientador, Conexao, Proposta, Projeto
from .models import Participante, ReuniaoParticipante, EncontroParticipante, Desconto

from academica.models import Exame

from estudantes.support import filtra_estudantes_por_curso
from estudantes.models import Pares, Relato, FeedbackPares

from operacional.models import Curso

from users.models import Alocacao, PFEUser, Alocacao, Associado, Aluno


def get_areas_estudantes(alunos, areas=None):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    usuarios = [aluno.user for aluno in alunos]

    todas_areas = areas if areas is not None else Area.objects.filter(ativa=True)
    areaspfe = {
        area: (AreaDeInteresse.objects.filter(usuario__in=usuarios, area=area), area.descricao)
        for area in todas_areas
    }

    outras = AreaDeInteresse.objects.filter(usuario__in=usuarios, area__isnull=True)

    return areaspfe, outras

def get_areas_propostas(propostas, areas=None):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    todas_areas = areas if areas is not None else Area.objects.filter(ativa=True)
    areaspfe = {
        area: (AreaDeInteresse.objects.filter(proposta__in=propostas, area=area), area.descricao)
        for area in todas_areas
    }

    outras = AreaDeInteresse.objects.filter(proposta__in=propostas, area__isnull=True)

    return areaspfe, outras



def _monta_tabela_areas(areaspfe, campo_origem):
    """Monta tabela de áreas por origem (usuário ou proposta)."""
    tabela = {}
    for _area, objs in areaspfe.items():
        for obj in objs[0]:
            origem = getattr(obj, campo_origem)
            tabela.setdefault(origem, []).append(obj.area)
    return tabela


def _monta_tabela_niveis(areaspfe, campo_origem):
    """Monta tabela de níveis por origem e área.

    Valor armazenado:
    - 1, 2, 3: nível de interesse definido
    - 0: área selecionada sem nível definido
    """
    tabela_niveis = {}
    for _area, objs in areaspfe.items():
        for obj in objs[0]:
            origem = getattr(obj, campo_origem)
            origem_id = getattr(origem, "id", None)
            if origem_id is None:
                continue

            if origem_id not in tabela_niveis:
                tabela_niveis[origem_id] = {}

            nivel = obj.nivel_interesse if obj.nivel_interesse in (1, 2, 3) else 0
            atual = tabela_niveis[origem_id].get(obj.area_id)

            # Se houver conflito, prioriza nível explícito sobre ausência de nível.
            if atual is None or (atual == 0 and nivel in (1, 2, 3)):
                tabela_niveis[origem_id][obj.area_id] = nivel

    return tabela_niveis


def _monta_dados_barras_area(areas_ativas, area_interesses):
    """Monta dados agregados para gráfico de barras empilhadas por nível de interesse."""
    agrupado = {
        area.id: {
            "area": area,
            "descricao": area.descricao,
            "itens": [],
            "counts": {0: 0, 1: 0, 2: 0, 3: 0},
        }
        for area in areas_ativas
    }

    for item in area_interesses:
        bucket = agrupado.get(item.area_id)
        if not bucket:
            continue
        bucket["itens"].append(item)

        nivel = item.nivel_interesse if item.nivel_interesse in (1, 2, 3) else 0
        bucket["counts"][nivel] += 1

    max_total = 0
    for bucket in agrupado.values():
        total = sum(bucket["counts"].values())
        bucket["total"] = total
        max_total = max(max_total, total)

    niveis = [
        {"key": 0, "label": "Sem nível", "color": "#111111"},
        {"key": 1, "label": "Muito Interesse", "color": "#0f766e"},
        {"key": 2, "label": "Interesse Médio", "color": "#d97706"},
        {"key": 3, "label": "Interesse Complementar", "color": "#2563eb"},
    ]

    dados = []
    for area in areas_ativas:
        bucket = agrupado[area.id]
        segmentos = []
        for nivel in niveis:
            quantidade = bucket["counts"][nivel["key"]]
            largura = (100.0 * quantidade / max_total) if max_total > 0 else 0
            segmentos.append({
                "key": nivel["key"],
                "label": nivel["label"],
                "color": nivel["color"],
                "count": quantidade,
                "width": largura,
            })

        dados.append({
            "area": bucket["area"],
            "descricao": bucket["descricao"],
            "itens": bucket["itens"],
            "total": bucket["total"],
            "segmentos": segmentos,
        })

    return dados


def filtra_areas_ativas_por_periodo(ano=None, semestre=None, todas=False):
    """Filtra áreas ativas considerando período (ano/semestre) e vigência da área."""
    areas = Area.objects.filter(ativa=True)
    if todas or ano is None or semestre is None:
        return areas

    ano = int(ano)
    semestre = int(semestre)
    inicio = datetime.date(ano, 1, 1) if semestre == 1 else datetime.date(ano, 7, 1)
    fim = datetime.date(ano, 6, 30) if semestre == 1 else datetime.date(ano, 12, 31)

    return areas.filter(
        Q(ativa_de__isnull=True) | Q(ativa_de__lte=fim),
        Q(ativa_ate__isnull=True) | Q(ativa_ate__gte=inicio),
    )


def contexto_distribuicao_areas(tipo, ano, semestre, todas, areas_ativas, curso="todos", cursos_insper=None):
    """Monta contexto de distribuicao para estudantes, propostas ou projetos."""
    context = {"areas": areas_ativas,}
    if tipo == "estudantes":
        estudantes = filtra_estudantes_por_curso(Aluno.objects.all(), curso, cursos_insper)
        if not todas:
            estudantes = estudantes.filter(ano=ano, semestre=semestre)

        usuarios_ids = estudantes.values_list("user_id", flat=True)
        total_preenchido = AreaDeInteresse.objects.filter(usuario_id__in=usuarios_ids).values("usuario_id").distinct().count()
        areaspfe, outras = get_areas_estudantes(estudantes, areas=areas_ativas)
        area_interesses = AreaDeInteresse.objects.filter(usuario_id__in=usuarios_ids, area__in=areas_ativas).select_related("area", "usuario", "usuario__aluno")
        context.update({
            "total": estudantes.count(),
            "total_preenchido": total_preenchido,
            "areaspfe": areaspfe,
            "outras": outras,
            "tabela": _monta_tabela_areas(areaspfe, "usuario"),
            "tabela_niveis": _monta_tabela_niveis(areaspfe, "usuario"),
            "area_chart_data": _monta_dados_barras_area(areas_ativas, area_interesses),
        })

    elif tipo == "propostas":
        propostas = Proposta.objects.all()
        if not todas:
            propostas = propostas.filter(ano=ano, semestre=semestre)

        areaspfe, outras = get_areas_propostas(propostas, areas=areas_ativas)
        propostas_ids = propostas.values_list("id", flat=True)
        area_interesses = AreaDeInteresse.objects.filter(proposta_id__in=propostas_ids, area__in=areas_ativas).select_related("area", "proposta")
        context.update({
            "total": propostas.count(),
            "areaspfe": areaspfe,
            "outras": outras,
            "tabela": _monta_tabela_areas(areaspfe, "proposta"),
            "tabela_niveis": _monta_tabela_niveis(areaspfe, "proposta"),
            "area_chart_data": _monta_dados_barras_area(areas_ativas, area_interesses),
        })
        
    elif tipo == "projetos":
        projetos = Projeto.objects.all()
        if not todas:
            projetos = projetos.filter(ano=ano, semestre=semestre)

        propostas_ids = projetos.values_list("proposta_id", flat=True)
        propostas_projetos = Proposta.objects.filter(id__in=propostas_ids).distinct()
        areaspfe, outras = get_areas_propostas(propostas_projetos, areas=areas_ativas)
        area_interesses = AreaDeInteresse.objects.filter(proposta_id__in=propostas_ids, area__in=areas_ativas).select_related("area", "proposta")

        context.update({
            "total": propostas_projetos.count(),
            "areaspfe": areaspfe,
            "outras": outras,
            "tabela": _monta_tabela_areas(areaspfe, "proposta"),
            "tabela_niveis": _monta_tabela_niveis(areaspfe, "proposta"),
            "area_chart_data": _monta_dados_barras_area(areas_ativas, area_interesses),
        })
    else:
        raise ValueError("Tipo inválido para distribuição de áreas")

    return context


def _atualiza_tabela_areas(tabela_areas, areaspfe, outras, total_preenchido, ano, semestre):
    """Atualiza as colunas de áreas para uma edição específica."""
    ano = int(ano)
    semestre = int(semestre)

    for area, objs in areaspfe.items():
        # Checa se é valida em area.ativa_de e area.ativa_ate
        if ano < area.ativa_de.year or (ano == area.ativa_de.year and (1 if semestre==1 else 9) < area.ativa_de.month) or (area.ativa_ate and (ano > area.ativa_ate.year or (ano == area.ativa_ate.year and (1 if semestre==1 else 9) > area.ativa_de.month))):
            ativa = False
        else:
            ativa = True
        quantidade = objs[0].count() if objs[0] else 0
        percentual = 100 * (quantidade / total_preenchido) if total_preenchido > 0 else 0
        cor = 255 - 180 * (quantidade / total_preenchido) if total_preenchido > 0 else 0
        tabela_areas[area].append([quantidade, percentual, cor, ativa])

    outras_txt = ", ".join([o.outras for o in outras if o.outras])
    tabela_areas["outras"].append(outras_txt)


def contexto_evolucao_areas(tipo, edicoes, curso="todos", cursos_insper=None):
    """Monta tabela de evolução de áreas para estudantes, propostas ou projetos."""
    tabela_areas = {
        "QUANTIDADE": [],
        "PREENCHIDOS": [],
        "outras": [],
    }
    for area in Area.objects.filter():
        tabela_areas[area] = []

    if tipo == "estudantes":
        estudantes = filtra_estudantes_por_curso(Aluno.objects.all(), curso, cursos_insper)

        for edicao in edicoes:
            ano, semestre = edicao.split('.')
            estudantes_as = estudantes.filter(ano=ano, semestre=semestre)
            usuarios_ids = estudantes_as.values_list("user_id", flat=True)
            total_preenchido = AreaDeInteresse.objects.filter(usuario_id__in=usuarios_ids).values("usuario_id").distinct().count()

            tabela_areas["QUANTIDADE"].append(estudantes_as.count())
            tabela_areas["PREENCHIDOS"].append(total_preenchido)

            areaspfe, outras = get_areas_estudantes(estudantes_as)
            _atualiza_tabela_areas(tabela_areas, areaspfe, outras, total_preenchido, ano, semestre)

        return tabela_areas

    if tipo == "propostas":
        propostas = Proposta.objects.all()

        for edicao in edicoes:
            ano, semestre = edicao.split('.')
            propostas_as = propostas.filter(ano=ano, semestre=semestre)
            propostas_ids = propostas_as.values_list("id", flat=True)
            total_preenchido = AreaDeInteresse.objects.filter(proposta_id__in=propostas_ids).values("proposta_id").distinct().count()

            tabela_areas["QUANTIDADE"].append(propostas_as.count())
            tabela_areas["PREENCHIDOS"].append(total_preenchido)

            areaspfe, outras = get_areas_propostas(propostas_as)
            _atualiza_tabela_areas(tabela_areas, areaspfe, outras, total_preenchido, ano, semestre)

        return tabela_areas

    if tipo == "projetos":
        projetos = Projeto.objects.all()

        for edicao in edicoes:
            ano, semestre = edicao.split('.')
            projetos_as = projetos.filter(ano=ano, semestre=semestre)
            propostas_ids = projetos_as.values_list("proposta_id", flat=True)
            propostas_projetos = Proposta.objects.filter(id__in=propostas_ids).distinct()
            total_preenchido = AreaDeInteresse.objects.filter(proposta_id__in=propostas_ids).values("proposta_id").distinct().count()

            tabela_areas["QUANTIDADE"].append(propostas_projetos.count())
            tabela_areas["PREENCHIDOS"].append(total_preenchido)

            areaspfe, outras = get_areas_propostas(propostas_projetos)
            _atualiza_tabela_areas(tabela_areas, areaspfe, outras, total_preenchido, ano, semestre)

        return tabela_areas

    raise ValueError("Tipo inválido para evolução de áreas")


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
    if 'O' in filtro:
        if projeto.orientador:
            pessoas.append(projeto.orientador.user)
    if 'C' in filtro:
        for coorientador in Coorientador.objects.filter(projeto=projeto).order_by("usuario__full_name"):
            pessoas.append(coorientador.usuario)
    if 'P' in filtro:
        for conexao in Conexao.objects.filter(projeto=projeto).order_by("parceiro__user__full_name"):
            pessoas.append(conexao.parceiro.user)
    if 'A' in filtro:
        for associado in Associado.objects.filter(projeto=projeto).order_by("estudante__user__full_name"):
            pessoas.append(associado.estudante.user)


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
                    participantes.append((participante, Participante.get_situacao_info(situacao)))
                else:
                    participante_model.objects.filter(**filter_kwargs).delete()

                # Lógica para estudantes
                if getattr(participante, "eh_estud", False):
                    alocacao = Alocacao.objects.filter(aluno=participante.aluno, projeto=projeto).last()
                    if alocacao:
                        # Se o estudante faltou sem justificativa, aplica desconto de 0.25 na próxima avaliação
                        # Caso contrário, remove qualquer desconto existente para essa reunião/encontro
                        desconto_filter_with_aloc = dict(desconto_filter, alocacao=alocacao)
                        if situacao == 2:  # Faltou sem justificativa
                            Desconto.objects.update_or_create(
                                **desconto_filter_with_aloc,
                                defaults={"nota": 0.25}
                            )
                        else:
                            Desconto.objects.filter(**desconto_filter_with_aloc).delete()

    return participantes