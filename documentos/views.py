#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import os
import re
import json
import zipfile
import tempfile
import random
import string

from django.http import FileResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied

from professores.support import recupera_orientadores
from professores.support import recupera_coorientadores
from professores.support import recupera_bancas_intermediarias
from professores.support import recupera_bancas_finais
from professores.support import recupera_bancas_falconi
from professores.support import recupera_mentorias
from professores.support import recupera_mentorias_técnica

from projetos.models import Documento, Configuracao, Projeto, Certificado
from projetos.support import get_upload_path

from users.support import get_edicoes

from operacional.models import Curso

from .support import render_pdf_file

from documentos.models import TipoDocumento

#@login_required
def index_documentos(request):
    """Lista os documentos armazenados no servidor."""
    configuracao = get_object_or_404(Configuracao)
    areas = json.loads(configuracao.index_documentos) if configuracao.index_documentos else None
    context = {
        "titulo": "Documentações",
        "documentos": Documento.objects.all(),
        "areas": areas,
    }
    return render(request, "documentos/index_documentos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def certificados_submetidos(request, edicao=None, tipos=None, gerados=None):
    """Lista os Certificados Emitidos."""

    configuracao = get_object_or_404(Configuracao)
    coordenacao = configuracao.coordenacao
    context = {
        "titulo": "Certificados Emitidos",
        "coordenacao": coordenacao,
        "configuracao": configuracao,
    }

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                certificados = Certificado.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                certificados = Certificado.objects.filter(projeto__ano=ano, projeto__semestre=semestre)
            context["certificados"] = certificados
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, ano, semestre = get_edicoes(Certificado)
        context["edicoes"] = edicoes
        if edicao:
            context["selecionada"] = edicao
        if tipos:
            context["tipos"] = tipos.split(',')
        if gerados:
            context["gerados"] = gerados


    return render(request, "documentos/certificados_submetidos.html", context)


def atualiza_certificado(usuario, projeto, tipo_cert, arquivo, banca=None):
    """Atualiza os certificados."""
    configuracao = get_object_or_404(Configuracao)

    (certificado, _) = \
        Certificado.objects.get_or_create(usuario=usuario,
                                          projeto=projeto,
                                          tipo_de_certificado=tipo_cert)

    tipo_documento = TipoDocumento.objects.get(sigla="PT")
    papel_timbrado = Documento.objects.filter(tipo_documento=tipo_documento).last()

    context = {
        "projeto": projeto,
        "configuracao": configuracao,
        "papel_timbrado": papel_timbrado.documento.url[1:],
    }

    if projeto and not certificado.documento:
        if tipo_cert == 101:
            tipo = "_orientacao"
        elif tipo_cert == 102:
            context["usuario"] = usuario
            tipo = "_coorientacao"
        elif tipo_cert == 103:
            context["usuario"] = usuario
            context["banca"] = banca
            tipo = "_banca_intermediaria"
        elif tipo_cert == 104:
            context["usuario"] = usuario
            context["banca"] = banca
            tipo = "_banca_final"
        elif tipo_cert == 105:
            context["usuario"] = usuario
            context["banca"] = banca
            tipo = "_banca_falconi"
        elif tipo_cert == 106:
            context["usuario"] = usuario
            context["dinamica"] = banca
            tipo = "_mentoria_profissional"
        elif tipo_cert == 107:
            context["usuario"] = usuario
            context["count_projetos"] = banca
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
@permission_required("users.altera_professor", raise_exception=True)
def selecao_geracao_certificados(request):
    """Recupera um certificado pelos dados."""
    context = {"edicoes": get_edicoes(Projeto)[0]}
    return render(request, "documentos/selecao_geracao_certificados.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def gerar_certificados(request):
    """Recupera um certificado pelos dados."""
    configuracao = get_object_or_404(Configuracao)

    if not configuracao.coordenacao or\
       not configuracao.coordenacao.assinatura or\
       not os.path.exists(settings.MEDIA_ROOT+"/"+str(configuracao.coordenacao.assinatura)):
        return HttpResponse("Arquivo de assinatura não encontrado.", status=401)
    
    tipo_documento = TipoDocumento.objects.get(sigla="PT")  # Papel Timbrado
    papel_timbrado = Documento.objects.filter(tipo_documento=tipo_documento).last()
    if not papel_timbrado or\
       not os.path.exists(settings.MEDIA_ROOT+"/"+str(papel_timbrado.documento)):
        return HttpResponse("Papel timbrado não encontrado.", status=401)

    if "edicao" in request.POST:
        ano, semestre = request.POST["edicao"].split('.')
    else:
        return HttpResponse("Algum erro não identificado.", status=401)

    tipos = []

    certificados = []
    if "orientador" in request.POST:
        # (101, "Orientação de Projeto"),
        orientadores = recupera_orientadores(ano, semestre)
        arquivo = "documentos/certificado_orientador.html"
        tipos.append("O")
        for orientador in orientadores:
            for projeto in orientador[1]:
                certificado = atualiza_certificado(orientador[0].user, projeto, 101, arquivo)
                if certificado:
                    certificados.append(certificado)

    if "coorientador" in request.POST:
        # (102, "Coorientação de Projeto"),
        coorientadores = recupera_coorientadores(ano, semestre)
        arquivo = "documentos/certificado_coorientador.html"
        tipos.append("C")
        for coorientador in coorientadores:
            for projeto in coorientador[1]:
                certificado = atualiza_certificado(coorientador[0].user, projeto, 102, arquivo)
                if certificado:
                    certificados.append(certificado)

    if "banca" in request.POST:
        # (103, "Membro de Banca Intermediária"),
        membro_banca = recupera_bancas_intermediarias(ano, semestre)
        arquivo = "documentos/certificado_banca_intermediaria.html"
        tipos.append("B")
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0].user, banca.get_projeto(), 103, arquivo, banca=banca)
                if certificado:
                    certificados.append(certificado)

    if "banca" in request.POST:
        # (104, "Membro de Banca Final"),
        membro_banca = recupera_bancas_finais(ano, semestre)
        arquivo = "documentos/certificado_banca_final.html"
        tipos.append("B")
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0].user, banca.get_projeto(), 104, arquivo, banca=banca)
                if certificado:
                    certificados.append(certificado)

    if "banca" in request.POST:
        # (105, "Membro de Banca Falconi"),
        membro_banca = recupera_bancas_falconi(ano, semestre)
        arquivo = "documentos/certificado_banca_falconi.html"
        tipos.append("B")
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0].user, banca.get_projeto(), 105, arquivo, banca=banca)
                if certificado:
                    certificados.append(certificado)

    if "mentoria_profissional" in request.POST:
        # (106, "Mentoria de Grupo"),  # mentor Profissional (antiga Mentoria Falconi)
        membro_banca = recupera_mentorias(ano, semestre)
        arquivo = "documentos/certificado_mentoria.html"
        tipos.append("MP")
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0], banca.get_projeto(), 106, arquivo, banca=banca)
                if certificado:
                    certificados.append(certificado)

    if "mentoria_tecnica" in request.POST:
        # (107, "Mentoria Técnica"),  # mentor da empresa
        membros = recupera_mentorias_técnica(ano, semestre)
        arquivo = "documentos/certificado_mentoria_tecnica.html"
        tipos.append("MT")
        for membro in membros:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0], banca.get_projeto(), 107, arquivo, banca=banca)
                if certificado:
                    certificados.append(certificado)


    return redirect("certificados_submetidos", edicao=request.POST["edicao"], tipos=",".join(tipos), gerados=len(certificados))


def materias_midia(request):
    """Exibe Matérias que houveram na mídia."""
    tipo_documento = TipoDocumento.objects.get(nome="Matéria na Mídia")
    documentos = Documento.objects.filter(tipo_documento=tipo_documento)
    context = {
        "titulo": "Matérias na Mídia",
        "documentos": documentos,
        "tipo": tipo_documento,
        }
    return render(request, "documentos/materias_midia.html", context)


# @login_required
def relatorios_publicos(request, edicao=None):
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

        context = {
            "titulo": "Relatórios Públicos",
            "edicoes": get_edicoes(Projeto)[0],
            "selecionada": edicao,
        }
    
    return render(request, "documentos/relatorios_publicos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_documentos(request):
    """Exibe tabela com todos os documentos armazenados."""
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            if edicao == "todas":
                projetos = Projeto.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

            if "curso" in request.POST:
                curso = request.POST["curso"]
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

            # Filtra para projetos com estudantes de um curso específico
            if curso != "TE":
                if curso != 'T':
                    projetos = projetos.filter(alocacao__aluno__curso2__sigla_curta=curso).distinct()
                else:
                    projetos = projetos.filter(alocacao__aluno__curso2__in=cursos_insper).distinct()

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

        context = {
            "titulo": "Documentação dos Projetos",
            "edicoes": get_edicoes(Projeto)[0],
            "informacoes": informacoes,
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "documentos/tabela_documentos.html", context)


# Function to generate a unique arcname if the provided one already exists in the zip file
def generate_unique_arcname(zip_file, arcname):
    arcname = arcname.replace('\\','/')
    if arcname not in zip_file.namelist():
        return arcname
    else:
        base_name, extension = os.path.splitext(arcname)
        counter = 1
        while True:
            new_arcname = f"{base_name}_{counter}{extension}"
            if new_arcname not in zip_file.namelist():
                return new_arcname
            counter += 1

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def exportar_documentos_projetos(request):
    """Exibe tabela com todos os documentos armazenados."""
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")
    
    tipos_documentos = TipoDocumento.objects.filter(projeto=True)

    context = {
        "titulo": "Exportar Documentos dos Projetos",
        "edicoes": get_edicoes(Projeto)[0],
        "cursos": cursos_insper,
        "cursos_externos": cursos_externos,
        "lista": tipos_documentos,
    }

    if "edicao" in request.POST:
        edicao = request.POST["edicao"]

        if edicao == "todas":
            projetos = Projeto.objects.all()
        else:
            ano, semestre = request.POST["edicao"].split('.')
            projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

        if "curso" in request.POST:
            curso = request.POST["curso"]
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        # Filtra para projetos com estudantes de um curso específico
        curso_sigla = ""
        if curso != "TE":
            if curso != 'T':
                projetos = projetos.filter(alocacao__aluno__curso2__sigla_curta=curso).distinct()
                curso_sigla = Curso.objects.get(sigla_curta=curso).sigla + "_"
            else:
                projetos = projetos.filter(alocacao__aluno__curso2__in=cursos_insper).distinct()

        context["projetos"] = projetos
        context["edicao"] = edicao

        if request.is_ajax():
            pass

        elif request.method == "POST":  # Significa que o usuário clicou no botão de exportar

            selecionados = request.POST.getlist("selection")
            tipos_documentos_selecionados = TipoDocumento.objects.filter(sigla__in=selecionados)

            # Return all the objects that point to files
            documentos = Documento.objects.filter(projeto__in=projetos, tipo_documento__in=tipos_documentos_selecionados)
            
            # Create a zip file
            nome_arquivo = "documentos_" + curso_sigla + edicao.replace('.', '_') + ".zip"
            # Random sequence of characters to avoid name conflicts
            sequencia_aleatoria = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            zip_path = os.path.join(settings.MEDIA_ROOT + "/tmp", "documentos_" + sequencia_aleatoria + ".zip")
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                
                # Loop over all documents
                for documento in documentos:
                    if documento.projeto:
                        projeto_titulo = re.sub(r"\W+", "", documento.projeto.get_titulo().replace(' ', '_'))
                    else:
                        projeto_titulo = "sem_projeto"
                    
                    if documento.usuario and documento.usuario.username:
                        username = re.sub(r'\W+', '', documento.usuario.username.replace(' ', '_'))
                    else:
                        username = "sem_usuario"

                    if documento.tipo_documento and documento.tipo_documento.nome:
                        tipo_documento = re.sub(r"\W+", "", documento.tipo_documento.nome.replace(' ', '_'))
                    else:
                        tipo_documento = "sem_tipo_documento"

                    # Get the path of the file
                    if documento.documento:
                        local_path = os.path.join(settings.MEDIA_ROOT, "{0}".format(documento.documento))
                        file_path = os.path.abspath(local_path)
                        if ".." in file_path:
                            raise PermissionDenied
                        if os.path.exists(file_path):
                            # Add the file to the zip file
                            virtual_path = projeto_titulo
                            if documento.tipo_documento and documento.tipo_documento.individual:
                                virtual_path = virtual_path + "/" + username
                            
                            basename = os.path.basename(file_path)
                            _, extension = os.path.splitext(basename)
                            filename = tipo_documento + extension
                            arcname = os.path.join(virtual_path, filename)
                            unique_arcname = generate_unique_arcname(zip_file, arcname)
                            zip_file.write(file_path, arcname=unique_arcname)

                    if documento.link:
                        # Documento does not have a file, create a temporary text file
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            redirect_content = "<html><head><meta http-equiv='refresh' content='0; url={0}'></head></html>".format(documento.link)
                            temp_file.write(redirect_content.encode("utf-8"))
                            temp_file_path = temp_file.name
                            print(temp_file_path)
                        
                        virtual_path = projeto_titulo
                        if documento.tipo_documento and documento.tipo_documento.individual:
                            virtual_path = virtual_path + "/" + username
                        
                        filename = tipo_documento + ".html"
                        arcname = os.path.join(virtual_path, filename)
                        unique_arcname = generate_unique_arcname(zip_file, arcname)
                        zip_file.write(temp_file_path, arcname=unique_arcname)
                        # The file is no longer needed, removing it
                        os.remove(temp_file_path)

            # Open the zip file and return it as a response
            return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=nome_arquivo)

    return render(request, "documentos/exportar_documentos_projetos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_seguros(request):
    """Exibe tabela com todos os seguros armazenados."""
    tipo_documento = TipoDocumento.objects.get(nome="Seguros")
    seguros = Documento.objects.filter(tipo_documento=tipo_documento)
    context = {
        "titulo": "Seguros Emitidos",
        "seguros": seguros,
        }
    return render(request, "documentos/tabela_seguros.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_atas(request):
    """Exibe tabela com todos os seguros armazenados."""
    try:
        tipo_ata = TipoDocumento.objects.get(nome="Ata do Comitê")
        atas = Documento.objects.filter(tipo_documento=tipo_ata).order_by("-data")
    except TipoDocumento.DoesNotExist:
        return HttpResponse("Tipo de Documento para Ata do Comitê não encontrado.", status=401)

    try:
        tipo_template = TipoDocumento.objects.get(sigla="TAC")  # Template Ata Comitê
        template = Documento.objects.filter(tipo_documento=tipo_template).last()
    except TipoDocumento.DoesNotExist:
        return HttpResponse("Tipo de Documento para Template de Ata do Comitê não encontrado.", status=401)

    context = {
        "titulo": "Atas do Comitê Capstone",
        "atas": atas,
        "template": template,
        "tipo": tipo_ata,
    }
    return render(request, "documentos/tabela_atas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_imagens(request):
    """Exibe tabela com todos as imagens (vídeos e fotos) produzidos no semestre."""
    try:
        tipo_imagens = TipoDocumento.objects.get(nome="Imagens do Semestre")
        imagens = Documento.objects.filter(tipo_documento=tipo_imagens).order_by("-data")
    except TipoDocumento.DoesNotExist:
        return HttpResponse("Tipo de Documento para Imagens do Semestre não encontrado.", status=401)

    context = {
        "titulo": "Tabela de Vídeos e Fotos do Semestre",
        "documentos": imagens,
        "tipo": tipo_imagens,
    }
    return render(request, "documentos/tabela_imagens.html", context)


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
        }

    else:
        context = {
            "titulo": "Contratos Assinados",
            "edicoes": get_edicoes(Projeto)[0],
            }

    return render(request, "documentos/contratos_assinados.html", context)
