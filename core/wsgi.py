"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from waitress import serve
from dj_static import Cling
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# application = get_wsgi_application()

application = Cling(get_wsgi_application())
serve(application, host='0.0.0.0', port=8081)
#waitress-serve core.wsgi:application