#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

import os
import re
import mimetypes

from wsgiref.util import FileWrapper

from django.conf import settings

from django.contrib.auth.decorators import login_required

from django.core.exceptions import PermissionDenied

from django.http.response import StreamingHttpResponse
from django.http import Http404
from django.http import HttpResponse

from django.shortcuts import render, get_object_or_404

from users.models import PFEUser, Alocacao
from documentos.models import TipoDocumento

from .models import Documento

# FONTE: https://stackoverflow.com/questions/33208849/
# ... python-django-streaming-video-mp4-file-using-httpresponse/41289535#41289535
class RangeFileWrapper:
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def close(self):
        if hasattr(self.filelike, 'close'):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            # If remaining is None, we're reading the entire file.
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()

        if self.remaining <= 0:
            raise StopIteration()
        data = self.filelike.read(min(self.remaining, self.blksize))
        if not data:
            raise StopIteration()
        self.remaining -= len(data)
        return data


def stream_video(request, path, content_type=None):
    range_header = request.META.get("HTTP_RANGE", '').strip()
    range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
    range_match = range_re.match(range_header)
    size = os.path.getsize(path)
    # content_type, encoding = mimetypes.guess_type(path)
    if not content_type:
        content_type, _ = mimetypes.guess_type(path)
    if not content_type:
        content_type = content_type or "application/octet-stream"
    resp = None
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(RangeFileWrapper(open(path, "rb"), offset=first_byte, length=length),
                                     status=206, content_type=content_type)
        #resp["Content-Length"] = str(length)
        resp["Content-Range"] = "bytes %s-%s/%s" % (first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(open(path, "rb")), content_type=content_type)
        resp["Content-Length"] = str(size)
    resp["Accept-Ranges"] = "bytes"
    return resp


def get_response(file, path, request):
    """Checa extensão do arquivo e retorna HttpRensponse corespondente."""
    # Exemplos:
    # image/gif, image/tiff, application/zip,
    # audio/mpeg, audio/ogg, text/csv, text/plain
    if path[-3:].lower() == "jpg" or path[-4:].lower() == "jpeg":
        return HttpResponse(file.read(), content_type="image/jpeg")
    elif path[-3:].lower() == "png":
        return HttpResponse(file.read(), content_type="image/png")
    elif path[-3:].lower() == "gif":
        return HttpResponse(file.read(), content_type="image/gif")
    elif path[-3:].lower() == "bmp":
        return HttpResponse(file.read(), content_type="image/bmp")
    elif path[-4:].lower() == "avif":
        return HttpResponse(file.read(), content_type="image/avif")
    elif path[-4:].lower() == "webp":
        return HttpResponse(file.read(), content_type="image/webp")
    elif path[-4:].lower() == "apng":
        return HttpResponse(file.read(), content_type="image/apng")
    elif path[-3:].lower() == "tif" or path[-4:].lower() == "tiff":
        return HttpResponse(file.read(), content_type="image/tiff")
    elif path[-3:].lower() == "svg" or path[-4:].lower() == "svgz":
        return HttpResponse(file.read(), content_type="image/svg+xml")
    elif path[-3:].lower() == "doc":
        return HttpResponse(file.read(), content_type=\
            "application/msword")
    elif path[-4:].lower() == "docx":
        return HttpResponse(file.read(), content_type=\
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif path[-3:].lower() == "ppt":
        return HttpResponse(file.read(), content_type=\
            "application/vnd.ms-powerpoint")
    elif path[-4:].lower() == "pptx":
        return HttpResponse(file.read(), content_type=\
            "application/vnd.openxmlformats-officedocument.presentationml.presentation")
    elif path[-3:].lower() == "xls":
        return HttpResponse(file.read(), content_type=\
            "application/vnd.ms-excel")
    elif path[-4:].lower() == "xlsx":
        return HttpResponse(file.read(), content_type=\
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    elif path[-3:].lower() == "csv":
        return HttpResponse(file.read(), content_type="text/comma-separated-values")
    elif path[-3:].lower() == "pdf":
        return HttpResponse(file.read(), content_type="application/pdf")
    elif path[-3:].lower() == "mp4":
        return stream_video(request, file.name, "video/mp4")
    elif path[-3:].lower() == "mpg" or path[-4:].lower() == "mpeg":
        return stream_video(request, file.name, "video/mpeg")
    elif path[-3:].lower() == "ogv":
        return stream_video(request, file.name, "video/ogg")
    elif path[-3:].lower() == "mov":
        return stream_video(request, file.name, "video/mp4")  # Não funcionando: "video/quicktime"
    elif path[-3:].lower() == "mkv":
        return HttpResponse(file.read(), content_type="video/webm")
    elif path[-3:].lower() == "zip" or path[-3:].lower() == "rar" or path[-4:].lower() == "7zip":
        return HttpResponse(file.read(), content_type="application/octet-stream")
    else:
        return None

def le_arquivo(request, local_path, path, bypass_confidencial=False):
    """Lê os arquivos pela URL."""
    file_path = os.path.abspath(local_path)
    if ".." in file_path:
        raise PermissionDenied
    # if "\\" in file_path:   # Protecao, porem nao funciona no windows
    #     raise PermissionDenied
    if os.path.exists(file_path):
        documento = local_path[len(settings.BASE_DIR) + len(settings.MEDIA_URL):]

        doc = Documento.objects.filter(documento=documento).last()
        if doc:
            mensagem = "Documento Confidencial"
            context = {"mensagem": mensagem,}

            if not bypass_confidencial: # Soh para o caso de documentos de bancas

                try:
                    user = PFEUser.objects.get(pk=request.user.pk)
                except PFEUser.DoesNotExist:
                    if doc.confidencial: 
                        return render(request, "generic.html", context=context)

                if (doc.confidencial) and \
                    not ((user.tipo_de_usuario == 2) or (user.tipo_de_usuario == 4)):

                    if (user.tipo_de_usuario == 1):
                        ## Verificar se o documento é do estudante ou do grupo dele
                        alocado_no_projeto = Alocacao.objects.filter(projeto=doc.projeto, aluno=user.aluno).exists()                    
                        if doc.tipo_documento.individual and doc.usuario != user:
                            return render(request, "generic.html", context=context)
                        elif not alocado_no_projeto:
                            return render(request, "generic.html", context=context)

                    elif (user.tipo_de_usuario == 3):
                        ## Verificar se o documento é da organização que o uruário faz parte
                        if doc.projeto is None:
                            return render(request, "generic.html", context=context)
                        if doc.projeto.proposta.organizacao != user.parceiro.organizacao:
                            return render(request, "generic.html", context=context)

                    else:
                        return render(request, "generic.html", context=context)
                    

        if documento[:3] == "tmp":
            mensagem = "Documento não acessível"
            context = {"mensagem": mensagem,}
            return render(request, 'generic.html', context=context)

        with open(file_path, "rb") as file:
            response = get_response(file, path, request)
            if not response:
                mensagem = "Erro ao carregar arquivo (formato não suportado)."
                context = {
                    "area_principal": True,
                    "mensagem": mensagem,
                }
                return render(request, "generic.html", context=context)
            response["Content-Disposition"] = "inline; filename=" +\
               os.path.basename(file_path)
            return response

    raise Http404


#@login_required
# Existe um controle de documentos confidenciais nos campos dos arquivos
def arquivos(request, path, documentos=None, organizacao=None, projeto=None, usuario=None):
    """Permite acessar arquivos do servidor."""
    if documentos is not None:
        local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}".format(documentos, path))
    elif organizacao is not None and projeto is not None and usuario is not None:
        local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}/{2}/{3}".format(organizacao, projeto, usuario, path))
    elif organizacao is not None and usuario is not None:
        local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}/{2}".format(organizacao, usuario, path))
    else:
        raise Http404
    return le_arquivo(request, local_path, path)

def doc(request, tipo):
    """Acessa arquivos do servidor pelo tipo dele se for publico."""
    tipo_documento = get_object_or_404(TipoDocumento, sigla=tipo)
    documento = Documento.objects.filter(tipo_documento=tipo_documento, confidencial=False).order_by("data").last()
    if documento is None:
        raise Http404
    path = str(documento.documento).split('/')[-1]
    local_path = os.path.join(settings.MEDIA_ROOT, "{0}".format(documento.documento))
    return le_arquivo(request, local_path, path)