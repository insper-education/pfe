
import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()



### NÃO SEI SE É UMA BOA IDEIA USAR ISSO, VAI DEIXAR MAIS PESADA TODAS AS CHAMADAS
@register.simple_tag
def static_mtime(path):
    """Return static URL with mtime querystring for automatic cache busting in dev."""
    url = static(path)
    static_path = finders.find(path)
    if not static_path:
        return url

    try:
        mtime = int(os.path.getmtime(static_path))
    except OSError:
        return url

    sep = "&" if "?" in url else "?"
    return f"{url}{sep}v={mtime}"
