#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

from projetos.models import Area, AreaDeInteresse


def cria_area_estudante(request, estudante):
    """Cria um objeto Areas e preenche ele."""
    check_values = request.POST.getlist('selection')

    todas_areas = Area.objects.filter(ativa=True)
    for area in todas_areas:
        if area.titulo in check_values:
            if not AreaDeInteresse.objects.filter(area=area, usuario=estudante.user).exists():
                AreaDeInteresse.create_estudante_area(estudante, area).save()
        else:
            if AreaDeInteresse.objects.filter(area=area, usuario=estudante.user).exists():
                AreaDeInteresse.objects.get(area=area, usuario=estudante.user).delete()

    outras = request.POST.get("outras", "").strip()
    if outras != "":
        (outra, _created) = AreaDeInteresse.objects.get_or_create(area=None, usuario=estudante.user)
        outra.ativa = True
        outra.outras = request.POST.get("outras", "")
        outra.save()
    else:
        if AreaDeInteresse.objects.filter(area=None, usuario=estudante.user).exists():
            AreaDeInteresse.objects.get(area=None, usuario=estudante.user).delete()
