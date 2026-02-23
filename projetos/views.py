#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import datetime
import csv
from multiprocessing import context
from urllib import request
import dateutil.parser
import json
import logging
import copy

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.functions import Lower
from django.http import JsonResponse, HttpResponse
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from estudantes.views import dinamica_conflitos
from users.templatetags import alocacao

from .messages import email, message_reembolso

from .models import Projeto, Proposta, Configuracao, Observacao, TematicaEncontro
from .models import Coorientador, Avaliacao2, ObjetivosDeAprendizagem
from .models import Feedback, Acompanhamento, Anotacao, Organizacao
from .models import Documento, FeedbackEstudante
from .models import Banco, Reembolso, Aviso, Conexao
from .models import Area, AreaDeInteresse, Banca, Reuniao, ReuniaoParticipante, Pedido

from .support import simple_upload
from .support2 import get_areas_propostas, get_areas_estudantes, recupera_envolvidos, anota_participacao
from .support3 import calcula_objetivos, cap_name, media
from .support3 import divide57, get_notas_alocacao
from .support3 import get_medias_oa, is_projeto_liberado

from .tasks import avisos_do_dia, eventos_do_dia

from academica.models import Exame, CodigoConduta
from academica.support3 import get_media_alocacao_i
from academica.support4 import get_banca_estudante

from administracao.models import Estrutura, Despesa
from administracao.support import usuario_sem_acesso

from operacional.models import Curso

from professores.support3 import puxa_encontros


from projetos.messages import email, render_message

from organizacoes.models import Segmento

from users.models import PFEUser, Aluno, Professor, Opcao, Alocacao, Parceiro, Associado
from users.support import get_edicoes, adianta_semestre_conf


# Get an instance of a logger
logger = logging.getLogger("django")


@login_required
@permission_required("projetos.view_projeto", raise_exception=True)
def index_projetos(request):
    """Página principal dos Projetos."""
    context = {"titulo": { "pt": "Projetos", "en": "Projects"},}
    if "/projetos/projetos" in request.path:
        return render(request, "projetos/projetos.html", context=context)
    else:
        return render(request, "projetos/index_projetos.html", context=context)

@login_required
def projeto_infos(request, primarykey):
    """Mostra um projeto com detalhes conforme tipo de usuário."""    
    projeto = get_object_or_404(Projeto, pk=primarykey)
    alocacoes = Alocacao.objects.filter(projeto=projeto)
    associados = Associado.objects.filter(projeto=projeto)

    context = {
        "titulo": { "pt": "Informações sobre Projeto", "en": "Project Information"},
        "projeto": projeto,
        "alocacoes": alocacoes,
        "associados": associados
    }

    if request.user.eh_estud:  # Se usuário é estudante
        alocado = any(alocacao.aluno == request.user.aluno for alocacao in alocacoes)  # Só libera a visualização se estudante estiver alocado no projeto
        liberado = is_projeto_liberado(projeto)
        if (not alocado) or (not liberado):
            return HttpResponseForbidden("Você não tem autorização para visualizar projeto")
        tipos_docs = ["RPR", "RFG", "RIG", "APG", "AFG", "RFR", "ABF", "ABI", "B", "RPU", "VP"]
        context["documentos"] = Documento.objects.filter(projeto=projeto, tipo_documento__sigla__in=tipos_docs)

    if request.user.eh_parc:  # Se usuário é parceiro
        organizacao = getattr(request.user.parceiro, "organizacao", None)
        if not request.user.has_perm("projetos.view_projeto"):
            if organizacao is None or projeto.proposta.organizacao != organizacao:
                return HttpResponseForbidden("Você não tem autorização para visualizar projeto")
        tipos_docs = ["RFR", "ABF", "B", "RPU", "VP", "COP", "CC", "COE", "APE"]
        context["documentos"] = Documento.objects.filter(projeto=projeto, tipo_documento__sigla__in=tipos_docs)

    if request.user.eh_prof_a:  # Se usuário é professor ou administrador
        context["documentos"] = Documento.objects.filter(projeto=projeto)
        context["medias_oo"] = get_medias_oa(alocacoes)
        context["horarios"] = Estrutura.loads(nome="Horarios Semanais")

    context["conexoes"] = Conexao.objects.filter(projeto=projeto)
    context["coorientadores"] = Coorientador.objects.filter(projeto=projeto)
    context["projetos_avancados"] = Projeto.objects.filter(avancado=projeto)
    context["cooperacoes"] = Conexao.objects.filter(projeto=projeto, colaboracao=True)
    
    return render(request, "projetos/projeto_infos.html", context=context)



@login_required
def dinamicas_infos(request, primarykey):
    """Mostra as dinâmicas de grupo de um projeto."""
    projeto = get_object_or_404(Projeto, pk=primarykey)
    alocacoes = Alocacao.objects.filter(projeto=projeto)
    
    context = {
        "titulo": { "pt": "Dinâmicas de Grupo", "en": "Group Dynamics"},
        "projeto": projeto,
        "alocacoes": alocacoes,    
    }

    if request.user.eh_prof_a:  # Se usuário é professor ou administrador

        # Código de Conduta do Grupo
        codigo_conduta = CodigoConduta.objects.filter(content_type=ContentType.objects.get_for_model(projeto), object_id=projeto.id).last()
        if codigo_conduta:
            context["perguntas_codigo_conduta"] = Estrutura.loads(nome="Código de Conduta do Grupo")
            context["respostas_conduta"] = json.loads(codigo_conduta.codigo_conduta) if codigo_conduta.codigo_conduta else None

        # Funcionalidade do Grupo
        funcionalidade_grupo = {}
        for alocacao in alocacoes:
            funcionalidade_grupo[alocacao.aluno.user] = alocacao.aluno.user.funcionalidade_grupo
        if projeto.orientador:
            funcionalidade_grupo[projeto.orientador.user] = projeto.orientador.user.funcionalidade_grupo
        if funcionalidade_grupo:
            context["questoes_funcionalidade"] = Estrutura.loads(nome="Questões de Funcionalidade")
            context["funcionalidade_grupo"] = funcionalidade_grupo


        # Dinâmica de Conflitos do Grupo
        dinamica_conflitos = {}
        for alocacao in alocacoes:
            dinamica_conflitos[alocacao.aluno.user] = alocacao.aluno.user.dinamica_conflitos
        if projeto.orientador:
            dinamica_conflitos[projeto.orientador.user] = projeto.orientador.user.dinamica_conflitos
        if dinamica_conflitos:
            context["questoes_dinamica_conflitos"] = Estrutura.loads(nome="Questões de Dinâmica de Conflitos")
            context["dinamica_conflitos"] = dinamica_conflitos
    
    return render(request, "projetos/dinamicas_infos.html", context=context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def distribuicao_areas(request):
    """Distribuição por área de interesse dos alunos/propostas/projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano              # Ano atual
    semestre = configuracao.semestre    # Semestre atual
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    todas = False  # Para mostrar todos os dados de todos os anos e semestres
    tipo = "estudantes"
    curso = "todos"

    if request.method == "POST":
        if "tipo" in request.POST and "edicao" in request.POST:

            tipo = request.POST["tipo"]

            if request.POST["edicao"] == "todas":
                todas = True
            else:
                ano, semestre = request.POST["edicao"].split('.')

            if tipo == "estudantes" and "curso" in request.POST:
                curso = request.POST["curso"]

        else:
            return HttpResponse("Erro não identificado (POST incompleto)", status=401)

        if tipo == "estudantes":
            alunos = Aluno.objects.all()

            if curso != "T":
                alunos = alunos.filter(curso2__sigla_curta=curso)
            
            # Filtra para estudantes de um curso específico
            if curso != "TE":
                if curso != 'T':
                    alunos = alunos.filter(curso2__sigla_curta=curso)
                else:
                    alunos = alunos.filter(curso2__in=cursos_insper)

            if not todas:
                alunos = alunos.filter(ano=ano, semestre=semestre)

            total_preenchido = 0
            for aluno in alunos:
                if AreaDeInteresse.objects.filter(usuario=aluno.user).count() > 0:
                    total_preenchido += 1
            areaspfe, outras = get_areas_estudantes(alunos)

            tabela = {}
            for area, objs in areaspfe.items():
                for o in objs[0]:
                    if o.usuario not in tabela:
                        tabela[o.usuario] = []
                    tabela[o.usuario].append(o.area)

            context = {
                "total": alunos.count(),
                "total_preenchido": total_preenchido,
                "areaspfe": areaspfe,
                "outras": outras,
                "tabela": tabela,
                "areas": Area.objects.filter(ativa=True),
            }

        elif tipo == "propostas":
            propostas = Proposta.objects.all()
            if not todas:
                propostas = propostas.filter(ano=ano, semestre=semestre)
            areaspfe, outras = get_areas_propostas(propostas)

            tabela = {}
            for area, objs in areaspfe.items():
                for o in objs[0]:
                    if o.proposta not in tabela:
                        tabela[o.proposta] = []
                    tabela[o.proposta].append(o.area)
            
            context = {
                "total": propostas.count(),
                "areaspfe": areaspfe,
                "outras": outras,
                "tabela": tabela,
                "areas": Area.objects.filter(ativa=True),
            }

        elif tipo == "projetos":

            projetos = Projeto.objects.all()
            if not todas:
                projetos = projetos.filter(ano=ano, semestre=semestre)

            # Estudar forma melhor de fazer isso
            propostas = [p.proposta.id for p in projetos]
            propostas_projetos = Proposta.objects.filter(id__in=propostas)

            areaspfe, outras = get_areas_propostas(propostas_projetos)

            tabela = {}
            for area, objs in areaspfe.items():
                for o in objs[0]:
                    if o.proposta not in tabela:
                        tabela[o.proposta] = []
                    tabela[o.proposta].append(o.area)

            context = {
                "total": propostas_projetos.count(),
                "areaspfe": areaspfe,
                "outras": outras,
                "tabela": tabela,
                "areas": Area.objects.filter(ativa=True),
            }

        else:
            return HttpResponse("Erro não identificado (não encontrado tipo)", status=401)

        context["tipo"] = tipo
        return render(request, "projetos/distribuicao_areas.html", context)

    context = {
        "titulo": { "pt": "Tendência de Áreas de Interesse", "en": "Trend of Areas of Interest"},
        "edicoes": get_edicoes(Aluno)[0],
        "cursos": cursos_insper,
        "cursos_externos": cursos_externos,
    }

    return render(request, "projetos/distribuicao_areas.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_areas(request):
    """Evolução das áreas de interesse dos alunos/propostas/projetos nos anos."""
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")
    edicoes = get_edicoes(Projeto)[0]
    
    tipo = "estudantes"
    curso = "todos"

    if request.method == "POST":
        if "tipo" in request.POST:
            tipo = request.POST["tipo"]
            if tipo == "estudantes" and "curso" in request.POST:
                curso = request.POST["curso"]

        else:
            return HttpResponse("Erro não identificado (POST incompleto)", status=401)

        tabela_areas = {}
        tabela_areas["QUANTIDADE"] = []
        tabela_areas["PREENCHIDOS"] = []
        for a in Area.objects.filter(ativa=True):
            tabela_areas[a] = []
        tabela_areas["outras"] = []
        
        if tipo == "estudantes":
            
            alunos = Aluno.objects.all()

            if curso != "T":
                alunos = alunos.filter(curso2__sigla_curta=curso)
            
            # Filtra para estudantes de um curso específico
            if curso != "TE":
                if curso != 'T':
                    alunos = alunos.filter(curso2__sigla_curta=curso)
                else:
                    alunos = alunos.filter(curso2__in=cursos_insper)

            for edicao in edicoes:
                ano, semestre = edicao.split('.')
                alunos_as = alunos.filter(ano=ano, semestre=semestre)
                total_preenchido = 0
                for aluno in alunos_as:
                    if AreaDeInteresse.objects.filter(usuario=aluno.user).count() > 0:
                        total_preenchido += 1

                tabela_areas["QUANTIDADE"].append(alunos_as.count())
                tabela_areas["PREENCHIDOS"].append(total_preenchido)

                areaspfe, outras = get_areas_estudantes(alunos_as)
            
                for area, objs in areaspfe.items():
                    q = objs[0].count() if objs[0] else 0
                    p = 100*(q/total_preenchido) if total_preenchido > 0 else 0
                    h = (255 - 180*(q/total_preenchido)) if total_preenchido > 0 else 0
                    tabela_areas[area].append( [q, p, h] )
                outras_txt = ""
                for o in outras:
                    outras_txt += o.outras + ", "
                tabela_areas["outras"].append(outras_txt[:-2])  # Remove última vírgula e espaço

        elif tipo == "propostas":
            propostas = Proposta.objects.all()
            for edicao in edicoes:
                ano, semestre = edicao.split('.')
                propostas_as = propostas.filter(ano=ano, semestre=semestre)
                total_preenchido = 0
                for proposta in propostas_as:
                    if AreaDeInteresse.objects.filter(proposta=proposta).count() > 0:
                        total_preenchido += 1

                tabela_areas["QUANTIDADE"].append(propostas_as.count())
                tabela_areas["PREENCHIDOS"].append(total_preenchido)

                areaspfe, outras = get_areas_propostas(propostas_as)
            
                for area, objs in areaspfe.items():
                    q = objs[0].count() if objs[0] else 0
                    p = 100*(q/total_preenchido) if total_preenchido > 0 else 0
                    h = (255 - 180*(q/total_preenchido)) if total_preenchido > 0 else 0
                    tabela_areas[area].append( [q, p, h] )
                outras_txt = ""
                for o in outras:
                    outras_txt += o.outras + ", "
                tabela_areas["outras"].append(outras_txt[:-2])  # Remove última vírgula e espaço

        elif tipo == "projetos":

            projetos = Projeto.objects.all()

            for edicao in edicoes:
                ano, semestre = edicao.split('.')

                projetos_as = projetos.filter(ano=ano, semestre=semestre)
                # Estudar forma melhor de fazer isso
                propostas = [p.proposta.id for p in projetos_as]
                propostas_projetos = Proposta.objects.filter(id__in=propostas)
                total_preenchido = 0
                for proposta in propostas_projetos:
                    if AreaDeInteresse.objects.filter(proposta=proposta).count() > 0:
                        total_preenchido += 1
                
                tabela_areas["QUANTIDADE"].append(propostas_projetos.count())
                tabela_areas["PREENCHIDOS"].append(total_preenchido)

                areaspfe, outras = get_areas_propostas(propostas_projetos)

                for area, objs in areaspfe.items():
                    q = objs[0].count() if objs[0] else 0
                    p = 100*(q/total_preenchido) if total_preenchido > 0 else 0
                    h = (255 - 180*(q/total_preenchido)) if total_preenchido > 0 else 0
                    tabela_areas[area].append( [q, p, h] )

                outras_txt = ""
                for o in outras:
                    outras_txt += o.outras + ", "
                tabela_areas["outras"].append(outras_txt[:-2])  # Remove última vírgula e espaço

        else:
            return HttpResponse("Erro não identificado (não encontrado tipo)", status=401)

        context = {
            "tipo": tipo,
            "tabela_areas": tabela_areas,
            "edicoes": edicoes,
        }
        return render(request, "projetos/evolucao_areas.html", context)

    context = {
        "titulo": { "pt": "Evolução de Áreas de Interesse", "en": "Evolution of Areas of Interest"},
        "cursos": cursos_insper,
        "cursos_externos": cursos_externos,
    }

    return render(request, "projetos/evolucao_areas.html", context)


@login_required
@permission_required("projetos.view_projeto", raise_exception=True)
def projetos_fechados(request):
    """Lista todos os projetos fechados."""

    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.method == "POST":
        if "edicao" in request.POST and "curso" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                projetos_filtrados = Projeto.objects.all()
            else:
                ano, semestre = edicao.split('.')
                projetos_filtrados = Projeto.objects.filter(ano=ano, semestre=semestre)

            curso = request.POST["curso"]    
            
            projetos_filtrados = projetos_filtrados.order_by("-avancado", Lower("proposta__organizacao__nome"))

            projetos_filtrados = projetos_filtrados.prefetch_related(
                "alocacao_set__aluno__user",
                "alocacao_set__aluno__curso2",
                "proposta",
                "conexao_set"
            )

            projetos_selecionados = []
            prioridade_list = []
            cooperacoes = []
            conexoes = []
            qtd_est = []

            numero_estudantes = 0
            numero_estudantes_regulares = 0
            numero_estudantes_avancado = 0
            numero_estudantes_externos = 0

            numero_projetos = 0
            numero_projetos_regulares = 0
            numero_projetos_avancado = 0
            numero_projetos_time_misto = 0

            for projeto in projetos_filtrados:

                estudantes_pfe = Aluno.objects.filter(alocacao__projeto=projeto)

                # Filtra para projetos com estudantes de um curso específico
                if curso != "TE":
                    if curso != 'T':
                        estudantes_pfe = estudantes_pfe.filter(alocacao__aluno__curso2__sigla_curta=curso).distinct()
                    else:
                        estudantes_pfe = estudantes_pfe.filter(alocacao__aluno__curso2__in=cursos_insper).distinct()
                
                num_est = len(estudantes_pfe)
                qtd_est.append(num_est)
                projetos_selecionados.append(projeto)

                if num_est > 0:
                    if projeto.avancado:
                        numero_projetos_avancado += 1
                    elif projeto.time_misto:
                        numero_projetos_time_misto += 1
                    else:
                        numero_projetos_regulares += 1

                    numero_projetos += 1

                prioridades = []
                for estudante in estudantes_pfe:
                    opcoes = Opcao.objects.filter(proposta=projeto.proposta,
                                                #   aluno__alocacao__projeto=projeto,
                                                  aluno=estudante)
                    if opcoes:
                        prioridades.append(opcoes.first().prioridade)
                    else:
                        prioridades.append(0)

                    if estudante.externo:
                        numero_estudantes_externos += 1
                    elif projeto.avancado:
                        numero_estudantes_avancado += 1
                    else:
                        numero_estudantes_regulares += 1

                    numero_estudantes += 1

                prioridade_list.append(zip(estudantes_pfe, prioridades))
                cooperacoes.append(projeto.conexao_set.filter(colaboracao=True))
                conexoes.append(projeto.conexao_set.filter(colaboracao=False))

            projetos = zip(projetos_selecionados, prioridade_list, cooperacoes, conexoes, qtd_est)

            context = {
                "projetos": projetos,
                "numero_projetos": numero_projetos,
                "numero_projetos_regulares": numero_projetos_regulares,
                "numero_projetos_avancado": numero_projetos_avancado,
                "numero_projetos_time_misto": numero_projetos_time_misto,
                "numero_estudantes": numero_estudantes,
                "numero_estudantes_regulares": numero_estudantes_regulares,
                "numero_estudantes_avancado": numero_estudantes_avancado,
                "numero_estudantes_externos": numero_estudantes_externos,
                "configuracao": get_object_or_404(Configuracao),
                "cores_opcoes": Estrutura.loads(nome="Cores Opcoes"),
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        
        informacoes = [
            (".logo", "Logo", "Logo"),
            (".descricao", "Descrição", "Description"),
            (".titulo_original", "Título original", "Original Title", False),
            (".resumo", "Resumo", "Abstract (pt)"),
            (".abstract", "Abstract", "Abstract (en)"),
            (".palavras_chave", "Palavras-chave", "Keywords"),
            (".apresentacao", "Apresentações", "Presentations"),
            (".orientador", "Orientador", "Advisor"),
            (".coorientador", "Coorientador", "Co-advisor"),
            (".estudantes", "Estudantes", "Students"),
            (".curso", "Cursos", "Programs"),
            (".organizacao", "Organização", "Sponsor"),
            (".website", "Website", "Website"),
            (".conexoes", "Conexões", "Connections"),
            (".papeis", "Papéis", "Roles"),
            (".totais", "Totais", "Totals"),
            (".emails", "e-mails", "e-mails"),
            (".avancado", "Avancados", "Advanced"),
            (".sem_estudantes", "Sem estudantes", "Without students"),
            (".grafico", "Gráfico", "Graph", False),
        ]

        context = {
            "titulo": { "pt": "Projetos", "en": "Projects"},
            "edicoes": get_edicoes(Projeto)[0],
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
            "informacoes": informacoes,
        }

    return render(request, "projetos/projetos_fechados.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projetos_lista(request):
    """Lista todos os projetos."""

    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.method == "POST":
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                projetos_filtrados = Projeto.objects.all()
            else:
                ano, semestre = edicao.split('.')
                projetos_filtrados = Projeto.objects.filter(ano=ano, semestre=semestre)

            avancados = "avancados" in request.POST and request.POST["avancados"]=="true"
            if not avancados:
                projetos_filtrados = projetos_filtrados.filter(avancado__isnull=True)

            curso = request.POST["curso"]
            if curso != "TE":
                if curso != 'T':
                    projetos_filtrados = projetos_filtrados.filter(alocacao__aluno__curso2__sigla_curta=curso).distinct()
                else:
                    projetos_filtrados = projetos_filtrados.filter(alocacao__aluno__curso2__in=cursos_insper).distinct()

            cabecalhos = [{ "pt": "Projeto", "en": "Project" },
                          { "pt": "Estudantes", "en": "Students" },
                          { "pt": "Média CR", "en": "Average GPA" },
                          { "pt": "Período", "en": "Semester" },
                          { "pt": "Orientador", "en": "Advisor" },
                          { "pt": "Organização", "en": "Sponsor" },]
            context = {
                "projetos": projetos_filtrados,
                "cabecalhos": cabecalhos,
            }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:

        context = {
            "titulo": { "pt": "Projetos", "en": "Projects"},
            "edicoes": get_edicoes(Projeto)[0],
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "projetos/projetos_lista.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projetos_lista_completa(request):
    """Lista todos os projetos (bem completa)."""
    if request.method == "POST":
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
    
        edicao = request.POST["edicao"]
        if edicao == "todas":
            projetos_filtrados = Projeto.objects.all()
        else:
            ano, semestre = edicao.split('.')
            projetos_filtrados = Projeto.objects.filter(ano=ano, semestre=semestre)

        cabecalhos = [
            { "pt": "Projeto", "en": "Project" },
            { "pt": "Tipo de Projeto", "en": "Project Type" },
            { "pt": "Organização", "en": "Sponsor" },
            { "pt": "ID Orientador", "en": "Advisor ID" },
            { "pt": "Período", "en": "Semester" },
            { "pt": "Quantidade de Estudantes", "en": "Number of Students" },
            { "pt": "Área de Interesse do Projeto", "en": "Project Area of Interest" },
            { "pt": "Média CR", "en": "Average GPA" },
            { "pt": "Média de Avaliações de Grupo", "en": "Average Group Evaluations" },
        ]

        estudantes_fields = [
            ("ID Estudante {i}", "Student {i} ID"),
            ("Curso Estudante {i}", "Student {i} Program"),
            ("CR Estudante {i}", "Student {i} GPA"),
            ("Posição do Projeto nas Opções Selecionadas Estudante {i}", "Student {i} Project Position in Selected Options"),
            ("Média Individual Estudante {i}", "Student {i} Individual Grade"),
            ("Média Final Estudante {i}", "Student {i} Final Grade"),
            ("Áreas de Interesse Estudante {i}", "Student {i} Areas of Interest"),
            ("Trabalho/Estágio Estudante {i}", "Student {i} Work/Internship"),
            ("Atividades Estudantis/Sociais Estudante {i}", "Student {i} Student/Social Activities"),
        ]

        for i in range(5):
            for pt, en in estudantes_fields:
                cabecalhos.append({
                    "pt": pt.format(i=i),
                    "en": en.format(i=i)
                })

        context = {
            "projetos": projetos_filtrados,
            "cabecalhos": cabecalhos,
        }
            
    else:

        context = {
            "titulo": { "pt": "Lista Completa dos Projetos", "en": "Complete Project List"},
            "edicoes": get_edicoes(Projeto)[0],
        }

    return render(request, "projetos/projetos_lista_completa.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_tabela_agenda(request):
    """Lista todos as bancas por semestre."""
    
    if request.method == "POST":
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        edicao = request.POST["edicao"]
        if edicao == "todas":
            bancas = Banca.objects.all()
        else:
            ano, semestre = edicao.split('.')
            bancas_p = Banca.objects.filter(projeto__ano=ano, projeto__semestre=semestre)
            bancas_a = Banca.objects.filter(alocacao__isnull=False, alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre)  # Probation
            bancas = bancas_p | bancas_a

        cabecalhos = [{"pt": "Tipo", "en": "Type"},
                        {"pt": "Data", "en": "Date"},
                        {"pt": "Projeto/Estudante", "en": "Project/Student"},
                        {"pt": "Avaliadores", "en": "Evaluators"},]
        
        context = {
            "bancas": bancas,
            "cabecalhos": cabecalhos,
        }
            
    else:

        context = {
            "titulo": {"pt": "Tabela das Bancas", "en": "Examination Boards Table"},
            "edicoes": get_edicoes(Projeto)[0],
            "tipos_bancas": Exame.objects.filter(banca=True),
        }

    return render(request, "projetos/bancas_tabela_agenda.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_tabela_agenda(request):
    """Lista todos as dinâmicas por semestre."""

    if request.method == "POST":
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        context = puxa_encontros(request.POST["edicao"])
        context["cabecalhos"] = [{"pt": "Tema", "en": "Theme"},
                                    {"pt": "Data", "en": "Date"},
                                    {"pt": "Projeto/Estudante", "en": "Project/Student"},
                                    {"pt": "Facilitador(a)", "en": "Facilitator"},
                                    {"pt": "Formulário", "en": "Form"},
                                ]

    else:

        context = {
            "titulo": {"pt": "Tabela de Mentorias", "en": "Mentoring Table"},
            "edicoes": get_edicoes(Projeto)[0],
            "tematicas": TematicaEncontro.objects.all().order_by("nome"),
        }

    return render(request, "projetos/dinamicas_tabela_agenda.html", context)


@login_required
def meuprojeto(request, primarykey=None):
    """Mostra o projeto do próprio estudante, se for estudante."""
    usuario_sem_acesso(request, (1, 2, 4,)) # Soh Est Parc Adm

    context = {
        "configuracao": get_object_or_404(Configuracao),
        "Projeto": Projeto,
    }
    
    # Caso seja Professor ou Administrador
    if request.user.eh_prof_a:
        context["professor"] = request.user.professor
        context["mensagem_aviso"] = {
            "pt": "Mostrando como é a tela, usando qualquer estudante de exemplo.",
            "en": "Showing how the screen looks, using any example student.",
        }

        # Pegando um estudante de um projeto quando orientador
        if primarykey:
            projeto = get_object_or_404(Projeto, pk=primarykey, orientador=request.user.professor)
        else:
            projeto = Projeto.objects.filter(orientador=request.user.professor).last()

        if projeto:
            alocacao = Alocacao.objects.filter(projeto=projeto).last()
        else:
            return HttpResponse("Nenhum projeto encontrado.", status=401)
        
        alocacao = Alocacao.objects.filter(projeto=projeto).last()
        context["aluno"] = alocacao.aluno if alocacao else None
        
    else:
        # Caso seja estudante
        context["aluno"] = request.user.aluno

    if primarykey:
        context["alocados"] = Alocacao.objects.filter(aluno=context["aluno"], projeto__id=primarykey)
        context["associados"] = Associado.objects.filter(estudante=context["aluno"], projeto__id=primarykey).last()
    else:
        context["alocados"] = Alocacao.objects.filter(aluno=context["aluno"]).order_by("-projeto__ano", "-projeto__semestre")
        context["associados"] = Associado.objects.filter(estudante=context["aluno"]).order_by("id")

    if context["alocados"].count() > 1 or context["associados"].count() > 1:
        context["titulo"] = { "pt": "Meus Projetos", "en": "My Projects"}
    else:
        context["titulo"] = { "pt": "Meu Projeto", "en": "My Project"}

    return render(request, "projetos/meuprojeto_estudantes.html", context=context)



@login_required
def gestao_projeto(request, primarykey=None):
    """Mostra o projeto do próprio estudante, se for estudante."""
    #usuario_sem_acesso(request, (1, 2, 4,)) # Soh Est Parc Adm
    
    context = {
        "titulo": {"pt": "Gestão de Projeto", "en": "Project Management"},
        "configuracao": get_object_or_404(Configuracao),
        "Projeto": Projeto,
    }

    # Caso seja Professor ou Administrador
    if request.user.eh_prof_a:
        context["mensagem_aviso"] = {
            "pt": "Mostrando como é a tela, usando qualquer estudante de exemplo.",
            "en": "Showing how the screen looks, using any example student.",
        }
        # Pegando um estudante de um projeto quando orientador
        if primarykey:
            context["projeto"] = get_object_or_404(Projeto, pk=primarykey, orientador=request.user.professor)
        else:
            context["projeto"] = Projeto.objects.filter(orientador=request.user.professor).last()
    elif request.user.eh_estud:  # Caso seja estudante
        context["projeto"] = Projeto.objects.filter(alocacao__aluno=request.user.aluno).last()
    else:
        return HttpResponse("Acesso negado.", status=401)

    return render(request, "projetos/gestao_projeto.html", context=context)




@login_required
@transaction.atomic
def pedir_recursos(request, primarykey=None):
    """Mostra o projeto do próprio estudante, se for estudante."""
    configuracao = get_object_or_404(Configuracao)
    
    projeto = None
    
    # Caso seja Professor ou Administrador
    if request.user.eh_prof_a:
        # Pegando um estudante de um projeto quando orientador
        if primarykey:
            projeto = get_object_or_404(Projeto, pk=primarykey, orientador=request.user.professor)
        else:
            projeto = Projeto.objects.filter(orientador=request.user.professor).last()
        if not projeto:
            # Criando projeto vazio para mostrar a tela, caso não tenha nenhum projeto com orientador
            projeto = Projeto(
                proposta=Proposta(titulo="Projeto Exemplo", organizacao=Organizacao(nome="Organização Exemplo"), ano=configuracao.ano, semestre=configuracao.semestre),
                ano=configuracao.ano, semestre=configuracao.semestre
            )
    elif request.user.eh_estud:  # Caso seja estudante
        projeto = Projeto.objects.filter(alocacao__aluno=request.user.aluno).last()
        if not projeto:
            return HttpResponse("Acesso negado ou projeto não encontrado.", status=401)
    else:
        return HttpResponse("Acesso negado.", status=401)
    
    

    if request.method == "POST":

        # Check if projeto is valid before creating Pedido
        if projeto.pk is None:
            context = {
                "mensagem": {
                    "pt": "Projeto inválido ou não encontrado.",
                    "en": "Invalid or no project found."
                }
            }
            return render(request, "generic_ml.html", context=context)
        

        tipo = request.POST.get("tipo_recurso")
        dados = {}
        
        if tipo == "github":
            dados["repo_nome"] = request.POST.get("repo_nome")
            dados["repo_descricao"] = request.POST.get("repo_descricao")

            github_users = {}
            for key, value in request.POST.items():
                if key.startswith('github_user_') and value:
                    user_id = int(key.replace('github_user_', ''))
                    github_users[user_id] = value
                    user = get_object_or_404(PFEUser, id=user_id)
                    user.conta_github = value
                    user.save()
            if github_users:
                dados["github_users"] = github_users

            if "repo_publico" in request.POST:
                dados["repo_publico"] = True
                dados["repo_publico_justificativa"] = request.POST.get("repo_publico_justificativa")
            else:
                dados["repo_publico"] = False
                
        elif tipo == "nuvem":
            dados["nuvem_servicos"] = request.POST.get("nuvem_servicos")
            dados["nuvem_finalidade"] = request.POST.get("nuvem_finalidade")
            dados["nuvem_justificativa"] = request.POST.get("nuvem_justificativa")
            
        elif tipo == "overleaf":
            dados["overleaf_nome"] = request.POST.get("overleaf_nome")
            dados["overleaf_descricao"] = request.POST.get("overleaf_descricao")
            
        elif tipo == "equipamento":
            dados["equip_tipo"] = request.POST.get("equip_tipo")
            dados["equip_detalhes"] = request.POST.get("equip_detalhes")
            dados["equip_finalidade"] = request.POST.get("equip_finalidade")
            
        elif tipo == "compra":
            dados["compra_item"] = request.POST.get("compra_item")
            dados["compra_quantidade"] = request.POST.get("compra_quantidade")
            dados["compra_justificativa"] = request.POST.get("compra_justificativa")
            
            # Cotações
            links = request.POST.getlist("cotacao_link[]")
            forns = request.POST.getlist("cotacao_fornecedor[]")
            precos = request.POST.getlist("cotacao_preco[]")
            cotacoes = []
            for i in range(len(links)):
                cotacoes.append({
                    "link": links[i],
                    "fornecedor": forns[i] if i < len(forns) else "",
                    "preco": precos[i] if i < len(precos) else "",
                })
            dados["cotacoes"] = cotacoes
            
        elif tipo == "reuniao":
            dados["reuniao_motivo"] = request.POST.get("reuniao_motivo")
            dados["reuniao_descricao"] = request.POST.get("reuniao_descricao")
            dados["reuniao_horarios"] = request.POST.get("reuniao_horarios")

        elif tipo == "llm":
            dados["llm_estimativa"] = request.POST.get("llm_estimativa")
            dados["llm_justificativa"] = request.POST.get("llm_justificativa")

        if tipo:
            observacoes = request.POST.get("observacoes", "")
            pedido = Pedido.objects.create(
                projeto=projeto,
                solicitante=request.user,
                tipo=tipo,
                dados=json.dumps(dados),
                observacoes=observacoes,
            )

            email_subject = f"Pedido de Recurso: {tipo.capitalize()} - Projeto {projeto.proposta.titulo}"
            email_recipients = [request.user.email]
            email_recipients += [configuracao.coordenacao.user.email]
            email_recipients += [projeto.orientador.user.email] if projeto.orientador else []
            for alocacao in Alocacao.objects.filter(projeto=projeto):
                email_recipients.append(alocacao.aluno.user.email)
            email_message = f"""
                Orientador{"a" if projeto.orientador.user.genero == 'F' else ""} {projeto.orientador.user.get_full_name() if projeto.orientador else ""},<br><br>
                &nbsp;&nbsp;&nbsp;&nbsp;Por favor, responda esse e-mail autorizando o pedido de recurso.<br><br>
                &nbsp;&nbsp;&nbsp;&nbsp;Tipo: {tipo.capitalize()}<br>
                &nbsp;&nbsp;&nbsp;&nbsp;Projeto: {projeto.proposta.titulo}<br>
                &nbsp;&nbsp;&nbsp;&nbsp;Estudantes:<br>
                <div style="margin-left: 20px;">
            """
            for alocacao in Alocacao.objects.filter(projeto=projeto):
                email_message += f"&bull; {alocacao.aluno.user.get_full_name()} &lt;{alocacao.aluno.user.email}&gt;<br>"
            email_message += f"""
                </div><br>
                &nbsp;&nbsp;&nbsp;&nbsp;Solicitante: {request.user.get_full_name()} &lt;{request.user.email}&gt;<br><br>
                &nbsp;&nbsp;&nbsp;&nbsp;Detalhes do pedido:<br>
                <div style="margin-left: 20px;">
                {pedido.get_detalhes_completos()}
                </div><br>
                &nbsp;&nbsp;&nbsp;&nbsp;Observações adicionais:<br>
                <div style="margin-left: 20px;">
                {observacoes if observacoes else "Nenhuma"}
                </div>
            """

            email(email_subject, email_recipients, email_message)

            return redirect("pedir_recursos")

    # Recupera pedidos anteriores
    pedidos = Pedido.objects.filter(projeto=projeto).order_by("-data_solicitacao")

    context = {
        "titulo": {"pt": "Pedir Recursos", "en": "Request Resources"},
        "configuracao": configuracao,
        "Projeto": Projeto,
        "projeto": projeto,
        "pedidos": pedidos,
    }

    # Caso seja Professor ou Administrador
    if request.user.eh_prof_a:
        context["mensagem_aviso"] = {
            "pt": "Mostrando como é a tela, usando qualquer estudante de exemplo.",
            "en": "Showing how the screen looks, using any example student.",
        }

    return render(request, "projetos/pedir_recursos.html", context=context)




@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projeto_avancado(request, primarykey):
    """cria projeto avançado e exibe ele."""
    projeto = get_object_or_404(Projeto, id=primarykey)
    if not Projeto.objects.filter(avancado=projeto).exists():  # Checa se já existe um projeto avançado
        np = copy.copy(projeto)
        np.pk = None  # Para duplicar objeto na base de dados
        np.ano, np.semestre = adianta_semestre_conf(get_object_or_404(Configuracao))
        np.avancado = projeto
        np.save()
    return redirect("projeto_infos", primarykey=np.id)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def carrega_bancos(request):
    """Rotina que carrega arquivo CSV de bancos para base de dados do servidor."""
    with open("bancos.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count != 0:
                banco = Banco.objects.create(nome=row[0], codigo=row[1])
                banco.save()
            line_count += 1
    context = {
        "area_principal": True,
        "mensagem": {"pt": "Bancos carregados.", "en": "Banks loaded."},
    }
    return render(request, "generic_ml.html", context=context)


@login_required
@transaction.atomic
def reembolso_pedir(request):
    """Página com sistema de pedido de reembolso."""
    configuracao = get_object_or_404(Configuracao)
    usuario = get_object_or_404(PFEUser, pk=request.user.pk)

    if request.user.tipo_de_usuario == 1:
        aluno = get_object_or_404(Aluno, pk=request.user.aluno.pk)

        if aluno.ano > configuracao.ano or\
            (aluno.ano == configuracao.ano and aluno.semestre > configuracao.semestre):
            mensagem_erro = {
                "pt": "Projetos ainda não disponíveis para o seu período do Capstone.",
                "en": "Projects not yet available for your Capstone period.",
            }
            context = {
                "area_principal": True,
                "mensagem_erro": mensagem_erro,
            }
            return render(request, "generic_ml.html", context=context)

        projeto = Projeto.objects.filter(alocacao__aluno=aluno).last()
    else:
        projeto = None

    if request.method == "POST":
        reembolso = Reembolso(usuario=usuario)
        reembolso.descricao = request.POST["descricao"]

        cpf = int(''.join(i for i in request.POST["cpf"] if i.isdigit()))

        reembolso.conta = request.POST["conta"]
        reembolso.agencia = request.POST["agencia"]

        reembolso.banco = get_object_or_404(Banco, codigo=request.POST["banco"])

        reembolso.valor = request.POST["valor"]

        reembolso.save()  # Preciso salvar para pegar o PK
        nota_fiscal = simple_upload(request.FILES["arquivo"],
                                    path="reembolsos/",
                                    prefix=str(reembolso.pk)+"_")
        reembolso.nota = nota_fiscal[len(settings.MEDIA_URL):]

        reembolso.save()

        subject = "Capstone | Reembolso: " + usuario.username
        recipient_list = configuracao.recipient_reembolso.split(";")
        recipient_list.append(usuario.email)  # mandar para o usuário que pediu o reembolso
        if projeto:
            if projeto.orientador:  # mandar para o orientador se houver
                recipient_list.append(projeto.orientador.user.email)
        message = message_reembolso(usuario, projeto, reembolso, cpf)
        email(subject, recipient_list, message)
    
        return HttpResponse(message)

    bancos = Banco.objects.all().order_by(Lower("nome"), "codigo")
    context = {
        "titulo": {"pt": "Formulário de Reembolso", "en": "Reimbursement Form"},
        "usuario": usuario,
        "projeto": projeto,
        "bancos": bancos,
        "configuracao": configuracao,
    }
    return render(request, "projetos/reembolso_pedir.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def comite(request):
    """Exibe os professores que estão no comitê do Capstone."""
    context = {
            "professores": Professor.objects.filter(user__membro_comite=True),
            "cabecalhos": [{"pt": "Nome", "en": "Name"}, {"pt": "e-mail", "en": "e-mail"}, {"pt": "Lattes", "en": "Lattes"}, ],
            "titulo": {"pt": "Comitê do Capstone", "en": "Capstone Committee"},
        }
    return render(request, "projetos/comite.html", context)


@login_required
def reunioes(request, todos=None):
    """Exibe as reuniões do Capstone."""

    if todos and not request.user.eh_admin:
        return HttpResponse("Acesso não autorizado.", status=401)

    configuracao = get_object_or_404(Configuracao)
    if request.user.eh_estud:
        alocacao = Alocacao.objects.filter(aluno=request.user.aluno, projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre).last()
        associado = Associado.objects.filter(estudante=request.user.aluno, projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre).last()
        if alocacao:
            reunioes = Reuniao.objects.filter(projeto=alocacao.projeto)
        elif associado:
            reunioes = Reuniao.objects.filter(projeto=associado.projeto)
        else:
            return HttpResponse("Nenhuma alocação encontrada.", status=404)
        
    elif request.user.eh_prof_a:
        if todos:
            reunioes = Reuniao.objects.filter(projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre)
        else:
            projetos = Projeto.objects.filter(orientador=request.user.professor, ano=configuracao.ano, semestre=configuracao.semestre)
            reunioes = Reuniao.objects.filter(projeto__in=projetos)
    else:
        return HttpResponse("Acesso não autorizado.", status=401)

    context = {
            "cabecalhos": [
                {"pt": "Título", "en": "Title"},
                {"pt": "Projeto", "en": "Project"},
                {"pt": "Data", "en": "Date", "tipo": "data_hora"},
                {"pt": "Local", "en": "Location"},
                {"pt": "Participantes", "en": "Participants"}
            ],
            "titulo": {"pt": "Reuniões do Projeto", "en": "Project Meetings"},
            "reunioes": reunioes,
            "todos": todos if todos else "",  # Usado para o criar reunioes
        }
    return render(request, "projetos/reunioes.html", context)


@login_required
@transaction.atomic
def reuniao(request, reuniao_id_g=None):  # Id da reunião para editar, None para criar nova ou TODOS para listar todos projetos
    """Formulário para estudantes preencherem os anotações de reuniões."""
    usuario_sem_acesso(request, (1, 2, 4,)) # Est, Prof, Adm
    configuracao = get_object_or_404(Configuracao)

    context = {
        "titulo": {"pt": "Registra Reunião", "en": "Register Meeting"},
        "area_principal": True,
        "Reuniao": Reuniao,
        "envolvidos": {},
    }
    
    reuniao = get_object_or_404(Reuniao, id=int(reuniao_id_g)) if (reuniao_id_g and reuniao_id_g != "todos") else None

    if request.user.eh_estud:  # Estudante

        alocacao = Alocacao.objects.filter(aluno=request.user.aluno,
                                           projeto__ano=configuracao.ano,
                                           projeto__semestre=configuracao.semestre).last()

        associados = Associado.objects.filter(estudante=request.user.aluno,
                                             projeto__ano=configuracao.ano, 
                                             projeto__semestre=configuracao.semestre)

        if reuniao:
            if not alocacao and not associados:
                context["mensagem"] = {"pt": "Você não tem permissão para visualizar/editar essa reunião.", "en": "You do not have permission to edit this meeting."}
                return render(request, "generic_ml.html", context=context)
            elif alocacao and reuniao.projeto != alocacao.projeto:
                context["mensagem"] = {"pt": "Você não tem permissão para visualizar/editar essa reunião.", "en": "You do not have permission to edit this meeting."}
                return render(request, "generic_ml.html", context=context)
            elif associados and reuniao.projeto not in [associado.projeto for associado in associados]:
                context["mensagem"] = {"pt": "Você não tem permissão para visualizar/editar essa reunião.", "en": "You do not have permission to edit this meeting."}
                return render(request, "generic_ml.html", context=context)

        if alocacao:
            projetos = [alocacao.projeto]
        elif associados:
            projetos = [associado.projeto for associado in associados]
        else:
            context["mensagem"] = {"pt": "Você não está alocado em um projeto esse semestre.", "en": "You are not allocated to a project this semester."}
            return render(request, "generic_ml.html", context=context)

    elif request.user.eh_prof_a:  # Professor
        if request.user.eh_admin and reuniao_id_g == "todos":
            projetos = Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre)
        else:
            projetos = Projeto.objects.filter(orientador=request.user.professor, ano=configuracao.ano, semestre=configuracao.semestre)

        if not projetos:
            context["mensagem"] = {"pt": "Você não tem projetos para registrar reuniões nesse semestre.", "en": "You do not have projects to register meetings this semester."}
            return render(request, "generic_ml.html", context=context)


    else:  # Outros usuários (não estudantes ou professores)
        context["mensagem"] = {"pt": "Você não tem permissão para registrar reuniões.", "en": "You do not have permission to register meetings."}
        return render(request, "generic_ml.html", context=context)

    context["projetos"] = projetos

    if reuniao:
        context["reuniao"] = reuniao
        context["titulo"] = {"pt": "Editar Reunião", "en": "Edit Meeting"}

    for projeto in context["projetos"]:
        context["envolvidos"][projeto.id] = recupera_envolvidos(projeto, reuniao=reuniao)

    if request.method == "POST":

        if reuniao is None:
            reuniao = Reuniao.objects.create()
        elif "remover" in request.POST:
            ReuniaoParticipante.objects.filter(reuniao=reuniao).delete()
            reuniao.delete()
            context["mensagem"] = {"pt": "Reunião removida!", "en": "Meeting removed!"}
            return render(request, "generic_ml.html", context=context)

        
        projeto_id = request.POST.get("projeto", None)
        reuniao.projeto = get_object_or_404(Projeto, id=projeto_id)

        if reuniao.projeto not in projetos:
            context["mensagem"] = {"pt": "Você não tem permissão para registrar reuniões nesse projeto.", "en": "You do not have permission to register meetings for this project."}
            return render(request, "generic_ml.html", context=context)

        if request.user.eh_estud and reuniao.travado:
            context["mensagem"] = {"pt": "Você não pode editar reuniões travadas.", "en": "You cannot edit locked meetings."}
            return render(request, "generic_ml.html", context=context)

        reuniao.titulo = request.POST.get("titulo", "")
        reuniao.data_hora = datetime.datetime.strptime(request.POST["data_hora"], "%Y-%m-%dT%H:%M")
        reuniao.local = request.POST.get("local", "")
        reuniao.anotacoes = request.POST.get("anotacoes", None)
        reuniao.travado = "travado" in request.POST
        reuniao.usuario = request.user
        reuniao.save()

        participantes = anota_participacao(request.POST, reuniao=reuniao)
        
        if "enviar_mensagem" in request.POST:
            if reuniao.projeto:
                subject = "Capstone | Anotações de Reunião (" + reuniao.titulo + ")"
                recipient_list = []
                alocacoes = Alocacao.objects.filter(projeto=reuniao.projeto)
                for alocacao in alocacoes:
                    recipient_list.append(alocacao.aluno.user.email)
                if reuniao.projeto.orientador:
                    recipient_list.append(reuniao.projeto.orientador.user.email)
                for coorientador in Coorientador.objects.filter(projeto=reuniao.projeto):
                    recipient_list.append(coorientador.usuario.email)
                for participante in participantes:
                    usuario, situacao = participante
                    if situacao == "Presente" and  usuario.email not in recipient_list:
                        recipient_list.append(usuario.email)
                # recipient_list.append(str(configuracao.coordenacao.user.email))

                context_email = {
                    "reuniao": reuniao,
                    "configuracao": configuracao
                }
                message = render_message("Anotações de Reunião", context_email)

                email(subject, recipient_list, message)

        context["mensagem"] = {"pt": "Reunião registrada com sucesso!<br><b>Horário de recebimento:</b> " + reuniao.criacao.strftime('%d/%m/%Y, %H:%M:%S'), 
                               "en": "Meeting successfully registered!<br><b>Submission time:</b> " + reuniao.criacao.strftime('%d/%m/%Y, %H:%M:%S')}
        return render(request, "generic_ml.html", context=context)

    return render(request, "projetos/reuniao.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def despesas(request):
    """Exibe as despesas do Capstone."""
    configuracao = get_object_or_404(Configuracao)

    if request.method == "POST":
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                despesas = Despesa.objects.all()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    despesas = Despesa.objects.filter(data__year=ano)
                elif semestre == "1":
                    despesas = Despesa.objects.filter(data__year=ano, data__month__lte=6)
                else:  # semestre == '2':
                    despesas = Despesa.objects.filter(data__year=ano, data__month__gte=7)

        despesa_por_tipo = {}
        for despesa in despesas:
            tipo = despesa.get_tipo_de_despesa_display()
            if tipo not in despesa_por_tipo:
                despesa_por_tipo[tipo] = 0
            if despesa.valor_r:
                despesa_por_tipo[tipo] += despesa.valor_r
            elif despesa.valor_d:
                despesa_por_tipo[tipo] += despesa.valor_d * configuracao.cotacao_dolar
        
        context = {
                "despesas": despesas,
                "cotacao_dolar": configuracao.cotacao_dolar,
                "despesa_por_tipo": despesa_por_tipo,
                "cabecalhos": [ {"pt": "Data", "en": "Date", "tipo": "data"},
                                {"pt": "Tipo", "en": "Type"},
                                {"pt": "Valor", "en": "Value"},
                                {"pt": "Descrição", "en": "Description"},
                                {"pt": "Fornecedor", "en": "Supplier"},
                                {"pt": "Projeto", "en": "Project"}, ],
            }
    else:

        context = {
            "titulo": {"pt": "Despesas", "en": "Expenses"},
            "edicoes": get_edicoes(Projeto, anual=True)[0],
        }
    
    return render(request, "projetos/despesas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_feedback(request):
    """Lista todos os feedback das Organizações Parceiras."""
    edicoes = get_edicoes(Projeto)[0]
    
    # primeiro ano foi diferente (edição anual em 2018.2)
    num_projetos = [Projeto.objects.filter(ano=2018, semestre=2).count()]
    num_feedbacks = [Feedback.objects.filter(data__range=["2018-06-01", "2019-05-31"]).count()]

    for ano, semestre in [edicao.split('.') for edicao in edicoes[1:]]:
        num_projetos.append(Projeto.objects.filter(ano=ano, semestre=semestre).count())
        if semestre == '1':
            faixa = [ano+"-06-01", ano+"-12-31"]
        else:
            faixa = [str(int(ano)+1)+"-01-01", str(int(ano)+1)+"-05-31"]
        num_feedbacks.append(Feedback.objects.filter(data__range=faixa).count())

    context = {
        "titulo": {"pt": "Feedbacks das Organizações Parceiras", "en": "Feedback from Partner Organizations"},
        "feedbacks": Feedback.objects.all().order_by("-data"),
        "edicoes": edicoes,
        "num_projetos": num_projetos,
        "num_feedbacks": num_feedbacks,
    }
    return render(request, "projetos/lista_feedback.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_feedback_estudantes(request):
    """Lista todos os feedback das Organizações Parceiras."""
    configuracao = get_object_or_404(Configuracao)
    edicoes = get_edicoes(Projeto)[0]

    recomendaria = [0, 0, 0]
    primeira_opcao = [0, 0]
    proposta = [0, 0, 0, 0, 0]
    trabalhando = [0, 0, 0, 0]

    if request.method == "POST":

        todos_feedbacks = FeedbackEstudante.objects.all().order_by("-momento")

        num_feedbacks = []
        num_estudantes = []

        for ano, semestre in [edicao.split('.') for edicao in edicoes]:
            
            estudantes = Aluno.objects.filter(ano=ano, semestre=semestre).count()
            num_estudantes.append(estudantes)

            numb_feedb = todos_feedbacks.filter(projeto__ano=ano, projeto__semestre=semestre).\
                values("estudante").distinct().count()
            num_feedbacks.append(numb_feedb)

        alocacoes = Alocacao.objects.filter(aluno__trancado=False, aluno__externo__isnull=True)

        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao != "todas":
                ano, semestre = edicao.split('.')
                alocacoes = alocacoes.filter(projeto__ano=ano, projeto__semestre=semestre)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        projetos = []
        feedbacks = []
        for alocacao in alocacoes:
            
            projetos.append(alocacao.projeto)
            
            feedback = todos_feedbacks.filter(projeto=alocacao.projeto, estudante=alocacao.aluno).last()
            
            if feedback:
                feedbacks.append(feedback)
                if feedback.recomendaria:
                    recomendaria[feedback.recomendaria-1] += 1
                if feedback.primeira_opcao != None:
                    primeira_opcao[0 if feedback.primeira_opcao else 1] += 1
                if feedback.proposta:
                    proposta[feedback.proposta-1] += 1
                if feedback.trabalhando:
                    trabalhando[feedback.trabalhando-1] += 1
            else:
                feedbacks.append(None)

        estudantes = zip(alocacoes, projetos, feedbacks)

        context = {
            "edicoes": edicoes,
            "num_estudantes": num_estudantes,
            "num_feedbacks": num_feedbacks,
            "estudantes": estudantes,
            "coordenacao": configuracao.coordenacao,
            "recomendaria": recomendaria,
            "primeira_opcao": primeira_opcao,
            "proposta": proposta,
            "trabalhando": trabalhando,

            "cabecalhos": [{"pt": "Nome", "en": "Name"},
                           {"pt": "Projeto", "en": "Project"}, 
                           {"pt": "Data", "en": "Date", "tipo": "data"}, 
                           {"pt": "Mensagem", "en": "Message"}, ],
        }

    else:
        context = {
            "titulo": {"pt": "Feedbacks Finais dos Estudantes", "en": "Final Feedback from Students"},
            "edicoes": edicoes,
            "recomendaria": recomendaria,
            "primeira_opcao": primeira_opcao,
            "proposta": proposta,
            "trabalhando": trabalhando,
        }

    return render(request, "projetos/lista_feedback_estudantes.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_acompanhamento(request):
    """Lista todos os acompanhamentos das Organizações Parceiras."""
    context = {
        "titulo": {"pt": "Acompanhamentos nas Organizações", "en": "Organizations Follow-up"},
        "acompanhamentos": Acompanhamento.objects.all().order_by("-data")
        }
    return render(request, "projetos/lista_acompanhamento.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mostra_feedback(request, feedback_id):
    """Detalha os feedbacks das Organizações Parceiras."""
    context = {
        "titulo": {"pt": "Feedback de Organizações Parceiras", "en": "Feedback from Partner Organizations"},
        "feedback": get_object_or_404(Feedback, id=feedback_id)
        }
    return render(request, "projetos/mostra_feedback.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mostra_feedback_estudante(request, feedback_id):
    """Detalha os feedbacks dos Estudantes."""
    feedback = get_object_or_404(FeedbackEstudante, id=feedback_id)
    context = {
        "feedback": feedback,
        "usuario": feedback.estudante.user,
        "projeto": feedback.projeto,
        "organizacao": feedback.projeto.proposta.organizacao,
        }
    return render(request, "estudantes/estudante_feedback.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def validate_aviso(request):
    """Ajax para validar avisos."""
    aviso_id = int(request.GET.get("aviso", None)[len("aviso"):])
    checked = request.GET.get("checked", None) == "true"
    value = request.GET.get("value", None)

    aviso = get_object_or_404(Aviso, id=aviso_id)

    datas_realizado = json.loads(aviso.datas_realizado)

    if checked:
        # Marca a data do aviso
        if value not in datas_realizado:
            datas_realizado.append(value)
            aviso.datas_realizado = json.dumps(datas_realizado)
    else:
        # Desmarca a data do aviso
        if value in datas_realizado:
            datas_realizado.remove(value)
            aviso.datas_realizado = json.dumps(datas_realizado)
    aviso.save()
    return JsonResponse({"atualizado": True,})


@login_required
@permission_required("projetos.view_projeto", raise_exception=True)
def projetos_vs_propostas(request):
    """Mostra graficos das evoluções dos projetos e propostas."""
    edicoes = get_edicoes(Proposta)[0]

    total_org_propostas = {}
    total_org_projetos = {}

    # PROPOSTAS e ORGANIZACOES COM PROPOSTAS
    num_propostas_submetidas = []
    nome_propostas_submetidas = []
    num_propostas_aceitas = []
    nome_propostas_aceitas = []
    org_propostas = []
    for edicao in edicoes:

        ano_projeto, semestre = edicao.split('.')

        propostas = Proposta.objects.filter(ano=ano_projeto, semestre=semestre)
        num_propostas_submetidas.append(propostas.count())
        nome_propostas_submetidas.append(propostas)

        propostas_aceitas = propostas.filter(disponivel=True)
        num_propostas_aceitas.append(propostas_aceitas.count())
        nome_propostas_aceitas.append(propostas_aceitas)

        tmp_org = {}
        for projeto in propostas:
            if projeto.organizacao:
                tmp_org[projeto.organizacao.id] = "True"
                total_org_propostas[projeto.organizacao.id] = "True"
        org_propostas.append(len(tmp_org))

    # PROJETOS e ORGANIZACOES COM PROJETOS
    num_projetos = []
    org_projetos = []
    nome_projetos = []

    segmentos = list(Segmento.objects.all())
    org_segmentos = {}
    total_org_segmentos = {}
    for segmento in segmentos:
        org_segmentos[segmento] = []
        total_org_segmentos[segmento] = 0

    for edicao in edicoes:

        ano_projeto, semestre = edicao.split('.')

        projetos = Projeto.objects.filter(ano=ano_projeto, semestre=semestre)
        nome_projetos.append(projetos)
        num_projetos.append(projetos.count())
        tmp_org = {}

        tmp_segmentos = {}
        for segmento in segmentos:
            tmp_segmentos[segmento] = 0
        for projeto in projetos:
            if projeto.organizacao:
                tmp_org[projeto.organizacao.id] = "True"
                total_org_projetos[projeto.organizacao.id] = "True"
                if projeto.organizacao.segmento:    # Segmentos por organização
                    tmp_segmentos[projeto.organizacao.segmento] += 1
                    total_org_segmentos[projeto.organizacao.segmento] += 1
        org_projetos.append(len(tmp_org))
        for segmento in segmentos:
            org_segmentos[segmento].append(tmp_segmentos[segmento])

    # ORGANIZACOES PROSPECTADAS
    org_prospectadas = []
    todas_organizacoes = Organizacao.objects.all()
    for edicao in edicoes:

        ano_projeto, _ = edicao.split('.')
        # Diferente dos outros, aqui se olha quem foi prospectado no semestre anterior

        # Primeiro Semestre
        count_organizacoes = 0
        for organizacao in todas_organizacoes:
            if Anotacao.objects.filter(organizacao=organizacao,
                                       momento__year=ano_projeto,
                                       momento__month__lt=7).exists():
                count_organizacoes += 1
        org_prospectadas.append(count_organizacoes)

        # Segundo Semeste
        count_organizacoes = 0
        for organizacao in todas_organizacoes:
            if Anotacao.objects.filter(organizacao=organizacao,
                                       momento__year=ano_projeto,
                                       momento__month__gt=6).exists():
                count_organizacoes += 1
        org_prospectadas.append(count_organizacoes)

    context = {
        "titulo": {"pt": "Organizações, Projetos e Propostas", "en": "Organizations, Projects and Proposals"},
        "num_propostas_submetidas": num_propostas_submetidas,
        "nome_propostas_submetidas": nome_propostas_submetidas,
        "num_propostas_aceitas": num_propostas_aceitas,
        "nome_propostas_aceitas": nome_propostas_aceitas,
        "num_projetos": num_projetos,
        "nome_projetos": nome_projetos,
        "total_propostas": sum(num_propostas_submetidas),
        "total_projetos": sum(num_projetos),
        "org_prospectadas": org_prospectadas,
        "org_propostas": org_propostas,
        "org_projetos": org_projetos,
        "total_org_propostas": len(total_org_propostas),
        "total_org_projetos": len(total_org_projetos),
        "org_segmentos": org_segmentos,
        "total_org_segmentos": total_org_segmentos,
        "edicoes": edicoes,
    }

    return render(request, "projetos/projetos_vs_propostas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def analise_notas(request):
    """Mostra analise de notas."""
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.method == "POST":
        
        medias_semestre = Alocacao.objects.all()
        
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        
        if request.POST["edicao"] != "todas":
            ano, semestre = map(int, request.POST["edicao"].split('.'))
            medias_semestre = medias_semestre.filter(projeto__ano=ano, projeto__semestre=semestre)
        
        curso = request.POST.get("curso")
        if curso != "TE":  # Filtra para projetos com estudantes de um curso específico
            if curso != 'T':
                medias_semestre = medias_semestre.filter(aluno__curso2__sigla_curta=curso)
            else:
                medias_semestre = medias_semestre.filter(aluno__curso2__in=cursos_insper)

        valor = {"ideal": 7.0, "regular": 5.0}

        # Criando espaço para todos as notas
        notas_keys = []
        for exame in Exame.objects.all():
            notas_keys.append(exame.sigla)

        notas = {key: {"ideal": 0, "regular": 0, "inferior": 0} for key in notas_keys}

        notas_lista = [get_notas_alocacao(x) for x in medias_semestre]
        for nota2 in notas_lista:
            for nota in nota2:
                if nota["nota"] is not None:
                    key = nota["exame"].sigla
                    if key:
                        if nota["nota"] >= valor["ideal"]:
                            notas[key]["ideal"] += 1
                        elif nota["nota"] >= valor["regular"]:
                            notas[key]["regular"] += 1
                        else:
                            notas[key]["inferior"] += 1
        medias_lista = [get_media_alocacao_i(x) for x in medias_semestre]

        # Somente apresenta as médias que esteja completas (pesso = 100%)
        medias_validas = list(filter(lambda d: d["pesos"] == 1.0, medias_lista))

        medias = {}
        medias["ideal"] = len(list(filter(lambda d: d["media"] is not None and valor["ideal"] is not None and d["media"] >= valor["ideal"], medias_validas)))
        medias["regular"] = len(list(filter(lambda d: d["media"] is not None and valor["ideal"] is not None and valor["regular"] is not None and valor["ideal"] > d["media"] >= valor["regular"], medias_validas)))
        medias["inferior"] = len(list(filter(lambda d: d["media"] is not None and valor["regular"] is not None and d["media"] < valor["regular"], medias_validas)))
        medias["total"] = len(medias_validas)

        context = {
            "medias": medias,
            "notas": notas,
            "curso": curso,
        }

    else:
        context = {
            "titulo": {"pt": "Análise de Notas/Conceitos", "en": "Analysis of Grades/Concepts"},
            "edicoes": get_edicoes(Avaliacao2)[0],
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "projetos/analise_notas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def certificacao_falconi(request):
    """Mostra graficos das certificacões Falconi."""
    configuracao = get_object_or_404(Configuracao)

    edicoes, _, _ = get_edicoes(Projeto)

    # cortando ["2018.2", "2019.1", "2019.2", "2020.1", ....]
    edicoes = edicoes[4:]

    if request.method == "POST":

        if "edicao" in request.POST:
            if request.POST["edicao"] != "todas":
                ano, semestre = request.POST["edicao"].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        # conceitos = I, D, C, C+, B, B+, A, A+
        conceitos = [0, 0, 0, 0, 0, 0, 0, 0]
        total = len(projetos)
        selecionados = 0
        projetos_selecionados = []
        for projeto in projetos:
            exame = Exame.objects.get(sigla="F")
            aval_banc_falconi = Avaliacao2.objects.filter(projeto=projeto, exame=exame)  # Falc.

            if aval_banc_falconi:
                projetos_selecionados.append(projeto)

            banca_info = get_banca_estudante(aval_banc_falconi, projeto.ano, projeto.semestre)
            nota_banca_falconi = banca_info["media"]
            peso = banca_info["peso"]
            avaliadores = banca_info["avaliadores"]

            if peso is not None:
                selecionados += 1
                if nota_banca_falconi >= 9.99:  # conceito A+
                    conceitos[7] += 1
                elif nota_banca_falconi >= 9.0:  # conceito A
                    conceitos[6] += 1
                elif nota_banca_falconi >= 8.0:  # conceito B+
                    conceitos[5] += 1
                elif nota_banca_falconi >= 7.0:  # conceito B
                    conceitos[4] += 1
                elif nota_banca_falconi >= 6.0:  # conceito C+
                    conceitos[3] += 1
                elif nota_banca_falconi >= 5.0:  # conceito C
                    conceitos[2] += 1
                elif nota_banca_falconi >= 1.0:  # Qualquer D
                    conceitos[1] += 1
                else:
                    conceitos[0] += 1  # conceito I

        if selecionados:
            for i in range(8):
                conceitos[i] *= 100/selecionados


        # Para as avaliações individuais
        objetivos = ObjetivosDeAprendizagem.objects.all()

        avaliadores = []

        for projeto in projetos_selecionados:

            avaliadores_falconi = {}

            for objetivo in objetivos:

                # Bancas Falconi
                exame = Exame.objects.get(sigla="F")
                bancas_falconi = Avaliacao2.objects.filter(projeto=projeto,
                                                        objetivo=objetivo,
                                                        exame=exame)\
                    .order_by("avaliador", "-momento")

                for banca in bancas_falconi:
                    if banca.avaliador not in avaliadores_falconi:
                        avaliadores_falconi[banca.avaliador] = {}
                    if objetivo not in avaliadores_falconi[banca.avaliador]:
                        avaliadores_falconi[banca.avaliador][objetivo] = banca
                        avaliadores_falconi[banca.avaliador]["momento"] = banca.momento
                    # Senão é só uma avaliação de objetivo mais antiga

            # Bancas Falconi
            exame = Exame.objects.get(sigla="F")
            observacoes = Observacao.objects.filter(projeto=projeto, exame=exame).\
                order_by("avaliador", "-momento")
            for observacao in observacoes:
                if observacao.avaliador not in avaliadores_falconi:
                    avaliadores_falconi[observacao.avaliador] = {}  # Não devia acontecer isso
                if "observacoes_orientador" not in avaliadores_falconi[observacao.avaliador]:
                    avaliadores_falconi[observacao.avaliador]["observacoes_orientador"] = observacao.observacoes_orientador
                # Senão é só uma avaliação de objetivo mais antiga

            avaliadores.append(avaliadores_falconi)

        bancas = zip(projetos_selecionados, avaliadores)

        context = {
            "ano": configuracao.ano,
            "semestre": configuracao.semestre,
            "edicoes": edicoes,
            "selecionados": selecionados,
            "nao_selecionados": total - selecionados,
            "conceitos": conceitos,
            "projetos_selecionados": projetos_selecionados,
            "objetivos": objetivos,
            "bancas": bancas,
        }

    else:
        context = {
            "titulo": {"pt": "Análise dos Conceitos das Certificações Falconi", "en": "Analysis of Falconi Certifications"},
            "edicoes": edicoes,
        }

    return render(request, "projetos/certificacao_falconi.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def analise_objetivos(request):
    """Mostra análise de objetivos de aprendizagem."""
    edicoes, _, _ = get_edicoes(Avaliacao2)
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.method == "POST":

        alocacoes = Alocacao.objects.all()

        periodo = ["todo", "periodo"]

        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        
        if request.POST["edicao"] != "todas":
            periodo = request.POST["edicao"].split('.')
            alocacoes = alocacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])

        if "curso" in request.POST:
            curso = request.POST["curso"]

            # Filtra para alocações de estudantes de um curso específico
            if curso != "TE":
                if curso != 'T':
                    alocacoes = alocacoes.filter(aluno__curso2__sigla_curta=curso)
                else:
                    alocacoes = alocacoes.filter(aluno__curso2__in=cursos_insper)
                
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        context = calcula_objetivos(alocacoes)
        context["edicoes"] = edicoes
        context["total_geral"] = len(alocacoes)

    else:
        context = {
            "titulo": {"pt": "Análise por Objetivos de Aprendizado", "en": "Analysis by Learning Goals"},
            "edicoes": edicoes,
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "projetos/analise_objetivos.html", context)

from collections import defaultdict


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_notas(request):
    """Mostra graficos das evoluções das notas."""
    edicoes = get_edicoes(Avaliacao2)[0]
    cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")

    if request.method == "POST":

        avaliacoes = Avaliacao2.objects.all()
        alocacoes = Alocacao.objects.all()

        if "curso" in request.POST:
            curso = request.POST["curso"]
            if curso != 'T':
                avaliacoes = avaliacoes.filter(alocacao__aluno__curso2__sigla_curta=curso)
                alocacoes = alocacoes.filter(aluno__curso2__sigla_curta=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        # Para armazenar todas as notas de todos os programas
        notas_total = defaultdict(list)

        # Filter avaliacoes for the specific exames
        exames_titulos = ["Relatório Intermediário Individual", "Relatório Final Individual"]
        avaliacoes = avaliacoes.filter(exame__titulo__in=exames_titulos)

        medias_individuais = []

        for t_curso in cursos:
            notas = []
            for edicao in edicoes:
                periodo = edicao.split('.')
                semestre = avaliacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
                notas_lista = [x.nota for x in semestre if x.alocacao and x.alocacao.aluno.curso2 == t_curso]
                notas_total[edicao].extend(notas_lista)
                notas.append(media(notas_lista))
            
            if any(nota is not None for nota in notas):  # Check if notas is not empty
                medias_individuais.append({"curso": t_curso, "media": notas})

        if len(medias_individuais) > 1:
            notas = [media(notas_total[edicao]) for edicao in edicoes]
            medias_individuais.append({"curso": {"sigla": "média dos cursos", "cor": "000000"}, "media": notas})

        # Para armazenar todas as notas de todos os programas
            notas_total = defaultdict(list)

        # Médias gerais totais
        medias_gerais = []

        for t_curso in cursos:
            notas = []
            for edicao in edicoes:
                periodo = edicao.split('.')
                alocacoes_tmp = alocacoes.filter(projeto__ano=periodo[0],
                                                projeto__semestre=periodo[1],
                                                aluno__curso2=t_curso)
                notas_lista = [get_media_alocacao_i(alocacao)["media"] for alocacao in alocacoes_tmp if get_media_alocacao_i(alocacao)["pesos"] == 1]

                notas_total[edicao].extend(notas_lista)
                notas.append(media(notas_lista))
            
            if any(nota is not None for nota in notas):  # Check if notas is not empty
                medias_gerais.append({"curso": t_curso, "media": notas})

        if len(medias_gerais) > 1:
            notas = [media(notas_total[edicao]) for edicao in edicoes]
            medias_gerais.append({"curso": {"sigla": "média dos cursos", "cor": "000000"}, "media": notas})

        context = {
            "medias_individuais": medias_individuais,
            "medias_gerais": medias_gerais,
            "edicoes": edicoes,
            "curso": curso,
        }

    else:
        context = {
            "titulo": {"pt": "Evolução por Notas/Conceitos", "en": "Evolution by Grades"},
            "edicoes": edicoes,
            "cursos": cursos,
        }

    return render(request, "projetos/evolucao_notas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_objetivos(request):
    """Mostra graficos das evoluções por objetivo de aprendizagem."""
    configuracao = get_object_or_404(Configuracao)
    edicoes = get_edicoes(Avaliacao2)[0]

    if request.method == "POST":

        if "curso" in request.POST:
            curso = request.POST["curso"]
            grupo = "grupo" in request.POST and request.POST["grupo"]=="true"
            individuais = "individuais" in request.POST and request.POST["individuais"]=="true"
            so_finais = "so_finais" in request.POST and request.POST["so_finais"]=="true"

            if so_finais:
                # Somenete avaliações finais do Capstone
                exames = Exame.objects.filter(titulo__in=[
                    "Banca Final",
                    "Relatório Final de Grupo",
                    "Relatório Final Individual",
                    "Avaliação Final Individual",
                    "Avaliação Final de Grupo"
                ])
                avaliacoes_sep = Avaliacao2.objects.filter(exame__in=exames)
            else:
                avaliacoes_sep = Avaliacao2.objects.all()

            if curso == 'T':

                # Avaliações Individuais
                if (individuais):
                    avaliacoes_ind = avaliacoes_sep.filter(alocacao__isnull=False)
                else:
                    avaliacoes_ind = avaliacoes_sep.none()

                # Avaliações Grupais
                if grupo:
                    avaliacoes_grupo = avaliacoes_sep.filter(alocacao__isnull=True, projeto__isnull=False)
                else:
                    avaliacoes_grupo = avaliacoes_sep.none()

                avaliacoes = avaliacoes_ind | avaliacoes_grupo

            else:

                # Avaliações Individuais
                if (individuais):
                    avaliacoes_ind = avaliacoes_sep.filter(alocacao__aluno__curso2__sigla_curta=curso)
                else:
                    avaliacoes_ind = avaliacoes_sep.none()

                # Avaliações Grupais
                if grupo:
                    # identificando projetos com estudantes do curso (pelo menos um)
                    projetos_selecionados = []
                    projetos = Projeto.objects.all()
                    for projeto in projetos:
                        alocacoes = Alocacao.objects.filter(projeto=projeto)
                        for alocacao in alocacoes:
                            if alocacao.aluno.curso2.sigla_curta == curso:
                                projetos_selecionados.append(projeto)
                                break
                            
                    avaliacoes_grupo = Avaliacao2.objects.filter(alocacao__isnull=True, projeto__in=projetos_selecionados)

                else:
                    avaliacoes_grupo = Avaliacao2.objects.none()

                avaliacoes = avaliacoes_ind | avaliacoes_grupo

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        cores = [
            "#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9", "#7cfa9f",
            "#e8c3b9", "#c45890", "#b76353", "#a48577", "#ffd3b6",
            "#b5ead7", "#ffdac1", "#e2f0cb", "#c7ceea", "#f2b5d4",
            "#b3d9ff", "#d4a5a5", "#e0bbff", "#ffb7b2", "#bae1ff"
        ]

        medias = []
        objetivos = ObjetivosDeAprendizagem.objects.all()
        count = 0

        # Precompute all avaliacoes and group them by edicao and objetivo
        avaliacoes_by_edicao_objetivo = {
            edicao: {
                objetivo: [
                    x.nota for x in avaliacoes.filter(
                        projeto__ano=edicao.split('.')[0],
                        projeto__semestre=edicao.split('.')[1],
                        objetivo=objetivo,
                        na=False
                    )
                ]
                for objetivo in objetivos
            }
            for edicao in edicoes
        }

        for objetivo in objetivos:
            notas = []
            faixas = []
            for edicao in edicoes:
                notas_lista = avaliacoes_by_edicao_objetivo[edicao][objetivo]
                faixa = divide57(notas_lista)
                soma = sum(faixa)
                if soma > 0:
                    faixa = [100 * f / soma for f in faixa]
                notas.append(media(notas_lista))
                faixas.append(faixa)

            medias.append({"objetivo": objetivo, "media": notas, "cor": cores[count], "faixas": faixas})
            count += 1

        # Número de estudantes alocados por semestre
        alocacoes = []
        if curso == 'T':
            alocados = Alocacao.objects.all() #filter(projeto__ano=configuracao.ano, semestre=configuracao.semestre)
        else:
            alocados = Alocacao.objects.filter(aluno__curso2__sigla_curta=curso) # , projeto__ano=configuracao.ano, semestre=configuracao.semestre)
        for edicao in edicoes:
            periodo = edicao.split('.')
            alocacoes.append(alocados.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1]).count())

        context = {
            "medias": medias,
            "ano": configuracao.ano,
            "semestre": configuracao.semestre,
            "edicoes": edicoes,
            "curso": curso,
            "alocacoes": alocacoes,
        }

    else:

        context = {
            "titulo": {"pt": "Evolução nos Objetivos de Aprendizado", "en": "Evolution in Learning Goals"},
            "edicoes": edicoes,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, "projetos/evolucao_objetivos.html", context)


@login_required
@permission_required("projetos.view_projeto", raise_exception=True)
def filtro_projetos(request):
    """Filtra os projetos."""
    if request.method == "POST":
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        edicao = request.POST["edicao"]
        if edicao == "todas":
            projetos_filtrados = Projeto.objects.all()
        else:
            ano, semestre = request.POST["edicao"].split('.')
            projetos_filtrados = Projeto.objects.filter(ano=ano, semestre=semestre)

        cabecalhos = [{"pt": "Projeto", "en": "Project"},
                        {"pt": "Áreas", "en": "Areas"},
                        {"pt": "Estudantes", "en": "Students"},
                        {"pt": "Período", "en": "Period"},
                        {"pt": "Orientador", "en": "Advisor"},
                        {"pt": "Organização", "en": "Organization"},
                        {"pt": "Orientador", "en": "Advisor"},
                        {"pt": "Bancas", "en": "Examination Boards"},
                        {"pt": "Falconi", "en": "Falconi"},
                        {"pt": "Média", "en": "Average"}
                        ]

        context = {
            "projetos": projetos_filtrados,
            "cabecalhos": cabecalhos,
        }
    
            
    else:
        context = {
            "titulo": {"pt": "Filtro para Projetos", "en": "Filter for Projects"},
            "edicoes": get_edicoes(Projeto)[0],
            "areas_de_interesse_possiveis": Area.objects.filter(ativa=True),
        }

    return render(request, "projetos/filtro_projetos.html", context)


@login_required
@permission_required("projetos.view_projeto", raise_exception=True)
def interesses_projetos(request):
    """Verifica interesse para com projetos (na verdade verifico as propostas)."""

    if request.method == "POST":
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                projetos = Projeto.objects.all()
                propostas = Proposta.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)
                propostas = Proposta.objects.filter(ano=ano, semestre=semestre)
  
            context = {
                "propostas": propostas,
                "projetos": projetos,
                "aprimorar": propostas.filter(aprimorar=True).count(),
                "realizar": propostas.filter(realizar=True).count(),
                "iniciar": propostas.filter(iniciar=True).count(),
                "identificar": propostas.filter(identificar=True).count(),
                "mentorar": propostas.filter(mentorar=True).count(),
                "tipo_interesse": Proposta.TIPO_INTERESSE,
            }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        context = {
            "titulo": {"pt": "Interesses com Projetos", "en": "Interests with Projects"},
            "edicoes": get_edicoes(Projeto)[0],
        }

    return render(request, "projetos/interesses_projetos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_por_objetivo(request):
    """Mostra graficos das evoluções por objetivo de aprendizagem."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, semestre = get_edicoes(Avaliacao2)

    objetivos = ObjetivosDeAprendizagem.objects.all()

    if request.method == "POST":

        if "curso" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)

        curso = request.POST["curso"]
        grupo = "grupo" in request.POST and request.POST["grupo"]=="true"
        individuais = "individuais" in request.POST and request.POST["individuais"]=="true"

        so_finais = "so_finais" in request.POST and request.POST["so_finais"]=="true"

        if so_finais:
            # Somenete avaliações finais do Capstone
            # tipos = [2, 12, 22, 52, 54]
            exames = Exame.objects.filter(titulo="Banca Final") |\
                        Exame.objects.filter(titulo="Relatório Final de Grupo") |\
                        Exame.objects.filter(titulo="Relatório Final Individual") |\
                        Exame.objects.filter(titulo="Avaliação Final Individual") |\
                        Exame.objects.filter(titulo="Avaliação Final de Grupo")
            avaliacoes_sep = Avaliacao2.objects.filter(exame__in=exames)
        else:
            avaliacoes_sep = Avaliacao2.objects.all()

        if curso == 'T':

            # Avaliações Individuais
            if (individuais):
                avaliacoes_ind = avaliacoes_sep.filter(alocacao__isnull=False)
            else:
                avaliacoes_ind = avaliacoes_sep.none()

            # Avaliações Grupais
            if grupo:
                avaliacoes_grupo = avaliacoes_sep.filter(alocacao__isnull=True, projeto__isnull=False)
            else:
                avaliacoes_grupo = avaliacoes_sep.none()

            avaliacoes = avaliacoes_ind | avaliacoes_grupo

        else:

            # Avaliações Individuais
            if (individuais):
                avaliacoes_ind = avaliacoes_sep.filter(alocacao__aluno__curso2__sigla_curta=curso)
            else:
                avaliacoes_ind = avaliacoes_sep.none()

            # Avaliações Grupais
            if grupo:
                # identificando projetos com estudantes do curso (pelo menos um)
                projetos_selecionados = []
                projetos = Projeto.objects.all()
                for projeto in projetos:
                    alocacoes = Alocacao.objects.filter(projeto=projeto)
                    for alocacao in alocacoes:
                        if alocacao.aluno.curso2.sigla_curta == curso:
                            projetos_selecionados.append(projeto)
                            break
                        
                avaliacoes_grupo = Avaliacao2.objects.filter(alocacao__isnull=True, projeto__in=projetos_selecionados)

            else:
                avaliacoes_grupo = Avaliacao2.objects.none()

            avaliacoes = avaliacoes_ind | avaliacoes_grupo

        low = []
        mid = []
        high = []
        
        id_objetivo = request.POST["objetivo"]
        objetivo = ObjetivosDeAprendizagem.objects.get(id=id_objetivo)

        alocacoes = []

        for edicao in edicoes:
            periodo = edicao.split('.')
            semestre = avaliacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
            notas_lista = [x.nota for x in semestre if x.objetivo == objetivo and not x.na]
            notas = divide57(notas_lista)
            soma = sum(notas)
            if soma > 0:
                low.append(100*notas[0]/soma)
                mid.append(100*notas[1]/soma)
                high.append(100*notas[2]/soma)
            else:
                low.append(0)
                mid.append(0)
                high.append(0)

            alocacoes_tmp = Alocacao.objects.filter(projeto__ano=periodo[0],
                                                    projeto__semestre=periodo[1])

            if curso != 'T':
                alocacoes_tmp = alocacoes_tmp.filter(aluno__curso2__sigla_curta=curso)

            alocacoes.append(alocacoes_tmp.count())

        estudantes = zip(edicoes, alocacoes)

        context = {
            "low": low,
            "mid": mid,
            "high": high,
            "curso": curso,
            "ano": configuracao.ano,
            "semestre": configuracao.semestre,
            "edicoes": edicoes,
            "objetivo": objetivo,
            "objetivos": objetivos,
            "estudantes": estudantes,
            "lingua": configuracao.lingua,
        }

    else:

        context = {
            "titulo": {"pt": "Evolução por Objetivos de Aprendizado", "en": "Evolution by Learning Goals"},
            "edicoes": edicoes,
            "objetivos": objetivos,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, "projetos/evolucao_por_objetivo.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def prop_por_opcao(request):
    """Mostra graficos da proporção por opção alocada em projeto."""
    edicoes = list(get_edicoes(Projeto)[0])
    cores_opcoes = Estrutura.loads(nome="Cores Opcoes")

    estudantes = []    
    opcoes = []
    for edicao in edicoes:
        periodo = edicao.split('.')
        alocacoes = Alocacao.objects.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
        estudantes.append([edicao, alocacoes])

    for indice in range(1,7):
        if indice <= 5:
            opcoes.append({
                "indice": f"#{indice}",
                "qtds": [0] * len(edicoes),
                "cor": cores_opcoes[indice-1],
            })
        else:
            opcoes.append({
                "indice": f"#>={indice}",
                "qtds": [0] * len(edicoes),
                "cor": cores_opcoes[indice-1],
            })

    for edicao, alocacoes in estudantes:
        periodo = edicao.split('.')
        for alocacao in alocacoes:
            opcao = Opcao.objects.filter(proposta=alocacao.projeto.proposta, aluno=alocacao.aluno).last()
            if opcao:
                indice = opcao.prioridade
            else:
                continue  # Se não tiver opção, pula
            if indice <= 5:
                opcoes[indice-1]["qtds"][edicoes.index(edicao)] += 1
            else:
                opcoes[5]["qtds"][edicoes.index(edicao)] += 1

    for indice in range(len(edicoes)):
        total = sum(opcao["qtds"][indice] for opcao in opcoes)
        if total > 0:
            for opcao in opcoes:
                opcao["qtds"][indice] = 100 * opcao["qtds"][indice] / total
    
    context = {
        "titulo": {"pt": "Proporção por Opção Alocada em Projeto", "en": "Proportion by Option Allocated in Project"},
        "estudantes": estudantes,
        "opcoes": opcoes,
    }

    return render(request, "projetos/prop_por_opcao.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def correlacao_medias_cr(request):
    """Mostra graficos da correlação entre notas e o CR dos estudantes."""
    edicoes, _, semestre = get_edicoes(Avaliacao2)
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")

    if request.method == "POST":

        periodo = ["todo", "periodo"]
        alocacoes = None
        estudantes = {}

        if "edicao" in request.POST:

            curso = request.POST["curso"]

            if request.POST["edicao"] != "todas":
                periodo = request.POST["edicao"].split('.')
                alocacoes_tmp = Alocacao.objects.filter(projeto__ano=periodo[0],
                                                        projeto__semestre=periodo[1])

                if curso != 'T':
                    curso_sel = Curso.objects.get(sigla_curta=curso)
                    estudantes[curso_sel] = alocacoes_tmp.filter(aluno__curso2__sigla_curta=curso)
                else:
                    for curso_sel in Curso.objects.filter(curso_do_insper=True):
                        aloc = alocacoes_tmp.filter(aluno__curso2__sigla_curta=curso_sel.sigla_curta)
                        if aloc:
                            estudantes[curso_sel] = aloc

            else:
                alocacoes = {}
                for edicao in edicoes:
                    periodo = edicao.split('.')
                    semestre = Alocacao.objects.filter(projeto__ano=periodo[0],
                                                       projeto__semestre=periodo[1])
                    if curso == 'T':
                        alocacoes[periodo[0]+"_"+periodo[1]] = semestre
                    else:
                        semestre = semestre.filter(aluno__curso2__sigla_curta=curso)
                        alocacoes[periodo[0]+"_"+periodo[1]] = semestre
                periodo = ["todo", "periodo"]

        else:
            return HttpResponse("Algum erro não identificado.", status=401)


        context = {
            "alocacoes": alocacoes,
            "estudantes": estudantes,
            "periodo": periodo,
            "edicoes": edicoes,
            "curso": curso,
        }

    else:
        context = {
            "titulo": {"pt": "Correlação entre Médias e CR", "en": "Correlation between Grades and CR"},
            "edicoes": edicoes,
            "cursos": cursos_insper,
        }

    return render(request, "projetos/correlacao_medias_cr.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def editar_projeto(request, primarykey):
    """Editar Projeto."""

    if not request.user.eh_admin:  # Administrador
        return HttpResponse("Somente administradores podem editar projetos.", status=401)

    projeto = Projeto.objects.get(id=primarykey)

    if request.method == "POST":
        
        # Realoca orientador
        orientador_user_id = request.POST.get("orientador", None)
        if orientador_user_id:
            orientador = get_object_or_404(Professor, user_id=orientador_user_id)
            projeto.orientador = orientador
        else:
            projeto.orientador = None


        # Realoca coorientadores
        coorientadores_user_ids = []
        coorientadores = request.POST.getlist("SelCoorientador")
        for coorientador_user_id in coorientadores:
            if coorientador_user_id:
                coorientadores_user_ids.append(int(coorientador_user_id))
        # Apaga os coorientadores que não estão mais no projeto
        Coorientador.objects.filter(projeto=projeto).exclude(usuario__id__in=coorientadores_user_ids).delete()
        # Aloca os coorientadores que não estavam alocados
        for coorientador_user_id in coorientadores_user_ids:
            if not Coorientador.objects.filter(projeto=projeto, usuario__id=coorientador_user_id).exists():
                coorientador = get_object_or_404(PFEUser, id=coorientador_user_id)
                coorientacao = Coorientador(usuario=coorientador, projeto=projeto)
                coorientacao.save()


        # Realoca estudantes
        estudantes_user_ids = []
        estudantes = request.POST.getlist("SelEstudante")
        for estudante_user_id in estudantes:
            if estudante_user_id:
                estudantes_user_ids.append(int(estudante_user_id))
        # Apaga os estudantes que não estão mais no projeto
        Alocacao.objects.filter(projeto=projeto).exclude(aluno__user__id__in=estudantes_user_ids).delete()
        # Aloca os estudantes que não estavam alocados
        for estudante_user_id in estudantes_user_ids:
            if not Alocacao.objects.filter(projeto=projeto, aluno__user__id=estudante_user_id).exists():
                estudante = get_object_or_404(Aluno, user__id=estudante_user_id)
                alocacao = Alocacao(aluno=estudante, projeto=projeto)
                alocacao.save()

        # Define projeto com time misto (estudantes de outras instituições)
        projeto.time_misto = "time_misto" in request.POST

        projeto.save()

        return redirect("projeto_infos", primarykey=primarykey)

    context = {
        "titulo": {"pt": "Editar Projeto", "en": "Edit Project"},
        "projeto": projeto,
        "usuarios_professores": PFEUser.objects.filter(tipo_de_usuario__in=[2, 4]),  # Professores e Administradores
        "usuarios_estudantes_alocados": PFEUser.objects.filter(aluno__alocacao__projeto=projeto).distinct(),
        "estudantes": PFEUser.objects.filter(tipo_de_usuario=1),
        "coorientadores": Coorientador.objects.filter(projeto=projeto),
        "usuarios_coorientadores": PFEUser.objects.filter(coorientador__projeto=projeto).distinct(),
    }
    return render(request, "projetos/editar_projeto.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def nomes(request):
    """Acerta maiúsculas de nomes."""

    message = "Os seguintes nomes foram alterados:<br><br>"
    for usuario in PFEUser.objects.all():

        first_name = cap_name(usuario.first_name)
        last_name = cap_name(usuario.last_name)

        if (first_name != usuario.first_name) or (last_name != usuario.last_name):

            message += "&bull; " + usuario.first_name + " " + usuario.last_name
            message += "   \t &nbsp; >>>> &nbsp; \t   "
            message += first_name + " " + last_name + "<br>"

            usuario.first_name = first_name
            usuario.last_name = last_name

            usuario.save()

    message += "<br>&nbsp;&nbsp;<a href='" + request.build_absolute_uri("/administracao") + "'>voltar</a><br>"

    return HttpResponse(message)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def acompanhamento_view(request):
    """Cria um anotação para uma organização parceira."""
    if request.method == "POST" and "texto" in request.POST:
        acompanhamento = Acompanhamento()

        try:
            parceiro_id = int(request.POST["parceiro"])
            parceiro = get_object_or_404(Parceiro, id=parceiro_id)
        except ValueError:
            return HttpResponse("Erro: Parceiro não foi informado corretamente.", status=401)
        
        acompanhamento.autor = parceiro.user
        acompanhamento.texto = request.POST["texto"]

        if "data_hora" in request.POST:
            try:
                acompanhamento.data = dateutil.parser\
                    .parse(request.POST["data_hora"])
            except (ValueError, OverflowError):
                acompanhamento.data = datetime.datetime.now()

        acompanhamento.save()

        data = {
            "data": acompanhamento.data.strftime("%Y.%m.%d"),
            "autor": str(acompanhamento.autor.get_full_name()),
            "autor_id": acompanhamento.autor.parceiro.id,
            "org": str(parceiro.organizacao),
            "org_id": parceiro.organizacao.id,
            "atualizado": True,
        }

        return JsonResponse(data)

    context = {
        "parceiros": Parceiro.objects.all(),
        "data_hora": datetime.datetime.now(),
        "url": request.get_full_path(),
    }

    return render(request, "projetos/acompanhamento_view.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def reenvia_avisos(request):
    """Reenvia avisos do dia."""
    usuario_sem_acesso(request, (4,)) # Soh Adm
    avisos_do_dia()
    eventos_do_dia()
    return redirect("avisos_listar")


@login_required
def upload_estudantes_projeto(request, projeto_id):

    if request.method == "POST":
        projeto = get_object_or_404(Projeto, id=projeto_id)
        projeto.titulo_final = request.POST.get("titulo_final", None)
        projeto.resumo = request.POST.get("resumo", None)
        projeto.abstract = request.POST.get("abstract", None)
        projeto.palavras_chave = request.POST.get("palavras_chave", None)

        projeto.atualizacao_estudantes = datetime.datetime.now()

        projeto.save()

    if request.user.eh_estud:
        return redirect("/projetos/meuprojeto")
    return redirect("/projetos/projeto_infos/"+str(projeto_id))


def grupos_formados(request):
    """Mostra os grupos formados (brincadeira)."""
    return render(request, "projetos/grupos_formados.html", context={})
