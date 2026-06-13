#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import uuid
import re
import os
import gzip

from xml.etree import ElementTree

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.template.defaultfilters import slugify
from django.utils import text
from django.utils.encoding import force_text


DOCUMENT_UPLOAD_ALLOWED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".zip",
    ".rar",
    ".7z",
    ".7zip",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".svgz",
    ".bmp",
    ".avif",
    ".webp",
    ".apng",
    ".tif",
    ".tiff",
    ".mp4",
    ".m4v",
    ".webm",
    ".mkv",
    ".mov",
    ".mpg",
    ".mpeg",
    ".ogv",
}

DOCUMENT_UPLOAD_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".svgz",
    ".bmp",
    ".avif",
    ".webp",
    ".apng",
    ".tif",
    ".tiff",
}

DOCUMENT_UPLOAD_VIDEO_EXTENSIONS = {
    ".mp4",
    ".m4v",
    ".webm",
    ".mkv",
    ".mov",
    ".mpg",
    ".mpeg",
    ".ogv",
}

DOCUMENT_UPLOAD_ALLOWED_MIME_TYPES = {
    "text/plain",
    "application/pdf",
    "application/zip",
    "application/x-zip",
    "application/x-zip-compressed",
    "application/x-rar-compressed",
    "application/vnd.rar",
    "application/x-7z-compressed",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "image/svg+xml",
}

DOCUMENT_UPLOAD_FALLBACK_MIME_TYPES = {
    "application/octet-stream",
    "binary/octet-stream",
}

DOCUMENT_UPLOAD_SVG_MIME_TYPES = {
    "image/svg+xml",
    "text/xml",
    "application/xml",
    "application/gzip",
    "application/x-gzip",
}

SVG_ALLOWED_TAGS = {
    "svg",
    "g",
    "defs",
    "title",
    "desc",
    "path",
    "rect",
    "circle",
    "ellipse",
    "line",
    "polyline",
    "polygon",
    "text",
    "tspan",
    "clipPath",
    "linearGradient",
    "radialGradient",
    "stop",
}

SVG_ALLOWED_ATTRIBUTES = {
    "xmlns",
    "viewBox",
    "width",
    "height",
    "x",
    "y",
    "x1",
    "x2",
    "y1",
    "y2",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "d",
    "points",
    "transform",
    "fill",
    "fill-opacity",
    "fill-rule",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-dasharray",
    "stroke-dashoffset",
    "stroke-opacity",
    "opacity",
    "font-family",
    "font-size",
    "font-weight",
    "text-anchor",
    "dominant-baseline",
    "preserveAspectRatio",
    "offset",
    "stop-color",
    "stop-opacity",
    "id",
    "clip-path",
}

SVG_URL_ATTRIBUTES = {
    "fill",
    "stroke",
    "clip-path",
}

SVG_ATTR_VALUE_BLOCKLIST = (
    "javascript:",
    "data:",
    "vbscript:",
    "<script",
    "</script",
)


def _strip_xml_namespace(tag_name):
    if "}" in tag_name:
        return tag_name.split("}", 1)[1]
    return tag_name


def _svg_attr_valido(attr_name, attr_value):
    nome = _strip_xml_namespace(attr_name)
    if nome.startswith("on"):
        return False
    if nome not in SVG_ALLOWED_ATTRIBUTES:
        return False

    valor = force_text(attr_value or "").strip()
    valor_normalizado = valor.lower().replace(" ", "")
    if any(item in valor_normalizado for item in SVG_ATTR_VALUE_BLOCKLIST):
        return False

    if nome in SVG_URL_ATTRIBUTES and valor.startswith("url("):
        return valor.startswith("url(#") and valor.endswith(")")

    return True


def _sanitize_svg_element(element):
    tag_name = _strip_xml_namespace(element.tag)
    if tag_name not in SVG_ALLOWED_TAGS:
        return None

    sanitized = ElementTree.Element(tag_name)
    for attr_name, attr_value in element.attrib.items():
        if _svg_attr_valido(attr_name, attr_value):
            sanitized.set(_strip_xml_namespace(attr_name), force_text(attr_value))

    if element.text:
        sanitized.text = force_text(element.text)
    if element.tail:
        sanitized.tail = force_text(element.tail)

    for child in list(element):
        sanitized_child = _sanitize_svg_element(child)
        if sanitized_child is not None:
            sanitized.append(sanitized_child)

    return sanitized


def sanitize_svg_upload(arquivo):
    """Sanitiza SVG/SVGZ com allowlist estrita antes de salvar."""
    nome_arquivo = force_text(getattr(arquivo, "name", "") or "").strip()
    extensao = os.path.splitext(nome_arquivo)[1].lower()

    conteudo_bruto = arquivo.read()
    arquivo.seek(0)

    try:
        if extensao == ".svgz":
            conteudo_svg = gzip.decompress(conteudo_bruto)
        else:
            conteudo_svg = conteudo_bruto

        raiz = ElementTree.fromstring(conteudo_svg)
    except (OSError, ElementTree.ParseError, ValueError):
        return None

    raiz_sanitizada = _sanitize_svg_element(raiz)
    if raiz_sanitizada is None or raiz_sanitizada.tag != "svg":
        return None

    raiz_sanitizada.set("xmlns", "http://www.w3.org/2000/svg")
    conteudo_sanitizado = ElementTree.tostring(raiz_sanitizada, encoding="utf-8", xml_declaration=True)

    if extensao == ".svgz":
        conteudo_sanitizado = gzip.compress(conteudo_sanitizado)

    return ContentFile(conteudo_sanitizado, name=nome_arquivo)


def documento_upload_permitido(arquivo):
    """Valida tipos permitidos para uploads de documentos."""
    nome_arquivo = force_text(getattr(arquivo, "name", "") or "").strip()
    extensao = os.path.splitext(nome_arquivo)[1].lower()

    if extensao not in DOCUMENT_UPLOAD_ALLOWED_EXTENSIONS:
        return False

    content_type = force_text(getattr(arquivo, "content_type", "") or "").split(";", 1)[0].strip().lower()
    if not content_type or content_type in DOCUMENT_UPLOAD_FALLBACK_MIME_TYPES:
        return True

    if extensao in DOCUMENT_UPLOAD_IMAGE_EXTENSIONS:
        if extensao in {".svg", ".svgz"}:
            return content_type in DOCUMENT_UPLOAD_SVG_MIME_TYPES
        return content_type.startswith("image/")

    if extensao in DOCUMENT_UPLOAD_VIDEO_EXTENSIONS:
        return content_type.startswith("video/")

    return content_type in DOCUMENT_UPLOAD_ALLOWED_MIME_TYPES


def get_upload_path(instance, filename):
    """Caminhos para armazenar os arquivos."""
    caminho = ""
    if instance.__class__.__name__ == "Documento":
        if instance.organizacao:
            caminho += slugify(instance.organizacao.sigla_limpa()) + "/"
        if instance.projeto:
            if (not instance.organizacao) and instance.projeto.organizacao:
                caminho += slugify(instance.projeto.organizacao.sigla_limpa()) + '/'
            caminho += "projeto" + str(instance.projeto.pk) + '/'
        if instance.usuario:
            caminho += slugify(instance.usuario.username) + '/'
        if caminho == "":
            caminho = "documentos/"
    elif instance.__class__.__name__ == "Projeto":
        caminho += slugify(instance.organizacao.sigla_limpa()) + '/'
        caminho += "projeto" + str(instance.pk) + '/'
    elif instance.__class__.__name__ == "Organizacao":
        caminho += slugify(instance.sigla_limpa()) + "/logotipo/"
    elif instance.__class__.__name__ == "Certificado":
        if instance.projeto and instance.projeto.organizacao:
            caminho += slugify(instance.projeto.organizacao.sigla_limpa()) + '/'
            caminho += "projeto" + str(instance.projeto.pk) + '/'
        if instance.usuario:
            caminho += slugify(instance.usuario.username) + '/'
    elif instance.__class__.__name__ == "Configuracao" or instance.__class__.__name__ == "Administrador":
        caminho += "configuracao/"
    elif instance.__class__.__name__ == "Proposta":
        caminho += "propostas/proposta"+ str(instance.pk) + '/'
    else:  # Arquivo Temporário
        caminho += "tmp/"

    if filename:
        filename = force_text(filename).strip().replace(' ', '_')
        filename = re.sub(r'(?u)[^-\w.]', '', filename)
        return "{0}/{1}".format(caminho, filename)

    return "{0}".format(caminho)


def simple_upload(arquivo, path="", prefix="", valida=None):
    """Faz uploads para o servidor."""
    if valida:
        if valida == "pdf":
            if arquivo.content_type != "application/pdf":
                return None  # Não é PDF
        elif valida == "documento":
            if not documento_upload_permitido(arquivo):
                return None
            extensao = os.path.splitext(force_text(getattr(arquivo, "name", "") or ""))[1].lower()
            if extensao in {".svg", ".svgz"}:
                arquivo = sanitize_svg_upload(arquivo)
                if arquivo is None:
                    return None
    file_system_storage = FileSystemStorage()
    filename = str(arquivo.name.encode("utf-8").decode("ascii", "ignore"))
    while ".." in filename:  # Remove .. do nome do arquivo
        filename = filename.replace("..", ".")
    filename = filename.strip()

    sanitized_filename = text.get_valid_filename(filename)
    
    ext = os.path.splitext(filename)[1]
    if not sanitized_filename or sanitized_filename in {".", ".."}:
        sanitized_filename = f"{uuid.uuid4().hex}{ext or '.file'}"
    
    name = os.path.join(path, prefix + sanitized_filename)
    filename = file_system_storage.save(name, arquivo)
    uploaded_file_url = file_system_storage.url(filename)
    return uploaded_file_url

