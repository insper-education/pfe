#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""


from django.conf import settings

from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required, permission_required

from django.http import HttpResponse, HttpResponseNotFound, JsonResponse

from django.db.models.functions import Lower

from users.support import get_edicoes, adianta_semestre

from users.models import Opcao, Aluno, Alocacao, PFEUser
from users.models import Professor, Parceiro, Administrador

from projetos.models import Proposta, Projeto
from projetos.models import Configuracao, Area, AreaDeInteresse

from .support import retorna_ternario, ordena_propostas_novo, ordena_propostas
from .support import envia_proposta, preenche_proposta


@login_required
@permission_required("users.altera_professor", login_url='/')
def index_propostas(request):
    """Mostra página principal de Propostas."""

    context = {}

    return render(request, 'propostas/index_propostas.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def mapeamento(request):
    """Chama o mapeamento entre estudantes e projetos do próximo semestre."""

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano
        semestre = configuracao.semestre
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    ano, semestre = adianta_semestre(ano, semestre)  # Vai para próximo semestre

    return redirect('map_est_proj', anosemestre="{0}.{1}".format(ano, semestre))


@login_required
@permission_required("users.altera_professor", login_url='/')
def map_est_proj(request, anosemestre):
    """Mapeamento entre estudantes e projetos."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    ano = int(anosemestre.split(".")[0])
    semestre = int(anosemestre.split(".")[1])

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
                    proj = Projeto.objects.get(proposta=proposta, ano=ano, semestre=semestre)
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
                proposta_indice[proposta.id] = repetidas_limpa[proposta.organizacao.sigla] + 1
                repetidas_limpa[proposta.organizacao.sigla] -= 1
        else:
            if proposta.nome_organizacao in repetidas_limpa:
                proposta_indice[proposta.id] = repetidas_limpa[proposta.nome_organizacao] + 1
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
    }
    return render(request, 'propostas/mapeamento_estudante_projeto.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def procura_propostas(request):
    """Exibe um histograma com a procura das propostas pelos estudantes."""

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano
        semestre = configuracao.semestre
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    curso = "T"  # por padrão todos os cursos

    ano, semestre = adianta_semestre(ano, semestre)

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
            return HttpResponse("Algum erro não identificado (POST incompleto).", status=401)

    mylist = ordena_propostas_novo(True, ano=ano, semestre=semestre, curso=curso)

    propostas = []
    prioridades = [[], [], [], [], []]
    estudantes = [[], [], [], [], []]

    if len(mylist) > 0:
        unzipped_object = zip(*mylist)
        propostas,\
        prioridades[0], prioridades[1], prioridades[2], prioridades[3], prioridades[4],\
        estudantes[0], estudantes[1], estudantes[2], estudantes[3], estudantes[4]\
             = list(unzipped_object)

    # Para procurar as áreas mais procuradas nos projetos
    opcoes = Opcao.objects.filter(aluno__user__tipo_de_usuario=1, aluno__trancado=False)

    if ano > 0:  # Ou seja não são todos os anos e semestres
        opcoes = opcoes.filter(aluno__anoPFE=ano, aluno__semestrePFE=semestre)
        opcoes = opcoes.filter(proposta__ano=ano, proposta__semestre=semestre)

    opcoes = opcoes.filter(prioridade=1)

    if curso != "T":  # Caso não se deseje todos os cursos, se filtra qual se deseja
        opcoes = opcoes.filter(aluno__curso=curso)

    areaspfe = {}
    areas = Area.objects.filter(ativa=True)
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

    edicoes, _, _ = get_edicoes(Proposta)

    context = {
        'tamanho': tamanho,
        'propostas': propostas,
        'prioridades': prioridades,
        'estudantes': estudantes,
        'ano': ano,
        'semestre': semestre,
        'areaspfe': areaspfe,
        'opcoes': opcoes,
        "edicoes": edicoes,
    }

    return render(request, 'propostas/procura_propostas.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def propostas_apresentadas(request):
    """Lista todas as propostas de projetos."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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
                propostas_filtradas = Proposta.objects.filter(ano=ano, semestre=semestre)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, ano, semestre = get_edicoes(Proposta)
        propostas_filtradas = Proposta.objects.filter(ano=ano, semestre=semestre)

    propostas_filtradas = propostas_filtradas.order_by("ano", "semestre", "organizacao", "titulo",)

    ternario_aprovados = retorna_ternario(propostas_filtradas.filter(disponivel=True))
    ternario_pendentes = retorna_ternario(propostas_filtradas.filter(disponivel=False))

    dic_organizacoes = {}
    for proposta in propostas_filtradas:
        if proposta.organizacao and proposta.organizacao not in dic_organizacoes:
            dic_organizacoes[proposta.organizacao] = 0
    num_organizacoes = len(dic_organizacoes)

    edicoes, ano, semestre = get_edicoes(Proposta)

    context = {
        'propostas': propostas_filtradas,
        'num_organizacoes': num_organizacoes,
        'ternario_aprovados': ternario_aprovados,
        'ternario_pendentes': ternario_pendentes,
        'configuracao': configuracao,
        "edicoes": edicoes,
    }
    return render(request, 'propostas/propostas_apresentadas.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def proposta_completa(request, primakey):
    """Mostra um projeto por completo."""

    try:
        proposta = Proposta.objects.get(pk=primakey)
    except Proposta.DoesNotExist:
        return HttpResponse("Proposta não encontrada.", status=401)

    if request.method == 'POST':
        if 'autorizador' in request.POST:
            try:
                if request.POST['autorizador'] == "0":
                    proposta.autorizado = None
                else:
                    proposta.autorizado = PFEUser.objects.get(pk=int(request.POST['autorizador']))
                proposta.disponivel = request.POST['disponibilizar'] == 'sim'
                proposta.save()
            except PFEUser.DoesNotExist:
                return HttpResponse("Autorizador não encontrado.", status=401)
        else:
            return HttpResponse("Autorizador não encontrado.", status=401)
        if proposta.disponivel:
            mensagem = "Proposta disponibilizada."
        else:
            mensagem = "Proposta indisponibilizada."
        context = {
            "area_principal": True,
            "propostas_lista": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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

    areas = Area.objects.filter(ativa=True)

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
    }
    return render(request, 'propostas/proposta_completa.html', context=context)


@login_required
def proposta_detalhes(request, primarykey):
    """Exibe uma proposta de projeto com seus detalhes para o estudante aplicar."""

    try:
        proposta = Proposta.objects.get(pk=primarykey)
    except Proposta.DoesNotExist:
        return HttpResponse("Proposta não encontrada.", status=401)

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    if user.tipo_de_usuario == 1:  # (1, 'aluno')
        if not (user.aluno.anoPFE == proposta.ano and user.aluno.semestrePFE == proposta.semestre):
            return HttpResponse("Usuário não tem permissão de acesso.", status=401)
        if not proposta.disponivel:
            return HttpResponse("Usuário não tem permissão de acesso.", status=401)

    if user.tipo_de_usuario == 3:  # (3, 'parceiro')
        return HttpResponse("Usuário não tem permissão de acesso.", status=401)

    context = {
        'proposta': proposta,
        'MEDIA_URL': settings.MEDIA_URL,
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
            mensagem = "Você não está cadastrado como parceiro de uma organização!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        if user.tipo_de_usuario == 3:  # parceiro
            try:
                parceiro = Parceiro.objects.get(pk=request.user.parceiro.pk)
            except Parceiro.DoesNotExist:
                return HttpResponse("Parceiro não encontrado.", status=401)
        elif user.tipo_de_usuario == 2:  # professor
            try:
                professor = Professor.objects.get(pk=request.user.professor.pk)
            except Professor.DoesNotExist:
                return HttpResponse("Professor não encontrado.", status=401)
        elif user.tipo_de_usuario == 4:  # admin
            try:
                administrador = Administrador.objects.get(pk=request.user.administrador.pk)
            except Administrador.DoesNotExist:
                return HttpResponse("Administrador não encontrado.", status=401)

    try:
        proposta = Proposta.objects.get(slug=slug)
    except Proposta.DoesNotExist:
        return HttpResponseNotFound('<h1>Proposta de Projeto não encontrada!</h1>')

    try:
        configuracao = Configuracao.objects.get()
        liberadas_propostas = configuracao.liberadas_propostas
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if request.method == 'POST':
        if (not liberadas_propostas) or (user.tipo_de_usuario == 4):
            preenche_proposta(request, proposta)
            enviar = "mensagem" in request.POST  # Por e-mail se enviar
            mensagem = envia_proposta(proposta, enviar)
            resposta = "Submissão de proposta de projeto atualizada com sucesso.<br>"

            if enviar:
                resposta += "Você deve receber um e-mail de confirmação nos próximos instantes.<br>"

            resposta += "<br><hr>"
            resposta += mensagem

            context = {
                "voltar": True,
                "mensagem": resposta,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Propostas não liberadas para edição.", status=401)

    areas = Area.objects.filter(ativa=True)

    context = {
        'liberadas_propostas': liberadas_propostas,
        'full_name': proposta.nome,
        'email': proposta.email,
        'organizacao': proposta.nome_organizacao,
        'website': proposta.website,
        'endereco': proposta.endereco,
        'descricao_organizacao': proposta.descricao_organizacao,
        'parceiro': parceiro,
        'professor': professor,
        'administrador': administrador,
        'contatos_tecnicos': proposta.contatos_tecnicos,
        'contatos_adm': proposta.contatos_administrativos,
        'info_departamento': proposta.departamento,
        'titulo': proposta.titulo,
        'desc_projeto': proposta.descricao,
        'expectativas': proposta.expectativas,
        'areast': areas,
        'recursos': proposta.recursos,
        'observacoes': proposta.observacoes,
        'proposta': proposta,
        'edicao': True,
        'interesses': Proposta.TIPO_INTERESSE,
        'tipo_de_interesse': proposta.tipo_de_interesse,
    }
    return render(request, 'organizacoes/proposta_submissao.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def validate_alunos(request):
    """Ajax para validar vaga de estudantes em propostas."""

    proposta_id = int(request.GET.get('proposta', None))
    vaga = request.GET.get('vaga', "  ")
    checked = request.GET.get('checked', None) == "true"

    try:
        proposta = Proposta.objects.get(id=proposta_id)

        if vaga[0] == 'C':
            if vaga[1] == '1':
                proposta.perfil_aluno1_computacao = checked
            elif vaga[1] == '2':
                proposta.perfil_aluno2_computacao = checked
            elif vaga[1] == '3':
                proposta.perfil_aluno3_computacao = checked
            elif vaga[1] == '4':
                proposta.perfil_aluno4_computacao = checked

        if vaga[0] == 'M':
            if vaga[1] == '1':
                proposta.perfil_aluno1_mecanica = checked
            elif vaga[1] == '2':
                proposta.perfil_aluno2_mecanica = checked
            elif vaga[1] == '3':
                proposta.perfil_aluno3_mecanica = checked
            elif vaga[1] == '4':
                proposta.perfil_aluno4_mecanica = checked

        if vaga[0] == 'X':
            if vaga[1] == '1':
                proposta.perfil_aluno1_mecatronica = checked
            elif vaga[1] == '2':
                proposta.perfil_aluno2_mecatronica = checked
            elif vaga[1] == '3':
                proposta.perfil_aluno3_mecatronica = checked
            elif vaga[1] == '4':
                proposta.perfil_aluno4_mecatronica = checked

        proposta.save()
    except Proposta.DoesNotExist:
        return HttpResponseNotFound('<h1>Proposta não encontrada!</h1>')

    data = {
        'atualizado': True,
    }

    return JsonResponse(data)
