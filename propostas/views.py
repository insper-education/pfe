#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

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
from projetos.models import Evento, get_upload_path
from projetos.support import simple_upload

from operacional.models import Curso

from administracao.support import get_limite_propostas, get_data_planejada


from .support import retorna_ternario, ordena_propostas_novo, ordena_propostas
from .support import envia_proposta, preenche_proposta


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_propostas(request):
    """Mostra página principal de Propostas."""
    return render(request, 'propostas/index_propostas.html')


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mapeamento_estudantes_propostas(request):
    """Faz o mapeamento entre estudantes e propostas do próximo semestre."""
    configuracao = get_object_or_404(Configuracao)

    ano = configuracao.ano
    semestre = configuracao.semestre
    edicoes, ano, semestre = get_edicoes(Proposta)

    if request.is_ajax():
        if 'edicao' in request.POST:
            ano, semestre = request.POST['edicao'].split('.')
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        lista_propostas = list(zip(*ordena_propostas(False, ano, semestre)))
        if lista_propostas:
            propostas = lista_propostas[0]
        else:
            propostas = []

        alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
            filter(anoPFE=ano).\
            filter(semestrePFE=semestre).\
            filter(trancado=False).\
            order_by(Lower("user__first_name"), Lower("user__last_name"))

        opcoes = []
        for aluno in alunos:
            opcoes_aluno = []
            alocacaos = Alocacao.objects.filter(aluno=aluno)
            for proposta in propostas:
                opcao = Opcao.objects.filter(aluno=aluno, proposta=proposta).last()
                if opcao:
                    opcoes_aluno.append(opcao)
                else:
                    try:
                        proj = Projeto.objects.get(proposta=proposta,
                                                   ano=ano,
                                                   semestre=semestre)
                        if alocacaos.filter(projeto=proj):
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

        # checa para empresas repetidas, para colocar um número para cada uma
        repetidas = {}
        for proposta in propostas:
            if proposta.organizacao:
                if proposta.organizacao.sigla in repetidas:
                    repetidas[proposta.organizacao.sigla] += 1
                else:
                    repetidas[proposta.organizacao.sigla] = 0
            else:
                if proposta.nome_organizacao in repetidas:
                    repetidas[proposta.nome_organizacao] += 1
                else:
                    repetidas[proposta.nome_organizacao] = 0
        repetidas_limpa = {}
        for repetida in repetidas:
            if repetidas[repetida] != 0:  # tira zerados
                repetidas_limpa[repetida] = repetidas[repetida]
        proposta_indice = {}
        for proposta in reversed(propostas):
            if proposta.organizacao:
                if proposta.organizacao.sigla in repetidas_limpa:
                    proposta_indice[proposta.id] = \
                        repetidas_limpa[proposta.organizacao.sigla] + 1
                    repetidas_limpa[proposta.organizacao.sigla] -= 1
            else:
                if proposta.nome_organizacao in repetidas_limpa:
                    proposta_indice[proposta.id] = \
                        repetidas_limpa[proposta.nome_organizacao] + 1
                    repetidas_limpa[proposta.nome_organizacao] -= 1

        estudantes = zip(alunos, opcoes)
        context = {
            'estudantes': estudantes,
            'propostas': propostas,
            'configuracao': configuracao,
            'ano': ano,
            'semestre': semestre,
            'loop_anos': range(2018, configuracao.ano+1),
            'proposta_indice': proposta_indice,
            'edicoes': edicoes,
        }

    else:

        informacoes = [
            ("#MapeamentoTable tr > *:nth-child(2)", "Curso"),
            ("#MapeamentoTable tr > *:nth-child(3)", "CR", False),
        ]

        context = {
            "edicoes": edicoes,
            "informacoes": informacoes,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request,
                  'propostas/mapeamento_estudante_projeto.html',
                  context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def procura_propostas(request):
    """Exibe um histograma com a procura das propostas pelos estudantes."""
    configuracao = get_object_or_404(Configuracao)
    curso = "T"  # por padrão todos os cursos
    ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)

    if request.is_ajax():

        if 'anosemestre' in request.POST:

            if request.POST['anosemestre'] == 'todas':
                ano = 0
            else:
                anosemestre = request.POST['anosemestre'].split(".")
                ano = int(anosemestre[0])
                semestre = int(anosemestre[1])

            if 'curso' in request.POST:
                curso = request.POST['curso']

        else:
            return HttpResponse("Erro não identificado (POST incompleto)",
                                status=401)

    mylist = ordena_propostas_novo(True,
                                   ano=ano,
                                   semestre=semestre,
                                   curso=curso)

    propostas = []
    prioridades = [[], [], [], [], []]
    estudantes = [[], [], [], [], []]

    if len(mylist) > 0:
        unzipped_object = zip(*mylist)

        propostas,\
            prioridades[0], prioridades[1], prioridades[2],\
            prioridades[3], prioridades[4],\
            estudantes[0], estudantes[1], estudantes[2],\
            estudantes[3], estudantes[4]\
            = list(unzipped_object)

    # Para procurar as áreas mais procuradas nos projetos
    opcoes = Opcao.objects.filter(aluno__user__tipo_de_usuario=1,
                                  aluno__trancado=False)

    if ano > 0:  # Ou seja não são todos os anos e semestres
        opcoes = opcoes.filter(aluno__anoPFE=ano, aluno__semestrePFE=semestre)
        opcoes = opcoes.filter(proposta__ano=ano, proposta__semestre=semestre)

    opcoes = opcoes.filter(prioridade=1)

    # Caso não se deseje todos os cursos, se filtra qual se deseja
    if curso != "T":
        opcoes = opcoes.filter(aluno__curso2__sigla_curta=curso)

    areaspfe = {}
    areas = Area.objects.filter(ativa=True)
    for area in areas:
        count = 0
        for opcao in opcoes:
            if AreaDeInteresse.objects.filter(proposta=opcao.proposta,
                                              area=area):
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
    aplicando_multidisciplinar = 0
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
    for opcao in opcoes:
        p = opcao.proposta.get_nativamente()
        if isinstance(p, Curso):
            aplicando_opcoes[p] += 1
        else:                
            aplicando_multidisciplinar += 1

    edicoes, _, _ = get_edicoes(Proposta)

    context = {
        "tamanho": tamanho,
        "propostas": propostas,
        "prioridades": prioridades,
        "estudantes": estudantes,
        "ano": ano,
        "semestre": semestre,
        "areaspfe": areaspfe,
        "opcoes": opcoes,
        "edicoes": edicoes,
        "cursos": cursos,
        "disponivel_propostas": disponivel_propostas,
        "disponivel_multidisciplinar": disponivel_multidisciplinar,
        "aplicando_opcoes": aplicando_opcoes,
        "aplicando_multidisciplinar": aplicando_multidisciplinar,
    }

    return render(request, 'propostas/procura_propostas.html', context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def propostas_apresentadas(request):
    """Lista todas as propostas de projetos."""
    configuracao = get_object_or_404(Configuracao)

    ano = configuracao.ano
    semestre = configuracao.semestre
    edicoes = []

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            if edicao == 'todas':
                propostas_filtradas = Proposta.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                propostas_filtradas = Proposta.objects\
                    .filter(ano=ano,
                            semestre=semestre)

            propostas_filtradas = propostas_filtradas.order_by("ano",
                                                               "semestre",
                                                               "organizacao",
                                                               "titulo", )

            cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")

            vagas, ternario_aprovados = retorna_ternario(propostas_filtradas.filter(disponivel=True), cursos)
            _, ternario_pendentes = retorna_ternario(propostas_filtradas.filter(disponivel=False), cursos)

            dic_organizacoes = {}
            for proposta in propostas_filtradas:
                if proposta.organizacao and\
                  proposta.organizacao not in dic_organizacoes:
                    dic_organizacoes[proposta.organizacao] = 0
            num_organizacoes = len(dic_organizacoes)

            # Contando propostas disponíveis e escolhas
            disponivel_propostas = {}
            for curso in cursos:
                disponivel_propostas[curso] = [0, 0]
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
        
            context = {
                'propostas': propostas_filtradas,
                'num_organizacoes': num_organizacoes,
                'ternario_aprovados': ternario_aprovados,
                'ternario_pendentes': ternario_pendentes,
                'configuracao': configuracao,
                "edicao": edicao,
                "cursos": cursos,
                "disponivel_propostas": disponivel_propostas,
                "disponivel_multidisciplinar": disponivel_multidisciplinar,
                "vagas": vagas,
                "limite_propostas": get_limite_propostas(configuracao),
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Proposta)
        context = {
            "edicoes": edicoes,
        }

    return render(request, 'propostas/propostas_apresentadas.html', context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def proposta_completa(request, primarykey):
    """Mostra uma proposta por completo."""
    proposta = get_object_or_404(Proposta, pk=primarykey)

    if request.is_ajax():

        # Troca Conformidade de Proposta
        for dict in request.POST:
            if dict[0:5]=="dict[":
                tmp = False
                if request.POST[dict] == "true":
                    tmp = True
                setattr(proposta, dict[5:-1], tmp)

        # Define autorizador
        if 'autorizador' in request.POST:
            try:
                if request.POST['autorizador'] == "0":
                    proposta.autorizado = None
                else:
                    proposta.autorizado = PFEUser.objects\
                        .get(pk=int(request.POST['autorizador']))
                proposta.disponivel = request.POST['disponibilizar'] == 'sim'
                proposta.save()
            except PFEUser.DoesNotExist:
                return HttpResponse("Autorizador não encontrado.", status=401)
        else:
            return HttpResponse("Autorizador não encontrado.", status=401)

        data = {
            'atualizado': True,
        }
        return JsonResponse(data)

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

    context = {
        "configuracao": configuracao,
        "proposta": proposta,
        "opcoes": opcoes,
        "MEDIA_URL": settings.MEDIA_URL,
        "projetos": projetos,
        "comite": membros_comite,
        "estudantes": estudantes,
        "sem_opcao": sem_opcao,
        'areast': areas,
        "procura": procura,
        "cursos": Curso.objects.all().order_by("id"),
        "liberacao_visualizacao": liberacao_visualizacao,
    }
    return render(request, 'propostas/proposta_completa.html', context=context)


@login_required
def proposta_detalhes(request, primarykey):
    """Exibe proposta de projeto com seus detalhes para estudante aplicar."""
    proposta = get_object_or_404(Proposta, pk=primarykey)
    
    if request.user.tipo_de_usuario == 1:  # (1, 'aluno')
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

    context = {
        "proposta": proposta,
        "MEDIA_URL": settings.MEDIA_URL,
        "procura": procura,
        "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),

    }
    return render(request, 'propostas/proposta_detalhes.html', context=context)


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
    liberadas_propostas = configuracao.liberadas_propostas

    configuracao = get_object_or_404(Configuracao)
    ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)

    vencida = proposta.ano != ano or proposta.semestre != semestre

    if request.method == 'POST':
        if (not liberadas_propostas) or (user.tipo_de_usuario == 4):
            if request.POST.get("new"):
                proposta = preenche_proposta(request, None)
            else:
                preenche_proposta(request, proposta)

            if "arquivo" in request.FILES:
                arquivo = simple_upload(request.FILES['arquivo'],
                                        path=get_upload_path(proposta, ""))
                proposta.anexo = arquivo[len(settings.MEDIA_URL):]
                proposta.save()

            enviar = "mensagem" in request.POST  # Por e-mail se enviar
            mensagem = envia_proposta(proposta, enviar)
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
            return render(request, 'generic.html', context=context)

        return HttpResponse("Propostas não liberadas para edição.", status=401)

    areas = Area.objects.filter(ativa=True)

    interesses = proposta.get_interesses()

    context = {
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
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, 'organizacoes/proposta_submissao.html', context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def proposta_remover(request, slug):
    """Remove Proposta do Sistema por slug."""
    if request.user.tipo_de_usuario != 4:  # admin
        return HttpResponse("Sem privilégios de Administrador.", status=401)

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
    """Definir datas do PFE."""
    configuracao = get_object_or_404(Configuracao)

    #if request.method == "POST":
    if request.is_ajax():
        if request.user.tipo_de_usuario != 4:  # Administrador
            return HttpResponse("Somenter coordenadores podem alterar valores de publicação de propostas.", status=401)
        if "liberadas_propostas" and "min_props" in request.POST:
            data = {"atualizado": True,}
            try:
                configuracao.liberadas_propostas = request.POST["liberadas_propostas"] == "true"
                data["liberadas_propostas"] = configuracao.liberadas_propostas
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
        "configuracao": configuracao,
        "limite_propostas": get_limite_propostas(configuracao),
        "data_planejada": get_data_planejada(configuracao),
    }

    return render(request, "propostas/publicar_propostas.html", context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def validate_alunos(request):
    """Ajax para validar vaga de estudantes em propostas."""
    proposta_id = int(request.GET.get('proposta', None))
    vaga = request.GET.get('vaga', "  ")
    checked = request.GET.get('checked', None) == "true"

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
        return HttpResponseNotFound('<h1>Proposta não encontrada!</h1>')

    return JsonResponse({'atualizado': True,})

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
        'disciplinas': Disciplina.objects.all().order_by("nome"),
        'proposta': proposta,
    }

    return render(request,
                  'propostas/disciplina_view.html',
                  context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def remover_disciplina(request):
    """Remove Disciplina Recomendada."""
    if request.is_ajax() and 'disciplina_id' in request.POST and 'proposta_id' in request.POST:

        try:
            proposta_id = int(request.POST['proposta_id'])
            disciplina_id = int(request.POST['disciplina_id'])
        except:
            return HttpResponse("Erro ao recuperar proposta e disciplinas.", status=401)

        instances = Recomendada.objects.filter(proposta__id=proposta_id, disciplina__id=disciplina_id)
        for instance in instances:
            instance.delete()

        return JsonResponse({"atualizado": True},)

    return HttpResponseNotFound('Requisição errada')


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def projeto_criar(request, proposta_id):
    """Criar projeto de proposta."""
    proposta = get_object_or_404(Proposta, id=proposta_id)

    projeto = Projeto.create(proposta)
    projeto.titulo = proposta.titulo
    projeto.descricao = proposta.descricao
    projeto.organizacao = proposta.organizacao
    projeto.ano = proposta.ano
    projeto.semestre = proposta.semestre
    projeto.save()

    return redirect('projeto_completo', primarykey=projeto.id)
