"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""


from django.shortcuts import render

from django.contrib.auth.decorators import login_required, permission_required

#from users.models import Aluno, Professor, Parceiro, , Opcao, Alocacao
from users.models import PFEUser, Administrador

#from projetos.models import ObjetivosDeAprendizagem, Avaliacao2, Observacao, Area, AreaDeInteresse
from projetos.models import Area, Proposta

@login_required
@permission_required("users.altera_valores", login_url='/projetos/')
def index_parceiros(request):
    """Mostra página principal do usuário que é um parceiro de uma organização."""
    return render(request, 'parceiros/index_parceiros.html')

@login_required
@permission_required('users.altera_parceiro', login_url='/projetos/')
def parceiro_propostas(request):
    """Lista todas as propostas de projetos."""

    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
        mensagem = "Você não está cadastrado como parceiro de uma organização!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    propostas = Proposta.objects.filter(organizacao=user.parceiro.organizacao).\
                        order_by("ano", "semestre", "titulo",)
    context = {
        'propostas': propostas,
    }
    return render(request, 'projetos/parceiro_propostas.html', context)

#@login_required
def proposta_submissao(request):
    """Formulário de Submissão de Proposta de Projetos."""
    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        user = None

    parceiro = None
    professor = None
    administrador = None
    organizacao = ""
    website = "http://"
    endereco = ""
    descricao_organizacao = ""
    full_name = ""
    email_sub = ""

    if user:

        if user.tipo_de_usuario == 1: # alunos
            mensagem = "Você não está cadastrado como parceiro de uma organização!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        full_name = user.get_full_name()
        email_sub = user.email

        if user.tipo_de_usuario == 3: # parceiro
            try:
                parceiro = Parceiro.objects.get(pk=request.user.parceiro.pk)
            except Parceiro.DoesNotExist:
                return HttpResponse("Parceiro não encontrado.", status=401)
            organizacao = parceiro.organizacao
            website = parceiro.organizacao.website
            endereco = parceiro.organizacao.endereco
            descricao_organizacao = parceiro.organizacao.informacoes
        elif user.tipo_de_usuario == 2: # professor
            try:
                professor = Professor.objects.get(pk=request.user.professor.pk)
            except Professor.DoesNotExist:
                return HttpResponse("Professor não encontrado.", status=401)
        elif user.tipo_de_usuario == 4: # admin
            try:
                administrador = Administrador.objects.get(pk=request.user.administrador.pk)
            except Administrador.DoesNotExist:
                return HttpResponse("Administrador não encontrado.", status=401)

    if request.method == 'POST':
        proposta = preenche_proposta(request, None)
        mensagem = envia_proposta(proposta) # Por e-mail

        resposta = "Submissão de proposta de projeto realizada com sucesso.<br>"
        resposta += "Você deve receber um e-mail de confirmação nos próximos instantes.<br>"
        resposta += mensagem
        context = {
            "voltar": True,
            "mensagem": resposta,
        }
        return render(request, 'generic.html', context=context)

    areas = Area.objects.filter(ativa=True)

    organizacao_str = request.GET.get('organizacao', None)
    if organizacao_str:
        try:
            organizacao_id = int(organizacao_str)
            organizacao = Organizacao.objects.get(id=organizacao_id)
        except (ValueError, Organizacao.DoesNotExist):
            return HttpResponseNotFound('<h1>Organização não encontrado!</h1>')

    context = {
        'full_name' : full_name,
        'email' : email_sub,
        'organizacao' : organizacao,
        'website' : website,
        'endereco' : endereco,
        'descricao_organizacao' : descricao_organizacao,
        'parceiro' : parceiro,
        'professor' : professor,
        'administrador' : administrador,
        'contatos_tecnicos' : "",
        'contatos_adm' : "",
        'info_departamento' : "",
        'titulo' : "",
        'desc_projeto' : "",
        'expectativas' : "",
        'areast' : areas,
        'recursos' : "",
        'observacoes' : "",
        'edicao' : False,
        'interesses' : Proposta.TIPO_INTERESSE,
        'tipo_de_interesse' : 0 # Não existe na verdade
    }
    return render(request, 'parceiros/proposta_submissao.html', context)
