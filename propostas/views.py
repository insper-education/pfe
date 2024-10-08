#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

from collections import Counter

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError

from users.support import get_edicoes, adianta_semestre
from users.models import Opcao, Aluno, Alocacao, PFEUser
from users.models import Professor, Parceiro, Administrador

from projetos.models import Proposta, Projeto, Organizacao, Disciplina, Conexao
from projetos.models import Configuracao, Area, AreaDeInteresse, Recomendada
from projetos.models import Evento
from projetos.support import get_upload_path, simple_upload

from operacional.models import Curso

from administracao.support import get_limite_propostas, get_data_planejada, propostas_liberadas, usuario_sem_acesso

from .support import retorna_ternario, ordena_propostas_novo, ordena_propostas
from .support import envia_proposta, preenche_proposta


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_propostas(request):
    """Mostra página principal de Propostas."""
    context = {"titulo": "Propostas de Projetos",}
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

        lista_propostas = list(zip(*ordena_propostas(False, ano, semestre)))
        propostas = lista_propostas[0] if lista_propostas else []

        alunos = Aluno.objects.filter(anoPFE=ano, semestrePFE=semestre, trancado=False).\
            order_by(Lower("user__first_name"), Lower("user__last_name"))
        projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

        opcoes = []
        for aluno in alunos:
            opcoes_aluno = []
            opcoes_estudante = Opcao.objects.filter(aluno=aluno, proposta__in=propostas)
            alocacoes = Alocacao.objects.filter(aluno=aluno, projeto__in=projetos)
            alocacoes_projetos = {a.projeto for a in alocacoes}
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
                proposta_indice[proposta.id] = repetidas_limpa[org_name] + 1
                repetidas_limpa[org_name] -= 1

        estudantes = zip(alunos, opcoes)
        context = {
            "estudantes": estudantes,
            "propostas": propostas,
            "proposta_indice": proposta_indice,
            "cursos": Curso.objects.filter(curso_do_insper=True),
        }

    else:

        informacoes = [
            ("#MapeamentoTable tr > *:nth-child(2)", "Curso"),
            ("#MapeamentoTable tr > *:nth-child(3)", "CR", False),
        ]

        context = {
            "titulo": "Mapeamento de Propostas por Estudantes",
            "edicoes": get_edicoes(Proposta)[0],
            "informacoes": informacoes,
        }

    return render(request, "propostas/mapeamento_estudante_projeto.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def procura_propostas(request):
    """Exibe um histograma com a procura das propostas pelos estudantes."""
    configuracao = get_object_or_404(Configuracao)
    curso = "T"  # por padrão todos os cursos
    ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.is_ajax():

        if "anosemestre" in request.POST:
            edicao = request.POST["anosemestre"]
            if edicao == "todas":
                ano = 0
            else:
                ano, semestre = map(int, edicao.split('.'))
            if "curso" in request.POST:
                curso = request.POST["curso"]
        else:
            return HttpResponse("Erro não identificado (POST incompleto)", status=401)

    NIVEIS_OPCOES = 5
    mylist = ordena_propostas_novo(True, ano=ano, semestre=semestre, curso=curso)
    propostas = []
    prioridades = [[] for _ in range(NIVEIS_OPCOES)]
    estudantes = [[] for _ in range(NIVEIS_OPCOES)]
    if mylist:
        propostas = [item[0] for item in mylist]
        for i in range(NIVEIS_OPCOES):
            prioridades[i] = [item[i+1] for item in mylist]
            estudantes[i] = [item[i+NIVEIS_OPCOES+1] for item in mylist]

    # Para procurar as áreas mais procuradas nos projetos
    opcoes = Opcao.objects.filter(aluno__user__tipo_de_usuario=1,
                                  aluno__trancado=False,
                                  prioridade=1)

    if ano > 0:  # Ou seja não são todos os anos e semestres
        opcoes = opcoes.filter(aluno__anoPFE=ano, aluno__semestrePFE=semestre,
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
    areaspfe = {}
    for area in areas:
        count = 0
        for opcao in opcoes:
            if AreaDeInteresse.objects.filter(proposta=opcao.proposta, area=area):
                count += 1
        areaspfe[area.titulo] = (count, area.descricao)

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
        p = proposta.get_nativamente()
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
        p = opcao.proposta.get_nativamente()
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

    context = {
        "titulo": "Procura pelas Propostas de Projetos",
        "tamanho": tamanho,
        "propostas": propostas,
        "escolhas": escolhas,
        "estudantes": estudantes,
        "areaspfe": areaspfe,
        "edicoes": get_edicoes(Proposta)[0],
        "cursos": cursos_insper,
        "cursos_externos": cursos_externos,
        "disponivel_propostas": disponivel_propostas,
        "disponivel_multidisciplinar": disponivel_multidisciplinar,
        "aplicando_opcoes": aplicando_opcoes,
        "aplicando_multidisciplinar": aplicando_multidisciplinar,
    }

    return render(request, "propostas/procura_propostas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def propostas_apresentadas(request):
    """Lista todas as propostas de projetos."""
    configuracao = get_object_or_404(Configuracao)
    edicoes = []

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                ano = None
                semestre = None
                propostas_filtradas = Proposta.objects.all().order_by("ano", "semestre", "organizacao", "titulo")
            else:
                ano, semestre = edicao.split('.')
                propostas_filtradas = Proposta.objects.filter(ano=ano, semestre=semestre).order_by("organizacao", "titulo")

            cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")

            dic_organizacoes = {}
            for proposta in propostas_filtradas:
                if proposta.organizacao and proposta.organizacao not in dic_organizacoes:
                    dic_organizacoes[proposta.organizacao] = 0
            num_organizacoes = len(dic_organizacoes)

            # Contando propostas disponíveis e escolhas
            disponivel_propostas = {}
            vagas = {}
            count = {}  # temporaria
            count_disp = {}  # temporaria
            prop = {}  # temporaria proporcional
            prop_disp = {}  # temporaria proporcional
            total_vagas = [0, 0, 0, 0, 0]
            for curso in cursos:
                if ano and semestre:
                    estudantes = Aluno.objects.filter(curso2=curso, anoPFE=ano, semestrePFE=semestre).count()
                else:
                    estudantes = Aluno.objects.filter(curso2=curso).count()
                disponivel_propostas[curso] = [0, 0]
                vagas[curso] = [0, 0, 0, 0, estudantes]
                total_vagas[4] += estudantes
            disponivel_multidisciplinar = [0, 0]
            for proposta in propostas_filtradas:
                p = proposta.get_nativamente()
                if isinstance(p, Curso):
                    if proposta.disponivel:
                        disponivel_propostas[p][0] += 1
                    disponivel_propostas[p][1] += 1
                else:
                    if proposta.disponivel:
                        disponivel_multidisciplinar[0] += 1
                    disponivel_multidisciplinar[1] += 1
                for curso in cursos:
                    count[curso] = 0
                    count_disp[curso] = 0
                    prop[curso] = 0
                    prop_disp[curso] = 0
                    for i in range(1,5):
                        perfil = getattr(proposta, "perfil"+str(i)).all()
                        if curso in perfil: 
                            count[curso] += 1
                            prop[curso] += 1/perfil.count()
                            if proposta.disponivel:
                                count_disp[curso] += 1
                                prop_disp[curso] += 1/perfil.count()
                    vagas[curso][0] += count[curso]
                    vagas[curso][1] += count_disp[curso]
                    vagas[curso][2] += prop[curso]
                    vagas[curso][3] += prop_disp[curso]
                    total_vagas[0] += count[curso]
                    total_vagas[1] += count_disp[curso]
                    total_vagas[2] += prop[curso]
                    total_vagas[3] += prop_disp[curso]
        
            context = {
                "propostas": propostas_filtradas,
                "num_organizacoes": num_organizacoes,
                "edicao": edicao,
                "cursos": cursos,
                "disponivel_propostas": disponivel_propostas,
                "disponivel_multidisciplinar": disponivel_multidisciplinar,
                "vagas": vagas,
                "total_vagas": total_vagas,
                "limite_propostas": get_limite_propostas(configuracao),
                "liberadas_propostas": propostas_liberadas(configuracao),
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Proposta)
        context = {
            "titulo": "Propostas de Projetos Apresentadas",
            "edicoes": edicoes,
            }

    return render(request, "propostas/propostas_apresentadas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def propostas_lista(request):
    """Lista todas as propostas de projetos."""

    if request.is_ajax():
        edicoes = []
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                propostas = Proposta.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                propostas = Proposta.objects\
                    .filter(ano=ano, semestre=semestre)

            propostas = propostas.order_by("ano", "semestre", "organizacao", "titulo")

            cabecalhos = [{"pt": "Título da Proposta", "en": "Proposal Title"},
                                {"pt": "Período", "en": "Period"},
                                {"pt": "Organização", "en": "Organization"},
                                {"pt": "Tipo", "en": "Type"},
                    ]
            context = {
                "propostas": propostas,
                "edicao": edicao,
                "cabecalhos": cabecalhos,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Proposta)
        context = {
            "titulo": {"pt": "Lista de Propostas", "en": "Proposals List"},
            "edicoes": edicoes,
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
                        .get(pk=int(request.POST["autorizador"]))
            except PFEUser.DoesNotExist:
                return HttpResponse("Analisador não encontrado.", status=401)
        
        # Disponibiliza proposta
        if "disponibilizar" in request.POST:
            proposta.disponivel = request.POST["disponibilizar"] == "sim"

        proposta.save()
        data = {"atualizado": True,}
        return JsonResponse(data)

    return HttpResponse("Erro não identificado.", status=401)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def proposta_completa(request, primarykey):
    """Mostra uma proposta por completo."""
    proposta = get_object_or_404(Proposta, pk=primarykey)
    configuracao = get_object_or_404(Configuracao)

    membros_comite = PFEUser.objects.filter(membro_comite=True)
    projetos = Projeto.objects.filter(proposta=proposta)

    estudantes = []
    sem_opcao = []
    for projeto in projetos:
        alocacoes = Alocacao.objects.filter(projeto=projeto)
        for alocacao in alocacoes:
            if Opcao.objects.filter(proposta=proposta, aluno=alocacao.aluno):
                estudantes.append(alocacao.aluno)
            else:
                sem_opcao.append(alocacao.aluno)

    opcoes = Opcao.objects.filter(proposta=proposta)

    procura = {}
    procura["1"] = opcoes.filter(prioridade=1).count()
    procura["2"] = opcoes.filter(prioridade=2).count()
    procura["3"] = opcoes.filter(prioridade=3).count()
    procura["4"] = opcoes.filter(prioridade=4).count()
    procura["5"] = opcoes.filter(prioridade=5).count()

    areas = Area.objects.filter(ativa=True)

    liberacao_visualizacao = Evento.objects.filter(tipo_de_evento=113).last()

    titulo = "Proposta " + str(proposta.ano) + '.' + str(proposta.semestre)
    if proposta.organizacao:
        titulo += " [" + proposta.organizacao.sigla + "] "
    titulo += proposta.titulo
    
    context = {
        "titulo": titulo,
        "configuracao": configuracao,
        "proposta": proposta,
        "opcoes": opcoes,
        "projetos": projetos,
        "comite": membros_comite,
        "estudantes": estudantes,
        "sem_opcao": sem_opcao,
        "areast": areas,
        "procura": procura,
        "cursos": Curso.objects.all().order_by("id"),
        "liberacao_visualizacao": liberacao_visualizacao,
    }
    return render(request, "propostas/proposta_completa.html", context=context)


@login_required
def proposta_detalhes(request, primarykey):
    """Exibe proposta de projeto com seus detalhes para estudante aplicar."""
    proposta = get_object_or_404(Proposta, pk=primarykey)
    
    if request.user.tipo_de_usuario == 1:  # (1, "estudante")
        if not (request.user.aluno.anoPFE == proposta.ano and
                request.user.aluno.semestrePFE == proposta.semestre):
            return HttpResponse("Usuário não tem permissão de acesso.",
                                status=401)
        if not proposta.disponivel:
            return HttpResponse("Usuário não tem permissão de acesso.",
                                status=401)

    if request.user.tipo_de_usuario == 3:  # (3, 'parceiro')
        return HttpResponse("Usuário não tem permissão de acesso.", status=401)

    opcoes = Opcao.objects.filter(proposta=proposta)

    procura = {}
    procura["1"] = opcoes.filter(prioridade=1).count()
    procura["2"] = opcoes.filter(prioridade=2).count()
    procura["3"] = opcoes.filter(prioridade=3).count()
    procura["4"] = opcoes.filter(prioridade=4).count()
    procura["5"] = opcoes.filter(prioridade=5).count()

    titulo = "Proposta " + str(proposta.ano) + '.' + str(proposta.semestre)
    if proposta.organizacao:
        titulo += " [" + proposta.organizacao.sigla + "] "
    titulo += proposta.titulo

    context = {
        "titulo": titulo,
        "proposta": proposta,
        "procura": procura,
        "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),

    }
    return render(request, "propostas/proposta_detalhes.html", context=context)


# @login_required
def proposta_editar(request, slug):
    """Formulário de Edição de Propostas de Projeto por slug."""
    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        user = None

    parceiro = None
    professor = None
    administrador = None

    if user:
        if user.tipo_de_usuario == 1:  # alunos
            mensagem = "Você não está cadastrado como parceiro!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        if user.tipo_de_usuario == 3:  # parceiro
            parceiro = get_object_or_404(Parceiro, pk=request.user.parceiro.pk)
        elif user.tipo_de_usuario == 2:  # professor
            professor = get_object_or_404(Professor, pk=request.user.professor.pk)
        elif user.tipo_de_usuario == 4:  # admin
            administrador = get_object_or_404(Administrador, pk=request.user.administrador.pk)

    proposta = get_object_or_404(Proposta, slug=slug)

    configuracao = get_object_or_404(Configuracao)
    liberadas_propostas = propostas_liberadas(configuracao)
    ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)

    vencida = proposta.ano != ano or proposta.semestre != semestre

    if request.method == "POST":
        if (not liberadas_propostas) or (user.tipo_de_usuario == 4):
            enviar = "mensagem" in request.POST  # Verifica check para enviar e-mail
            if request.POST.get("new"):
                 
                titulo = request.POST.get("titulo_prop", "").strip()
                if titulo and Proposta.objects.filter(titulo=titulo, ano=ano, semestre=semestre).exists():
                    context = {
                        "voltar": True,
                        "mensagem": "Uma proposta com este título já existe para o próximo semestre e aparentemente está sendo duplicada.<br> Caso considere que isso não deveria acontecer, por favor contactar: <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>.<br> A proposta não foi salva.",
                    }
                    return render(request, "generic.html", context=context)

                if proposta:
                    organizacao = proposta.organizacao
                    colaboracao = proposta.colaboracao
                    anexo = proposta.anexo
                    proposta = preenche_proposta(request, None)
                    proposta.organizacao = organizacao
                    proposta.colaboracao = colaboracao
                    proposta.anexo = anexo
                else:
                    proposta = preenche_proposta(request, None)
            elif request.POST.get("update"):
                preenche_proposta(request, proposta)
            elif request.POST.get("remover"):
                proposta.delete()
                context = {
                    "voltar": True,
                    "mensagem": "Proposta removida!",
                }
                return render(request, "generic.html", context=context)
            else:
                return HttpResponse("Erro não identificado.", status=401)

            if "arquivo" in request.FILES:
                arquivo = simple_upload(request.FILES["arquivo"],
                                        path=get_upload_path(proposta, ""))
                proposta.anexo = arquivo[len(settings.MEDIA_URL):]
                proposta.save()

            if request.user.is_authenticated:
                if request.user.tipo_de_usuario == 2 or request.user.tipo_de_usuario == 4:
                    proposta.internacional = True if request.POST.get("internacional", None) else False
                    proposta.intercambio = True if request.POST.get("intercambio", None) else False
                    proposta.empreendendo = True if request.POST.get("empreendendo", None) else False
                    colaboracao_id = request.POST.get("colaboracao", None)
                    if colaboracao_id:
                        proposta.colaboracao = Organizacao.objects.filter(pk=colaboracao_id).last()
            
            # Salva a proposta no Banco de Dados
            proposta.save()

            mensagem = envia_proposta(proposta, request, enviar)
            resposta = "Submissão de proposta de projeto "
            resposta += "atualizada com sucesso.<br>"

            if enviar:
                resposta += "Você deve receber um e-mail de confirmação "
                resposta += "nos próximos instantes.<br>"

            resposta += "<br><hr>"
            resposta += mensagem

            context = {
                "voltar": True,
                "mensagem": resposta,
            }
            return render(request, "generic.html", context=context)

        return HttpResponse("Propostas não liberadas para edição.", status=401)

    areas = Area.objects.filter(ativa=True)

    interesses = proposta.get_interesses()

    context = {
        "titulo": "Edição de Proposta de Projeto",
        "liberadas_propostas": liberadas_propostas,
        "full_name": proposta.nome,
        "email": proposta.email,
        "parceiro": parceiro,
        "professor": professor,
        "administrador": administrador,
        "areast": areas,
        "proposta": proposta,
        "edicao": True,
        "interesses": interesses,
        "ano_semestre": str(proposta.ano)+"."+str(proposta.semestre),
        "vencida": vencida,
        "configuracao": configuracao,
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
        "mensagem": "Proposta removida!",
    }
    return render(request, "generic.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def publicar_propostas(request):
    """Definir datas de publicação de propostas."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if request.user.tipo_de_usuario != 4:  # Administrador
            return HttpResponse("Somente coordenadores podem alterar valores de publicação de propostas.", status=401)
        if "min_props" in request.POST:
            data = {"atualizado": True,}
            try:
                #configuracao.liberadas_propostas = request.POST["liberadas_propostas"] == "true"
                #data["liberadas_propostas"] = configuracao.liberadas_propostas
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
        "titulo": "Publicação das Propostas de Projetos",
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
    proposta_id = int(request.GET.get("proposta", None))
    vaga = request.GET.get("vaga", " - ").split('-')
    checked = request.GET.get("checked", None) == "true"

    try:
        proposta = Proposta.objects.select_for_update().get(id=proposta_id)

        curso_selecionado = Curso.objects.get(sigla_curta=vaga[0])
        if vaga[1] == '1':
            if checked:
                proposta.perfil1.add(curso_selecionado)
            else:
                proposta.perfil1.remove(curso_selecionado)
        elif vaga[1] == '2':
            if checked:
                proposta.perfil2.add(curso_selecionado)
            else:
                proposta.perfil2.remove(curso_selecionado)
        elif vaga[1] == '3':
            if checked:
                proposta.perfil3.add(curso_selecionado)
            else:
                proposta.perfil3.remove(curso_selecionado)
        elif vaga[1] == '4':
            if checked:
                proposta.perfil4.add(curso_selecionado)
            else:
                proposta.perfil4.remove(curso_selecionado)

        proposta.save()
    except Proposta.DoesNotExist:
        return HttpResponseNotFound("<h1>Proposta não encontrada!</h1>")

    return JsonResponse({"atualizado": True,})

@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def link_organizacao(request, proposta_id):
    """Cria um anotação para uma organização parceira."""
    proposta = get_object_or_404(Proposta, id=proposta_id)

    if request.is_ajax() and 'organizacao_id' in request.POST:

        organizacao_id = int(request.POST['organizacao_id'])
        organizacao = get_object_or_404(Organizacao, id=organizacao_id)

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
        "organizacoes": Organizacao.objects.all().order_by(Lower('sigla')),
        "proposta": proposta,
    }

    return render(request,
                  'propostas/organizacao_view.html',
                  context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def link_disciplina(request, proposta_id):
    """Adicionar Disciplina Recomendada."""
    proposta = get_object_or_404(Proposta, id=proposta_id)
    if request.is_ajax() and 'disciplina_id' in request.POST:

        disciplina_id = int(request.POST['disciplina_id'])
        disciplina = get_object_or_404(Disciplina, id=disciplina_id)

        ja_existe = Recomendada.objects.filter(proposta=proposta, disciplina=disciplina)

        if ja_existe:
            return HttpResponseNotFound('Já existe')

        recomendada = Recomendada.create()
        recomendada.proposta = proposta
        recomendada.disciplina = disciplina
        recomendada.save()

        data = {
            'disciplina': str(disciplina),
            'disciplina_id': disciplina.id,
            'proposta_id': proposta_id,
            'atualizado': True,
        }

        return JsonResponse(data)

    context = {
        "disciplinas": Disciplina.objects.all().order_by("nome"),
        "proposta": proposta,
    }

    return render(request, "propostas/disciplina_view.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def remover_disciplina(request):
    """Remove Disciplina Recomendada."""
    if request.is_ajax() and 'disciplina_id' in request.POST and 'proposta_id' in request.POST:

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

    projeto = Projeto.create(proposta)
    projeto.organizacao = proposta.organizacao
    projeto.ano = proposta.ano
    projeto.semestre = proposta.semestre
    projeto.save()

    return redirect("projeto_completo", primarykey=projeto.id)
