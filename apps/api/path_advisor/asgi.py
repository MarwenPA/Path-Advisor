"""ASGI entrypoint."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "path_advisor.settings.local")

application = get_asgi_application()
