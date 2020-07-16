import os
import django
#import sys

#path='/home/ubuntu/pfe'
#path='/Users/lpsoares/pfe'

#if path not in sys.path:
#  sys.path.append(path)

#os.chdir(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'pfe.settings'

django.setup()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

#import django.core.handlers.wsgi
#application = django.core.handlers.wsgi.WSGIHandler()
