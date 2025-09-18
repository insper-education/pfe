#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 3 de Maio de 2024
"""

from django import template
import hashlib

register = template.Library()

@register.filter
def clarear(value):
    # Recebe um valor hexadecimal e retorna um valor hexadecimal mais claro
    nova_cor = ""
    if value[0] == "#":
        value = value[1:]
        nova_cor = "#"
    r = int(value[:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:], 16)
    brilho = 64
    r = min(255, r + brilho)
    g = min(255, g + brilho)
    b = min(255, b + brilho)
    nova_cor += "{:02X}{:02X}{:02X}".format(r, g, b)
    return nova_cor

@register.filter
def hash_color(value):
    """Generate a consistent color based on a value (like student ID)"""
    # Convert the value to a string and encode
    value_str = str(value)
    hash_obj = hashlib.md5(value_str.encode())
    
    # Get the hexadecimal digest and take first 6 characters for RGB
    hex_digest = hash_obj.hexdigest()
    
    # Make sure color is not too light by adjusting brightness
    r = int(hex_digest[0:2], 16) % 180  # Keep under 180 to avoid light colors
    g = int(hex_digest[2:4], 16) % 180
    b = int(hex_digest[4:6], 16) % 180
    
    # Return the color in hexadecimal format
    return f'#{r:02x}{g:02x}{b:02x}'