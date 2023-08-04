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

from django.shortcuts import render

from users.models import PFEUser

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


def stream_video(request, path):
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
    range_match = range_re.match(range_header)
    size = os.path.getsize(path)
    # content_type, encoding = mimetypes.guess_type(path)
    content_type, _ = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'
    resp = None
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(RangeFileWrapper(open(path, 'rb'), offset=first_byte, length=length),
                                     status=206, content_type=content_type)
        #resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type=content_type)
        #resp['Content-Length'] = str(size)
    resp['Accept-Ranges'] = 'bytes'
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
    elif path[-3:].lower() == "doc":
        return HttpResponse(file.read(), content_type=\
            'application/msword')
    elif path[-4:].lower() == "docx":
        return HttpResponse(file.read(), content_type=\
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    elif path[-3:].lower() == "ppt":
        return HttpResponse(file.read(), content_type=\
            'application/vnd.ms-powerpoint')
    elif path[-4:].lower() == "pptx":
        return HttpResponse(file.read(), content_type=\
            'application/vnd.openxmlformats-officedocument.presentationml.presentation')
    elif path[-3:].lower() == "pdf":
        return HttpResponse(file.read(), content_type="application/pdf")
    elif path[-3:].lower() == "mp4":
        return stream_video(request, file.name)
    elif path[-3:].lower() == "mkv":
        return HttpResponse(file.read(), content_type="video/webm")
    else:
        return None

def le_arquivo(request, local_path, path):
    """Lê os arquivos pela URL."""
    file_path = os.path.abspath(local_path)
    print(file_path)
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

            try:
                user = PFEUser.objects.get(pk=request.user.pk)
            except PFEUser.DoesNotExist:
                if doc.confidencial: 
                    return render(request, 'generic.html', context=context)    

            if (doc.confidencial) and \
                not ((user.tipo_de_usuario == 2) or (user.tipo_de_usuario == 4)):
                return render(request, 'generic.html', context=context)

        if documento[:3] == "tmp":
            mensagem = "Documento não acessível"
            context = {"mensagem": mensagem,}
            return render(request, 'generic.html', context=context)

        with open(file_path, 'rb') as file:
            response = get_response(file, path, request)
            if not response:
                mensagem = "Erro ao carregar arquivo (formato não suportado)."
                context = {
                    "area_principal": True,
                    "mensagem": mensagem,
                }
                return render(request, 'generic.html', context=context)
            response['Content-Disposition'] = 'inline; filename=' +\
               os.path.basename(file_path)
            return response

    raise Http404


@login_required
def arquivos(request, documentos, path):
    """Permite acessar arquivos do servidor."""
    local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}".\
        format(documentos, path))
    return le_arquivo(request, local_path, path)


# @login_required
# Para pegar os relatórios publicos
def arquivos2(request, organizacao, usuario, path):
    """Permite acessar arquivos do servidor."""
    local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}/{2}".\
        format(organizacao, usuario, path))
    return le_arquivo(request, local_path, path)


# @login_required
# Para pegar certificados não pode ter o login required
def arquivos3(request, organizacao, projeto, usuario, path):
    """Permite acessar arquivos do servidor."""
    local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}/{2}/{3}".\
        format(organizacao, projeto, usuario, path))
    return le_arquivo(request, local_path, path)

