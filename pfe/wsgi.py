import os
import sys
import django

# O diretório pai de onde reside o wsgi.py
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if path not in sys.path:
  sys.path.append(path)

os.chdir(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'pfe.settings'

django.setup()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
