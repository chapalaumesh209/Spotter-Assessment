import os
import sys
from pathlib import Path

# Add project directories to sys.path for serverless / Vercel execution
CURRENT_DIR = Path(__file__).resolve().parent
DJANGO_APP_DIR = CURRENT_DIR.parent
BACKEND_DIR = DJANGO_APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

for p in [DJANGO_APP_DIR, BACKEND_DIR, ROOT_DIR]:
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# Alias for Vercel / WSGI servers
app = application
