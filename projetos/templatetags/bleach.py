#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 31 de Outubro de 2024
"""

import bleach
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = ["a", "br", "p"]
ALLOWED_ATTRS = {"a": ["href", "rel", "target", "title"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]
DISALLOWED_BLOCK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)


def _set_link_attributes(attrs, new=False):
    rel_values = set(attrs.get((None, "rel"), "").split())
    rel_values.update(["nofollow", "noopener", "noreferrer"])
    attrs[(None, "rel")] = " ".join(sorted(rel_values))
    href = attrs.get((None, "href"), "")
    if href.startswith(("http://", "https://")):
        attrs[(None, "target")] = "_blank"
    return attrs

@register.filter(name='bleach_urlize')
def bleach_urlize(value):
    if not value:
        return ""

    text = DISALLOWED_BLOCK_RE.sub("", str(value))
    sanitized = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    linkified = bleach.linkify(
        sanitized,
        parse_email=True,
        callbacks=[_set_link_attributes],
    )

    return mark_safe(linkified)

