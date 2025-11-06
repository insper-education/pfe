#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import logging

from collections import Counter

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import timezone

from ratelimit.decorators import ratelimit

from .models import PerguntasRespostas

from .support import ordena_propostas_novo, ordena_propostas
from .support import envia_proposta, preenche_proposta, preenche_proposta_pdf
from .support import contem_caracteres_invalidos

from administracao.models import Estrutura
from administracao.support import get_limite_propostas, get_data_planejada, propostas_liberadas, usuario_sem_acesso
from administracao.support import limpa_texto

from operacional.models import Curso

from organizacoes.support import get_form_fields

from projetos.models import Proposta, Projeto, Organizacao, Disciplina
from projetos.models import Configuracao, Area, Recomendada
from projetos.models import Evento
from projetos.messages import email
from projetos.support import get_upload_path, simple_upload
from projetos.support2 import get_nativamente

from users.models import Opcao, Aluno, Alocacao, PFEUser
from users.models import Contato, Parceiro
from users.support import get_edicoes, adianta_semestre


# Get an instance of a logger
logger = logging.getLogger("django")

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_propostas(request):
    """Mostra página principal de Propostas."""
    context = {"titulo": {"pt": "Propostas de Projetos", "en": "Project Proposals"},}
    if "/propostas/propostas" in request.path:
        return render(request, "propostas/propostas.html", context=context)
    else:
        return render(request, "propostas/index_propostas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mapeamento_estudantes_propostas(request):
    """Faz o mapeamento entre estudantes e propostas do próximo semestre."""

    if request.is_ajax():
        if "edicao" in request.POST:
            ano, semestre = request.POST["edicao"].split('.')
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        propostas = ordena_propostas(False, ano, semestre)

        alunos = Aluno.objects.filter(ano=ano, semestre=semestre, trancado=False).\
            order_by(Lower("user__first_name"), Lower("user__last_name"))
        projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

        opcoes = []
        aloc_proj = []
        for aluno in alunos:
            opcoes_aluno = []
            opcoes_estudante = Opcao.objects.filter(aluno=aluno, proposta__in=propostas)
            alocacoes_estudante = Alocacao.objects.filter(aluno=aluno, projeto__in=projetos)
            aloc_proj.append(alocacoes_estudante.last().projeto.proposta if alocacoes_estudante else None)
            alocacoes_projetos = {a.projeto for a in alocacoes_estudante}
            for proposta in propostas:
                opcao = next((o for o in opcoes_estudante if o.proposta == proposta), None)
                if opcao:
                    opcoes_aluno.append(opcao)
                else:
                    try:
                        proj = next((p for p in projetos if p.proposta == proposta), None)
                        if proj and proj in alocacoes_projetos:
                            # Cria uma opção temporaria
                            opc = Opcao()
                            opc.prioridade = 0
                            opc.proposta = proposta
                            opc.aluno = aluno
                            opcoes_aluno.append(opc)
                        else:
                            opcoes_aluno.append(None)
                    except Projeto.DoesNotExist:
                        opcoes_aluno.append(None)

            opcoes.append(opcoes_aluno)

        # Checa para empresas repetidas, para colocar um número para cada uma
        counter = Counter(proposta.organizacao.sigla if proposta.organizacao else proposta.nome_organizacao for proposta in propostas)

        # Remove as Organizações que aparecem só uma vez
        repetidas_limpa = {org: count for org, count in counter.items() if count > 1}

        proposta_indice = {}
        for proposta in reversed(propostas):
            org_name = proposta.organizacao.sigla if proposta.organizacao else proposta.nome_organizacao
            if org_name in repetidas_limpa:
                proposta_indice[proposta.id] = repetidas_limpa[org_name]
                repetidas_limpa[org_name] -= 1

        estudantes = zip(alunos, opcoes, aloc_proj)
        context = {
            "qtd_estudantes": len(alunos),
            "estudantes": estudantes,
            "propostas": propostas,
            "proposta_indice": proposta_indice,
            "cursos": Curso.objects.filter(curso_do_insper=True),
        }

    else:

        informacoes = [
            ("#MapeamentoTable tr > *:nth-child(2)", "Curso", "Program"),
            ("#MapeamentoTable tr > *:nth-child(3)", "CR", "GPA", False),
        ]

        context = {
            "titulo": {"pt": "Mapeamento de Propostas por Estudantes", "en": "Mapping of Proposals by Students"},
            "edicoes": get_edicoes(Proposta)[0],
            "informacoes": informacoes,
        }

    return render(request, "propostas/mapeamento_estudante_projeto.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def procura_propostas(request):
    """Exibe um histograma com a procura das propostas pelos estudantes."""
    
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    
    if request.is_ajax():

        configuracao = get_object_or_404(Configuracao)
        ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)
        curso = "T"  # por padrão todos os cursos

        if "edicao" in request.POST and "curso" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                ano = 0
            else:
                ano, semestre = map(int, edicao.split('.'))
            if "curso" in request.POST:
                curso = request.POST["curso"]
        else:
            return HttpResponse("Erro não identificado (POST incompleto)", status=401)

        NIVEIS_OPCOES = 5
        propostas_ordenadas = ordena_propostas_novo(True, ano=ano, semestre=semestre, curso=curso)

        propostas = [item[0] for item in propostas_ordenadas]
        prioridades = [[item[i+1] for item in propostas_ordenadas] for i in range(NIVEIS_OPCOES)]
        estudantes = [[item[i+NIVEIS_OPCOES+1] for item in propostas_ordenadas] for i in range(NIVEIS_OPCOES)]

        # Para procurar as áreas mais procuradas nos projetos
        opcoes = Opcao.objects.filter(aluno__trancado=False, prioridade=1)

        if ano > 0:  # Ou seja não são todos os anos e semestres
            opcoes = opcoes.filter(aluno__ano=ano, aluno__semestre=semestre,
                                proposta__ano=ano, proposta__semestre=semestre)

        # Caso não se deseje todos os cursos, se filtra qual se deseja
        if curso != "T":
            opcoes = opcoes.filter(aluno__curso2__sigla_curta=curso)
        
        # Filtra para opções com estudantes de um curso específico
        if curso != "TE":
            if curso != 'T':
                opcoes = opcoes.filter(aluno__curso2__sigla_curta=curso)
            else:
                opcoes = opcoes.filter(aluno__curso2__in=cursos_insper)

        areas = Area.objects.filter(ativa=True)
        areas = areas.annotate(
            count=Count("areadeinteresse", filter=Q(areadeinteresse__proposta__in=opcoes.values("proposta")))
        )
        areaspfe = {area.titulo: (area.count, area.descricao) for area in areas}

        # conta de maluco para fazer diagrama ficar correto
        tamanho = len(propostas)
        if tamanho <= 4:
            tamanho *= 9
        else:
            tamanho *= 5

        # Contando propostas disponíveis e escolhas
        cursos = Curso.objects.all().order_by("id")
        disponivel_propostas = {}
        aplicando_opcoes = {}
        for curso in cursos:
            disponivel_propostas[curso] = [0, 0]
            aplicando_opcoes[curso] = 0
                
        disponivel_multidisciplinar = [0, 0]
        for proposta in propostas:
            p = get_nativamente(proposta)
            if isinstance(p, Curso):
                if proposta.disponivel:
                    disponivel_propostas[p][0] += 1
                disponivel_propostas[p][1] += 1
            else:
                if proposta.disponivel:
                    disponivel_multidisciplinar[0] += 1
                disponivel_multidisciplinar[1] += 1

        aplicando_multidisciplinar = 0
        for opcao in opcoes:
            p = get_nativamente(opcao.proposta)
            if isinstance(p, Curso):
                aplicando_opcoes[p] += 1
            else:                
                aplicando_multidisciplinar += 1

        cores_propostas = ["#00FA00", "#D2E61E", "#D2BE23", "#B4B478", "#B4C8A0", "#8B4513"]
        escolhas = []
        for i in range(5):
            escolhas.append({
                "prioridades": prioridades[i],
                "estudantes": estudantes[i],
                "cor": cores_propostas[i],
            })

        qtd_estudantes = Aluno.objects.filter(ano=ano, semestre=semestre, trancado=False, curso2__in=cursos_insper).count()
        qtd_estudantes_opc = len(opcoes.values("aluno").distinct())

        qtd_estudantes_curso = {}
        for curso in cursos_insper:
            qtd_estudantes_curso[curso] = {}
            qtd_estudantes_curso[curso]["qtd"] = Aluno.objects.filter(ano=ano, semestre=semestre, trancado=False, curso2=curso).count()
            qtd_estudantes_curso[curso]["opc"] = len(opcoes.filter(aluno__curso2=curso).values("aluno").distinct())

        context = {
            "tamanho": tamanho,
            "propostas": propostas,
            "escolhas": escolhas,
            "estudantes": estudantes,
            "areaspfe": areaspfe,
            "disponivel_propostas": disponivel_propostas,
            "disponivel_multidisciplinar": disponivel_multidisciplinar,
            "aplicando_opcoes": aplicando_opcoes,
            "aplicando_multidisciplinar": aplicando_multidisciplinar,
            "qtd_estudantes": qtd_estudantes,
            "qtd_estudantes_opc": qtd_estudantes_opc,
            "qtd_estudantes_curso": qtd_estudantes_curso,
        }

    else:
        
        cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

        context = {
            "titulo": {"pt": "Procura pelas Propostas de Projetos", "en": "Demand for Project Proposals"},
            "edicoes": get_edicoes(Proposta)[0],
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "propostas/procura_propostas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def propostas_apresentadas(request):
    """Lista todas as propostas de projetos."""
    configuracao = get_object_or_404(Configuracao)
    
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                ano, semestre = None, None
                propostas_filtradas = Proposta.objects.all().order_by("ano", "semestre", "organizacao", "titulo")
            else:
                ano, semestre = edicao.split('.')
                propostas_filtradas = Proposta.objects.filter(ano=ano, semestre=semestre).order_by("organizacao", "titulo")

            unique_organizacoes = set()
            for proposta in propostas_filtradas:
                if proposta.organizacao:
                    unique_organizacoes.add(proposta.organizacao)
            num_organizacoes = len(unique_organizacoes)

            # Contando propostas disponíveis e escolhas
            disponivel_propostas = {}
            vagas = {}
            total_vagas = {"count": 0, "count_disp": 0, "prop": 0, "prop_disp": 0, "neces": 0}

            cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")
            alunos = Aluno.objects.all()

            for curso in cursos:
                if ano and semestre:
                    estudantes = alunos.filter(curso2=curso, ano=ano, semestre=semestre, trancado=False).count()
                else:
                    estudantes = alunos.filter(curso2=curso, trancado=False).count()
                disponivel_propostas[curso] = [0, 0]
                vagas[curso] = {"count": 0, "count_disp": 0, "prop": 0, "prop_disp": 0, "neces": estudantes}
                total_vagas["neces"] += estudantes

            disponivel_multidisciplinar = [0, 0]

            nativamente = []
            for proposta in propostas_filtradas:
                p = get_nativamente(proposta)
                nativamente.append(p)
                if isinstance(p, Curso):
                    if proposta.disponivel:
                        disponivel_propostas[p][0] += 1
                    disponivel_propostas[p][1] += 1
                else:
                    if proposta.disponivel:
                        disponivel_multidisciplinar[0] += 1
                    disponivel_multidisciplinar[1] += 1

                for curso in cursos:
                    count = 0
                    count_disp = 0
                    prop = 0
                    prop_disp = 0
                    for i in range(1, 5):
                        perfil = getattr(proposta, f"perfil{i}").all()
                        count_tot_perfil = perfil.count()
                        if curso in perfil: 
                            count += 1
                            prop += 1 / count_tot_perfil
                            if proposta.disponivel:
                                count_disp += 1
                                prop_disp += 1 / count_tot_perfil

                    vagas[curso]["count"] += count
                    vagas[curso]["count_disp"] += count_disp
                    vagas[curso]["prop"] += prop
                    vagas[curso]["prop_disp"] += prop_disp

                    total_vagas["prop"] += prop
                    total_vagas["prop_disp"] += prop_disp
                
                total_propostas = propostas_filtradas.count()

            cabecalhos = [
                {"pt": "Analisada", "en": "Analyzed", "font": "12px", "tooltip": "Algum professor do comitê analisou que a proposta seja publicada para os estudantes"},
                {"pt": "Disponível", "en": "Available", "font": "12px", "tooltip": "Proposta ficará disponível para estudantes na fase onde eles deverão selecionar interesse"},
                {"pt": "Fechada", "en": "Confirmed", "font": "12px", "tooltip": "Foi formado um grupo de estudantes para essa proposta de projeto"},
                {"pt": "Proposta", "en": "Proposal"},
                {"pt": "Período", "en": "Semester", "esconder": True},
                {"pt": "Organização", "en": "Organization"},
                {"pt": "Tipo", "en": "Type", "font-size": "12px"},
                {"pt": "Estudante1", "en": "Student1", "font": "12px", "classes": "estudante-icon"},
                {"pt": "Estudante2", "en": "Student2", "font": "12px", "classes": "estudante-icon"},
                {"pt": "Estudante3", "en": "Student3", "font": "12px", "classes": "estudante-icon"},
                {"pt": "Estudante4", "en": "Student4", "font": "12px", "classes": "estudante-icon"},
                {"pt": "Disciplinas Recomendadas", "en": "Recommended Courses", "font": "12px"},
            ]

            context = {
                "prop_nativ": zip(propostas_filtradas, nativamente),
                "num_organizacoes": num_organizacoes,
                "edicao": edicao,
                "cursos": cursos,
                "disponivel_propostas": disponivel_propostas,
                "disponivel_multidisciplinar": disponivel_multidisciplinar,
                "vagas": vagas,
                "total_vagas": total_vagas,
                "limite_propostas": get_limite_propostas(configuracao),
                "liberadas_propostas": propostas_liberadas(configuracao),
                "cabecalhos": cabecalhos,
                "total_propostas": total_propostas,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:
        context = {
            "titulo": {"pt": "Propostas de Projetos Apresentadas", "en": "Proposed Projects"},
            "edicoes": get_edicoes(Proposta)[0],
            }

    return render(request, "propostas/propostas_apresentadas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def propostas_lista(request):
    """Lista todas as propostas de projetos."""

    if request.is_ajax():

        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)

        edicao = request.POST["edicao"]
        if edicao == "todas":
            propostas = Proposta.objects.all()
        else:
            ano, semestre = request.POST["edicao"].split('.')
            propostas = Proposta.objects.filter(ano=ano, semestre=semestre)

        cabecalhos = [{"pt": "Título da Proposta", "en": "Proposal Title"},
                    {"pt": "Período", "en": "Period", "esconder": True},
                    {"pt": "Organização", "en": "Organization"},
                    {"pt": "Tipo", "en": "Type"},]
        
        context = {
            "propostas": propostas,
            "edicao": edicao,
            "cabecalhos": cabecalhos,
        }
            
    else:
        context = {
            "titulo": {"pt": "Lista de Propostas", "en": "Proposals List"},
            "edicoes": get_edicoes(Proposta)[0],
            }

    return render(request, "propostas/propostas_lista.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def ajax_proposta(request, primarykey=None):
    """Atualiza uma proposta."""

    if primarykey is None:
        return HttpResponse("Erro não identificado.", status=401)
    
    if request.is_ajax():

        proposta = get_object_or_404(Proposta, pk=primarykey)

        # Troca Conformidade de Proposta
        for dict in request.POST:
            if dict[0:5]=="dict[":
                tmp = False
                if request.POST[dict] == "true":
                    tmp = True
                setattr(proposta, dict[5:-1], tmp)

        # Define analisador
        if "autorizador" in request.POST:
            try:
                if request.POST["autorizador"] == "0":
                    proposta.autorizado = None
                else:
                    proposta.autorizado = PFEUser.objects\
                        .get(pk=request.POST["autorizador"])
            except PFEUser.DoesNotExist:
                return HttpResponse("Analisador não encontrado.", status=401)
        
        # Disponibiliza proposta
        if "disponibilizar" in request.POST:
            proposta.disponivel = request.POST["disponibilizar"] == "sim"

        # Anotações internas
        if "anotacoes" in request.POST:
            proposta.anotacoes = request.POST["anotacoes"]

        proposta.save()
        data = {"atualizado": True,}
        return JsonResponse(data)

    return HttpResponse("Erro não identificado.", status=401)


@login_required
@transaction.atomic
def ajax_proposta_pergunta(request, primarykey=None):
    """Atualiza perguntas sobre uma proposta."""

    if primarykey is None:
        return HttpResponse("Erro não identificado.", status=401)
    
    if request.is_ajax():

        proposta = get_object_or_404(Proposta, pk=primarykey)
        
        # Define analisador
        if "pergunta" in request.POST:
            pergunta_resposta = PerguntasRespostas(
                proposta=proposta,
                pergunta=request.POST["pergunta"],
                quem_perguntou=request.user,
            )
            pergunta_resposta.save()

        
            # Enviando e-mail com mensagem para usuários.
            mensagem = f"O estudante: <b>{request.user.get_full_name()}</b>, fez uma pergunta sobre a proposta: <b>{proposta.titulo}</b>."
            mensagem += f"\n\n<br><br>Pergunta: <i>{pergunta_resposta.pergunta}</i>"
            mensagem += f"\n\n<br><br>Link para a proposta: {request.scheme}://{request.get_host()}/propostas/proposta_completa/{proposta.id}"
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
    
    return HttpResponse("Erro não identificado.", status=401)


@login_required
@transaction.atomic
def ajax_proposta_resposta(request, primarykey=None):
    """Atualiza perguntas sobre uma proposta."""

    if primarykey is None:
        return HttpResponse("Erro não identificado.", status=401)
    
    if request.is_ajax():

        proposta = get_object_or_404(Proposta, pk=primarykey)
        
        # Define analisador
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
                str(configuracao.coordenacao.user.email)
                ]

            email(subject, recipient_list, mensagem)
            return JsonResponse({"atualizado": True,})
    
    return HttpResponse("Erro não identificado.", status=401)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def proposta_completa(request, primarykey):
    """Mostra uma proposta por completo."""
    proposta = get_object_or_404(Proposta, pk=primarykey)
    configuracao = get_object_or_404(Configuracao)

    projetos = Projeto.objects.filter(proposta=proposta)

    estudantes = []
    sem_opcao = []
    for projeto in projetos:
        alocacoes = Alocacao.objects.filter(projeto=projeto).select_related("aluno")
        for alocacao in alocacoes:
            if Opcao.objects.filter(proposta=proposta, aluno=alocacao.aluno).exists():
                estudantes.append(alocacao.aluno)
            else:
                sem_opcao.append(alocacao.aluno)

    opcoes = Opcao.objects.filter(proposta=proposta)

    prioridades = 5
    procura = {str(prioridade+1): opcoes.filter(prioridade=prioridade+1).count() for prioridade in range(prioridades)}

    context = {
        "titulo": {"pt": "Proposta de Projeto", "en": "Project Proposal"},
        "configuracao": configuracao,
        "proposta": proposta,
        "opcoes": opcoes,
        "projetos": projetos,
        "comite": PFEUser.objects.filter(membro_comite=True),
        "estudantes": estudantes,
        "sem_opcao": sem_opcao,
        "areas_de_interesse_possiveis": Area.objects.filter(ativa=True),
        "procura": procura,
        "cursos": Curso.objects.all().order_by("id"),
        "liberacao_visualizacao": Evento.objects.filter(tipo_evento__sigla="APDE").last(),
        "conformidades": proposta.CONFORMIDADES,
        "cores_opcoes": Estrutura.loads(nome="Cores Opcoes"),
    }
    return render(request, "propostas/proposta_completa.html", context=context)


@login_required
def proposta_detalhes(request, primarykey):
    """Exibe proposta de projeto com seus detalhes para estudante aplicar."""
    proposta = get_object_or_404(Proposta, pk=primarykey)
    
    if request.user.eh_estud:  # estudante
        if not (request.user.aluno.ano == proposta.ano and
                request.user.aluno.semestre == proposta.semestre):
            return HttpResponse("Usuário não tem permissão de acesso.",
                                status=401)
        if not proposta.disponivel:
            return HttpResponse("Usuário não tem permissão de acesso.",
                                status=401)

    if request.user.eh_parc:  # parceiro
        return HttpResponse("Usuário não tem permissão de acesso.", status=401)

    opcoes = Opcao.objects.filter(proposta=proposta)

    prioridades = 5
    procura = {
            str(prioridade): 
                opcoes.filter(prioridade=prioridade).count() for prioridade in range(1, prioridades+1)
          }

    context = {
        "titulo": {"pt": "Detalhes da Proposta", "en": "Proposal Details"},
        "proposta": proposta,
        "procura": procura,
        "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        "cores_opcoes": Estrutura.loads(nome="Cores Opcoes"),
    }
    return render(request, "propostas/proposta_detalhes.html", context=context)


@ratelimit(key="ip", rate="5/m", block=False)
def proposta_editar(request, slug=None):
    """Formulário de Submissão de Proposta de Projetos."""
    if getattr(request, 'limited', False):
        mensagem_erro = {
            "pt": "Você enviou propostas demais em pouco tempo. Por favor, aguarde um instante antes de tentar novamente.",
            "en": "You have submitted too many proposals in a short period. Please wait a moment before trying again.",
        }
        context = {"voltar": True, "mensagem_erro": mensagem_erro}
        return render(request, "generic_ml.html", context=context, status=429)  # 429 Too Many Requests


    configuracao = get_object_or_404(Configuracao)
    ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)

    organizacao = None

    if request.user and request.user.is_authenticated:

        if request.user.eh_estud:  # estudante
            mensagem_erro = {
                "pt": "Você não está cadastrado como parceiro!",
                "en": "You are not registered as a partner!",
            }
            context = {
                "area_principal": True,
                "mensagem_erro": mensagem_erro,
            }
            return render(request, "generic_ml.html", context=context)

        if request.user.eh_parc:  # parceiro
            parceiro = get_object_or_404(Parceiro, pk=request.user.parceiro.pk)
            organizacao = parceiro.organizacao

    if slug:
        proposta = get_object_or_404(Proposta, slug=slug)
        vencida = proposta.ano != ano or proposta.semestre != semestre
    else:
        proposta = None
        vencida = False
    
    liberadas_propostas = propostas_liberadas(configuracao)

    if request.method == "POST":

        if (not liberadas_propostas) or (request.user.is_authenticated and request.user.eh_admin):
            
            if "new" in request.POST:
                titulo = request.POST.get("titulo_prop", "").strip()

                if contem_caracteres_invalidos(titulo):
                    mensagem_erro = {
                        "pt": "O título contém caracteres inválidos. Por favor, remova-os e tente novamente.",
                        "en": "The title contains invalid characters. Please remove them and try again.",
                    }
                    context = {"voltar": True, "mensagem_erro": mensagem_erro}
                    return render(request, "generic_ml.html", context=context)

                if titulo and Proposta.objects.filter(titulo=titulo, ano=ano, semestre=semestre).exists():
                    mensagem_erro = {
                        "pt": "Uma proposta com este título já existe para o próximo semestre e aparentemente está sendo duplicada.<br> Caso considere que isso não deveria acontecer, por favor contactar: <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>.<br> A proposta não foi salva.",
                        "en": "A proposal with this title already exists for the next semester and appears to be duplicated.<br> If you believe this should not happen, please contact: <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>.<br> The proposal has not been saved.",
                    }
  
                    context = {
                        "voltar": True,
                        "mensagem_erro": mensagem_erro,
                    }
                    return render(request, "generic_ml.html", context=context)

                if proposta:  # Nova proposta baseada na antiga
                    organizacao = proposta.organizacao
                    colaboracao = proposta.colaboracao
                    anexo = proposta.anexo
                    proposta = preenche_proposta(request, None)
                    proposta.organizacao = organizacao
                    proposta.colaboracao = colaboracao
                    proposta.anexo = anexo
                    proposta.save()
                else:
                    proposta = preenche_proposta(request, None)
                resposta = {"pt": "Submissão de proposta de projeto realizada com sucesso.<br>",
                            "en": "Project proposal submission completed successfully.<br>"}
            elif "update" in request.POST:
                preenche_proposta(request, proposta)
                resposta = {"pt": "Atualização de proposta de projeto realizada com sucesso.<br>",
                            "en": "Project proposal update completed successfully.<br>"}
            elif "remover" in request.POST:
                proposta.delete()
                context = {
                    "voltar": True,
                    "mensagem": {"pt": "Proposta removida!", "en": "Proposal removed!"},
                }
                return render(request, "generic_ml.html", context=context)
            else:
                return HttpResponse("Erro não identificado.", status=401)

            if "arquivo" in request.FILES:
                try:
                    arquivo = simple_upload(request.FILES["arquivo"],
                                            path=get_upload_path(proposta, ""))
                    proposta.anexo = arquivo[len(settings.MEDIA_URL):]
                    proposta.save()
                except Exception as e:
                    logger.error(f"Erro ao fazer upload do arquivo: {e}")
                    mensagem_erro = {
                        "pt": f"Erro no upload do arquivo: {e}",
                        "en": f"Error uploading file: {e}",
                    }
                    context = {
                        "voltar": True,
                        "mensagem_erro": mensagem_erro,
                    }
                    return render(request, "generic_ml.html", context=context)

            # Só faz essa parte se usuário logado e professor ou administrador:
            if request.user.is_authenticated and request.user.eh_prof_a:
                proposta.internacional = True if request.POST.get("internacional", None) else False
                proposta.intercambio = True if request.POST.get("intercambio", None) else False
                proposta.empreendendo = True if request.POST.get("empreendendo", None) else False
                colaboracao_id = request.POST.get("colaboracao", None)
                if colaboracao_id:
                    proposta.colaboracao = Organizacao.objects.filter(pk=colaboracao_id).last()
                else:
                    proposta.colaboracao = None
                proposta.save()

            enviar = "mensagem" in request.POST  # Por e-mail se enviar
            mensagem = envia_proposta(proposta, request, enviar)

            if enviar:
                resposta["pt"] += "Você deve receber um e-mail de confirmação nos próximos instantes.<br>"
                resposta["en"] += "You should receive a confirmation email in the next few moments.<br>"
            resposta["pt"] += "<br><hr>" + mensagem  # Precisa acertar isso
            resposta["en"] += "<br><hr>" + mensagem  # Precisa acertar isso

            context = {
                "voltar": True,
                "mensagem": resposta,
                "ver_proposta": proposta,
            }
            return render(request, "generic_ml.html", context=context)

        else:
            return HttpResponse("Propostas não estão liberadas para submissão/edição.", status=401)

    organizacao_str = request.GET.get("organizacao", None)
    if organizacao_str:
        try:
            organizacao = Organizacao.objects.get(id=organizacao_str)
        except (ValueError, Organizacao.DoesNotExist):
            return HttpResponseNotFound("<h1>Organização não encontrado!</h1>")

    if proposta:
        interesses = proposta.get_interesses()
    else:
        interesses = [
            ["aprimorar", Proposta.TIPO_INTERESSE[0], False],
            ["realizar", Proposta.TIPO_INTERESSE[1], False],
            ["iniciar", Proposta.TIPO_INTERESSE[2], False],
            ["identificar", Proposta.TIPO_INTERESSE[3], False],
            ["mentorar", Proposta.TIPO_INTERESSE[4], False],
        ]

    ano_semestre = f"{ano}.{semestre}"

    obs = {
           "pt": """
                Observação: Ao submeter o projeto, é fundamental deixar claro que o objetivo do Capstone é 
                proporcionar aos estudantes um contato próximo com os responsáveis das organizações parceiras 
                para o desenvolvimento de uma solução tecnológica. Em geral, os estudantes se comunicam 
                semanalmente com a instituição para compreender melhor o desafio, apresentar os resultados 
                obtidos até o momento, planejar as próximas etapas em conjunto e tratar de outros aspectos 
                que podem variar conforme o projeto.
                Além disso, deve-se esclarecer que, embora não haja um custo direto para as organizações 
                parceiras, será necessário que pelo menos um profissional dedique algumas horas semanais 
                para acompanhar os estudantes. Caso a proposta envolva custos, como servidores ou materiais, 
                o Insper pode não ter condições de arcar com essas despesas, cabendo à empresa assumi-las. 
                Os estudantes, no entanto, terão acesso aos laboratórios do Insper para o desenvolvimento 
                do projeto, mediante agendamento.
           """,
           "en": """
                Note: When submitting the project, it is essential to clarify that the goal of the Capstone 
                is to provide students with close contact with the representatives of partner institutions 
                for the development of a technological solution. In general, students communicate with the 
                institution on a weekly basis to better understand the challenge, present the results obtained 
                so far, plan the next steps together, and address other aspects that may vary depending on 
                the project.
                Additionally, it should be made clear that although there is no direct cost for partner 
                institutions, at least one professional will need to dedicate a few hours per week to support 
                the students. If the proposal involves costs such as servers or materials, Insper may not be 
                able to cover these expenses, and it will be up to the company to assume them. However, 
                students will have access to Insper's laboratories for project development, subject to scheduling.
           """
    }

    tipo_pt = "Edição" if proposta else "Submissão"
    tipo_en = "Edit" if proposta else "Submission"

    context = {
        "titulo": {"pt": tipo_pt + " de Proposta de Projeto (Capstone " + ano_semestre + ")", "en": "Project Proposal " + tipo_en + " (Capstone " + ano_semestre + ")" },
        "liberadas_propostas": liberadas_propostas,
        "organizacao": organizacao,
        "proposta": proposta,
        "Proposta": Proposta,
        "Contato": Contato,
        "obs": obs,
        "areas_de_interesse_possiveis": Area.objects.filter(ativa=True),
        "edicao": True if proposta else False,
        "interesses": interesses,
        "configuracao": configuracao,
        "vencida": vencida,
        "organizacoes": Organizacao.objects.all(),
    }
    return render(request, "organizacoes/proposta_submissao.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def proposta_remover(request, slug):
    """Remove Proposta do Sistema por slug."""
    usuario_sem_acesso(request, (4,)) # Soh Adm

    proposta = get_object_or_404(Proposta, slug=slug)
    proposta.delete()

    context = {
        "voltar": True,
        "mensagem": {"pt": "Proposta removida!", "en": "Proposal removed!"},
    }
    return render(request, "generic_ml.html", context=context)



@ratelimit(key="ip", rate="5/m", block=False)
def carrega_proposta(request):
    """Página para carregar Proposta de Projetos em PDF."""

    if getattr(request, 'limited', False):
        mensagem_erro = {
            "pt": "Você enviou propostas demais em pouco tempo. Por favor, aguarde um instante antes de tentar novamente.",
            "en": "You have submitted too many proposals in a short period. Please wait a moment before trying again.",
        }
        context = {"voltar": True, "mensagem_erro": mensagem_erro}
        return render(request, "generic_ml.html", context=context, status=429)  # 429 Too Many Requests

    configuracao = get_object_or_404(Configuracao)
    ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)

    if request.user and request.user.is_authenticated:

        if request.user.eh_estud:  # estudantes
            mensagem_erro = {
                "pt": "Você não está cadastrado como parceiro!",
                "en": "You are not registered as a partner!",
            }
            context = {
                "area_principal": True,
                "mensagem_erro": mensagem_erro,
            }
            return render(request, "generic_ml.html", context=context)

    if request.method == "POST":

        resposta = {"pt": "", "en": ""}

        if "arquivo" in request.FILES:
            try:
                arquivo = simple_upload(request.FILES["arquivo"],
                                        path=get_upload_path(None, ""),
                                        valida="pdf")
            except Exception as e:
                logger.error(f"Erro ao fazer upload do arquivo de proposta: {e}")
                mensagem_erro = {
                    "pt": f"Erro ao processar o arquivo: {e}",
                    "en": f"Error processing file: {e}",
                }
                context = {
                    "voltar": True,
                    "mensagem_erro": mensagem_erro,
                }
                return render(request, "generic_ml.html", context=context)

            if arquivo is None:
                return HttpResponse("Arquivo não reconhecido.", status=401)
            
            try:
                fields = get_form_fields(arquivo[1:])
            except Exception as e:
                return HttpResponse("Erro ao processar o arquivo: " + str(e), status=401)
            
            if fields is None:
                mensagem_erro = {
                    "pt": "ERRO: Arquivo formulário não reconhecido",
                    "en": "ERROR: File form not recognized",
                }
                context = {
                    "voltar": True,
                    "mensagem_erro": mensagem_erro,
                }
                return render(request, "generic_ml.html", context=context)

            fields["nome"] = limpa_texto(request.POST.get("nome", "").strip())
            fields["email"] = limpa_texto(request.POST.get("email", "").strip())

            proposta, erros = preenche_proposta_pdf(fields, None)

            if erros:
                resposta["pt"] += "ERROS:<br><b style='color:red;font-size:40px'>" + erros + "<br><br></b>"
                resposta["en"] += "ERRORS:<br><b style='color:red;font-size:40px'>" + erros + "<br><br></b>"
                mensagem = "Proposta de projeto não foi submetida."
            else:
                enviar = "mensagem" in request.POST  # Por e-mail se enviar
                mensagem = envia_proposta(proposta, request, enviar)
                
                resposta["pt"] += "Submissão de proposta de projeto realizada com sucesso.<br>"
                resposta["en"] += "Project proposal submission completed successfully.<br>"

                if enviar:
                    resposta["pt"] += "Você deve receber um e-mail de confirmação nos próximos instantes.<br><br>"
                    resposta["en"] += "You should receive a confirmation email in the next few moments.<br><br>"

        else:
            mensagem = "Arquivo não identificado"

        resposta["pt"] += "<br><hr>" + mensagem
        resposta["en"] += "<br><hr>" + mensagem

        context = {
            "voltar": True,
            "mensagem_l": resposta,
        }
        return render(request, "generic_ml.html", context=context)

    ano_semestre = f"{ano}.{semestre}"
    
    context = {
        "titulo": {"pt": "Carrega Proposta de Projeto em PDF (Capstone " + ano_semestre + ")", 
                   "en": "Upload Project Proposal in PDF (Capstone " + ano_semestre + ")" },
    }
    return render(request, "organizacoes/carrega_proposta.html", context)

@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def publicar_propostas(request):
    """Definir datas de publicação de propostas."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if not request.user.eh_admin:  # Administrador
            return HttpResponse("Somente coordenadores podem alterar valores de publicação de propostas.", status=401)
        if "min_props" in request.POST:
            data = {"atualizado": True,}
            try:
                data["liberadas_propostas"] = propostas_liberadas(configuracao)
                if int(request.POST["min_props"]) != configuracao.min_props:
                    configuracao.min_props = int(request.POST["min_props"])
                    data["min_props"] = configuracao.min_props
                configuracao.save()
            except (ValueError, OverflowError, MultiValueDictKeyError):
                return HttpResponse("Algum erro não identificado.", status=401)
             
            return JsonResponse(data)
        
        else:
            return HttpResponse("Algum erro ao passar parâmetros.", status=401)
    
    context = {
        "titulo": {"pt": "Publicação das Propostas de Projetos", "en": "Publication of Project Proposals"},
        "liberadas_propostas": propostas_liberadas(configuracao),
        "min_props": configuracao.min_props,
        "limite_propostas": get_limite_propostas(configuracao),
        "data_planejada": get_data_planejada(configuracao),
    }

    return render(request, "propostas/publicar_propostas.html", context)


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
    """Cria um anotação para uma organização parceira."""
    proposta = get_object_or_404(Proposta, id=proposta_id)

    if request.is_ajax() and "organizacao_id" in request.POST:

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
    """Adicionar Disciplina Recomendada."""
    proposta = get_object_or_404(Proposta, id=proposta_id)
    if request.is_ajax() and "disciplina_id" in request.POST:

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
    """Remove Disciplina Recomendada."""
    if request.is_ajax() and "disciplina_id" in request.POST and "proposta_id" in request.POST:

        try:
            proposta_id = int(request.POST["proposta_id"])
            disciplina_id = int(request.POST["disciplina_id"])
        except:
            return HttpResponse("Erro ao recuperar proposta e disciplinas.", status=401)

        instances = Recomendada.objects.filter(proposta__id=proposta_id, disciplina__id=disciplina_id)
        for instance in instances:
            instance.delete()

        return JsonResponse({"atualizado": True},)

    return HttpResponseNotFound("Requisição errada")


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def projeto_criar(request, proposta_id):
    """Criar projeto de proposta."""
    proposta = get_object_or_404(Proposta, id=proposta_id)

    projeto = Projeto.objects.create(
        proposta=proposta,
        ano=proposta.ano,
        semestre=proposta.semestre
    )

    return redirect("projeto_infos", primarykey=projeto.id)
