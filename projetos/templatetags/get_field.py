#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 30 de Novembro de 2023
"""

from django import template
register = template.Library()

@register.filter
def concat(val, arg):
    return f"{val}{arg}"

@register.simple_tag()
def max_length(instance, field):
    """ Retorna o valor do campo limitado ao tamanho máximo do campo """
    if instance is None or not hasattr(instance, field):
        return None
    length = instance._meta.get_field(field).max_length
    return length

@register.simple_tag()
def max_length_menos(instance, field, menos):
    """ Retorna o valor do campo limitado ao tamanho máximo do campo menos um valor"""
    if instance is None or not hasattr(instance, field):
        return None
    length = instance._meta.get_field(field).max_length - menos
    return length

@register.filter
def get_attr(instance, field):
    """ Retorna o campo """
    if instance is None or not hasattr(instance, field):
        return None
    return getattr(instance, field)

@register.simple_tag()
def slice_max_length(instance, field):
    """ Retorna o valor do campo limitado ao tamanho máximo do campo """
    text = getattr(instance, field)
    length = instance._meta.get_field(field).max_length
    return text[:length]

@register.simple_tag()
def slice_max_length_other(instance, field, other):
    """ Retorna o valor do campo limitado ao tamanho máximo de outro campo"""
    text = getattr(instance, field)
    length = instance._meta.get_field(other).max_length
    return text[:length]

@register.simple_tag()
def slice_other_max_length(text, instance, field):
    """ Retorna o valor do campo limitado ao tamanho máximo de outro campo"""
    length = instance._meta.get_field(field).max_length
    return text[:length]

@register.simple_tag()
def slice_other_max_length_upper(text, instance, field):
    """ Retorna o valor do campo limitado ao tamanho máximo de outro campo"""
    length = instance._meta.get_field(field).max_length
    return text[:length].upper()