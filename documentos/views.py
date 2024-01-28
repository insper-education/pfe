#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import os

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from professores.support import recupera_orientadores
from professores.support import recupera_coorientadores
from professores.support import recupera_bancas_intermediarias
from professores.support import recupera_bancas_finais
from professores.support import recupera_bancas_falconi
from professores.support import recupera_mentorias
from professores.support import recupera_mentorias_técnica

from projetos.models import Documento, Configuracao, Projeto, Certificado
from projetos.support import get_upload_path

# from users.models import PFEUser
from users.support import get_edicoes

from operacional.models import Curso

from .support import render_pdf_file



#@login_required
def index_documentos(request):
    """Lista os documentos armazenados no servidor."""
    context = {
        "documentos": Documento.objects.all(),
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, "documentos/index_documentos.html", context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def certificados_submetidos(request):
    """Lista os Certificados Emitidos."""
    edicoes = []

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            if edicao == 'todas':
                certificados = Certificado.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                certificados = Certificado.objects\
                    .filter(projeto__ano=ano, projeto__semestre=semestre)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, ano, semestre = get_edicoes(Certificado)
        certificados = Certificado.objects\
            .filter(projeto__ano=ano, projeto__semestre=semestre)

    configuracao = get_object_or_404(Configuracao)
    coordenacao = configuracao.coordenacao

    context = {
        "certificados": certificados,
        "edicoes": edicoes,
        "coordenacao": coordenacao,
        "configuracao": configuracao,
    }

    return render(request, 'documentos/certificados_submetidos.html', context)


def atualiza_certificado(usuario, projeto, tipo_cert, arquivo, banca=None):
    """Atualiza os certificados."""
    configuracao = get_object_or_404(Configuracao)
    (certificado, _created) = \
        Certificado.objects.get_or_create(usuario=usuario,
                                          projeto=projeto,
                                          tipo_de_certificado=tipo_cert)

    context = {
        "projeto": projeto,
        "configuracao": configuracao,
    }

    if projeto and not certificado.documento:
        if tipo_cert == 101:
            tipo = "_orientacao"
        elif tipo_cert == 102:
            context['usuario'] = usuario
            tipo = "_coorientacao"
        elif tipo_cert == 103:
            context['usuario'] = usuario
            context['banca'] = banca
            tipo = "_banca_intermediaria"
        elif tipo_cert == 104:
            context['usuario'] = usuario
            context['banca'] = banca
            tipo = "_banca_final"
        elif tipo_cert == 105:
            context['usuario'] = usuario
            context['banca'] = banca
            tipo = "_banca_falconi"
        elif tipo_cert == 106:
            context['usuario'] = usuario
            context['dinamica'] = banca
            tipo = "_mentoria_profissional"
        elif tipo_cert == 107:
            context['usuario'] = usuario
            context['count_projetos'] = banca
            tipo = "_mentoria_tecnica"
        else:
            tipo = ""

        path = get_upload_path(certificado, "")

        full_path = settings.MEDIA_ROOT + "/" + path
        os.makedirs(full_path, mode=0o777, exist_ok=True)

        filename = full_path + "certificado" + tipo + ".pdf"

        pdf = render_pdf_file(arquivo, context, filename)

        if (not pdf) or pdf.err:
            return HttpResponse("Erro ao gerar certificados.", status=401)

        certificado.documento = path + "certificado" + tipo + ".pdf"
        certificado.save()

        return certificado

    return None


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def selecao_geracao_certificados(request):
    """Recupera um certificado pelos dados."""

    edicoes, _, _ = get_edicoes(Projeto)
    

    context = {
        'edicoes': edicoes,
    }

    return render(request, 'documentos/selecao_geracao_certificados.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def gerar_certificados(request):
    """Recupera um certificado pelos dados."""
    configuracao = get_object_or_404(Configuracao)

    if not os.path.exists("arquivos/"+str(configuracao.assinatura)):
        return HttpResponse("Arquivo de assinatura não encontrado.", status=401)
    if not os.path.exists("arquivos/papel_timbrado.pdf"):
        return HttpResponse("Papel timbrado não encontrado.", status=401)

    if 'edicao' in request.POST:
        ano, semestre = request.POST['edicao'].split('.')
    else:
        return HttpResponse("Algum erro não identificado.", status=401)

    certificados = []
    if 'orientador' in request.POST:
        # (101, "Orientação de Projeto"),
        orientadores = recupera_orientadores(ano, semestre)
        arquivo = "documentos/certificado_orientador.html"
        for orientador in orientadores:
            for projeto in orientador[1]:
                certificado = atualiza_certificado(orientador[0].user,
                                                   projeto,
                                                   101,
                                                   arquivo)
                if certificado:
                    certificados.append(certificado)

    if 'coorientador' in request.POST:
        # (102, "Coorientação de Projeto"),
        coorientadores = recupera_coorientadores(ano, semestre)
        arquivo = "documentos/certificado_coorientador.html"
        for coorientador in coorientadores:
            for projeto in coorientador[1]:
                certificado = atualiza_certificado(coorientador[0].user,
                                                   projeto,
                                                   102,
                                                   arquivo)
                if certificado:
                    certificados.append(certificado)

    if 'banca' in request.POST:
        # (103, "Membro de Banca Intermediária"),
        membro_banca = recupera_bancas_intermediarias(ano, semestre)
        arquivo = "documentos/certificado_banca_intermediaria.html"
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0].user,
                                                   banca.projeto,
                                                   103,
                                                   arquivo,
                                                   banca=banca)
                if certificado:
                    certificados.append(certificado)

    if 'banca' in request.POST:
        # (104, "Membro de Banca Final"),
        membro_banca = recupera_bancas_finais(ano, semestre)
        arquivo = "documentos/certificado_banca_final.html"
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0].user,
                                                   banca.projeto,
                                                   104,
                                                   arquivo,
                                                   banca=banca)
                if certificado:
                    certificados.append(certificado)

    if 'banca' in request.POST:
        # (105, "Membro de Banca Falconi"),
        membro_banca = recupera_bancas_falconi(ano, semestre)
        arquivo = "documentos/certificado_banca_falconi.html"
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0].user,
                                                   banca.projeto,
                                                   105,
                                                   arquivo,
                                                   banca=banca)
                if certificado:
                    certificados.append(certificado)

    if 'mentoria_profissional' in request.POST:
        # (106, "Mentoria de Grupo"),  # mentor Profissional (antiga Mentoria Falconi)
        membro_banca = recupera_mentorias(ano, semestre)
    
        arquivo = "documentos/certificado_mentoria.html"
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0],
                                                   banca.projeto,
                                                   106,
                                                   arquivo,
                                                   banca=banca)
                if certificado:
                    certificados.append(certificado)

    if 'mentoria_tecnica' in request.POST:
        # (107, "Mentoria Técnica"),  # mentor da empresa
        membros = recupera_mentorias_técnica(ano, semestre)
        arquivo = "documentos/certificado_mentoria_tecnica.html"
        for membro in membros:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0],
                                                   banca.projeto,
                                                   107,
                                                   arquivo,
                                                   banca=banca)
                if certificado:
                    certificados.append(certificado)

    configuracao = get_object_or_404(Configuracao)
    coordenacao = configuracao.coordenacao

    context = {
        "certificados": certificados,
        "coordenacao": coordenacao,
        "configuracao": configuracao,
    }

    return render(request, 'documentos/gerar_certificados.html', context)

from documentos.models import TipoDocumento

def materias_midia(request):
    """Exibe Matérias que houveram na mídia."""
    tipo_documento = TipoDocumento.objects.get(nome="Matéria na Mídia")
    relatorios = Documento.objects.filter(tipo_documento=tipo_documento, confidencial=False)

    context = {
        "relatorios": relatorios,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, "documentos/materias_midia.html", context)


# @login_required
def relatorios_publicos(request):
    """Exibe relatórios públicos."""

    if request.is_ajax():
        
        tipo_documento = TipoDocumento.objects.get(nome="Relatório Publicado")

        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            relatorios = Documento.objects.filter(tipo_documento=tipo_documento, confidencial=False)\
                            .order_by("-projeto__ano", "-projeto__semestre")
            if edicao != "todas":
                ano, semestre = request.POST["edicao"].split('.')
                relatorios = relatorios.filter(projeto__ano=ano, projeto__semestre=semestre)

        else:
            return HttpResponse("Erro ao carregar dados.", status=401)

        context = {
            "relatorios": relatorios,
            "edicao": edicao,
        }

    else:
        edicoes, _, _ = get_edicoes(Projeto)
        context = {
            "edicoes": edicoes,
        }
    
    return render(request, "documentos/relatorios_publicos.html", context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def tabela_documentos(request):
    """Exibe tabela com todos os documentos armazenados."""

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']

            if edicao == 'todas':
                projetos = Projeto.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

            if 'curso' in request.POST:
                curso = request.POST['curso']    
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

            if curso != 'T':
                projetos = projetos.filter(alocacao__aluno__curso2__sigla_curta=curso).distinct()

        context = {
            "projetos": projetos,
            "edicao": edicao,
        }

    else:
    
        informacoes = [
            (".tit_ori", "Título Original"),
            (".curso", "Curso"),
            (".coorientadores", "Coorientadores"),
            (".confidencial", "Confidenciais"),
        ]
        edicoes, _, _ = get_edicoes(Projeto)
        context = {
            "edicoes": edicoes,
            "informacoes": informacoes,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, "documentos/tabela_documentos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_seguros(request):
    """Exibe tabela com todos os seguros armazenados."""
    tipo_documento = TipoDocumento.objects.get(nome="Seguros")
    seguros = Documento.objects.filter(tipo_documento=tipo_documento)
    context = {"seguros": seguros,}
    return render(request, "documentos/tabela_seguros.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_atas(request):
    """Exibe tabela com todos os seguros armazenados."""
    tipo_documento = TipoDocumento.objects.get(nome="Ata do Comitê do PFE")
    atas = Documento.objects.filter(tipo_documento=tipo_documento).order_by("-data")
    context = {"atas": atas,}
    return render(request, "documentos/tabela_atas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def contratos_assinados(request):
    """Exibe tabela com todos os documentos armazenados."""

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            if edicao == "todas":
                projetos = Projeto.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

        context = {
            "projetos": projetos,
            "edicao": edicao,
            "MEDIA_URL": settings.MEDIA_URL,
        }

    else:
        edicoes, _, _ = get_edicoes(Projeto)
        context = {
            "edicoes": edicoes,
        }

    return render(request, "documentos/contratos_assinados.html", context)
