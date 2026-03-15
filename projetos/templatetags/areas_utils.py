from django import template

register = template.Library()


@register.filter
def selected_area_ids(areas_de_interesse_selecionadas):
    """Retorna lista deduplicada de IDs de áreas selecionadas."""
    if not areas_de_interesse_selecionadas:
        return []

    ids = []
    vistos = set()

    for item in areas_de_interesse_selecionadas:
        area_id = None
        area = getattr(item, "area", None)
        if area is not None:
            area_id = getattr(area, "id", None)
        elif hasattr(item, "id"):
            area_id = item.id

        if area_id and area_id not in vistos:
            vistos.add(area_id)
            ids.append(area_id)

    return ids


def _find_area_interesse(areas_de_interesse_selecionadas, area_id):
    if not areas_de_interesse_selecionadas:
        return None

    try:
        area_id = int(area_id)
    except (TypeError, ValueError):
        return None

    for item in areas_de_interesse_selecionadas:
        area = getattr(item, "area", None)
        if area is not None and getattr(area, "id", None) == area_id:
            return item
    return None


@register.filter
def area_selected(areas_de_interesse_selecionadas, area_id):
    """Indica se uma área foi selecionada pelo usuário."""
    return _find_area_interesse(areas_de_interesse_selecionadas, area_id) is not None


@register.filter
def area_nivel_interesse(areas_de_interesse_selecionadas, area_id):
    """Retorna texto do nível de interesse da área selecionada, se houver."""
    item = _find_area_interesse(areas_de_interesse_selecionadas, area_id)
    if not item:
        return ""

    nivel = getattr(item, "nivel_interesse", None)
    if nivel is None:
        return ""

    get_display = getattr(item, "get_nivel_interesse_display", None)
    if callable(get_display):
        return get_display()
    return str(nivel)


@register.filter
def dict_get(mapping, key):
    """Retorna item de dict por chave, com fallback para None."""
    if mapping is None:
        return None
    try:
        return mapping.get(key)
    except AttributeError:
        return None
