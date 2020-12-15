
# Fonte: https://gist.github.com/martinsvoboda/1bf965a8c6037c0fe1a88d89ea822df6

import re

from django.utils.encoding import force_text
from django.template import Library, Node


register = Library()


def strip_spaces_in_tags(value):
    value = force_text(value)
    value = re.sub(r'\s+', ' ', value)
    value = re.sub(r'>\s+', '>', value)
    value = re.sub(r'\s+<', '<', value)
    return value


class NoSpacesNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return strip_spaces_in_tags(self.nodelist.render(context).strip())


@register.tag
def nospaces(parser, token):
    """
    Removes any duplicite whitespace in tags and text. Can be used as supplementary tag for {% spaceless %}::
        {% nospaces %}
        <strong>
            Hello
            this is text
        </strong>
        {% nospaces %}
    Returns::
        <strong>Hello this is text</strong>
    """
    nodelist = parser.parse(('endnospaces',))
    parser.delete_first_token()
    return NoSpacesNode(nodelist)