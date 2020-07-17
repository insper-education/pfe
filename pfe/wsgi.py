"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import os
import sys
import django
from django.core.wsgi import get_wsgi_application

# O diretório pai de onde reside o wsgi.py
PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if PATH not in sys.path:
    sys.path.append(PATH)

os.chdir(PATH)

os.environ['DJANGO_SETTINGS_MODULE'] = 'pfe.settings'

django.setup()

application = get_wsgi_application()
