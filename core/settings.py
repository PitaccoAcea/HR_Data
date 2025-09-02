"""
Django settings for core project.

Generato con Django 5.2.x.
Questo settings.py è pensato per due ambienti:
- sviluppo/test: .env.dev
- produzione:    .env.prod

Regola di caricamento .env (in ordine di priorità):
1) Se esiste BASE_DIR/.env.prod  -> carica quello (produzione "auto")
2) Altrimenti se DJANGO_ENV=prod -> carica .env.prod
   Altrimenti                     -> carica .env.dev
"""

from pathlib import Path
import os
from dotenv import load_dotenv



# === Path base del progetto ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === Caricamento .env in modo robusto ===
# Commento:
# - In IIS non esegui comandi shell, quindi preferiamo che la sola presenza di .env.prod
#   faccia "auto-switch" alla produzione.
# - In console puoi sempre forzare con: $env:DJANGO_ENV="prod"
env_from_var = os.environ.get("DJANGO_ENV", "").lower()
prod_env_path = BASE_DIR / ".env.prod"
dev_env_path = BASE_DIR / ".env.dev"

if prod_env_path.exists():
    # Produzione "auto" se troviamo il file .env.prod nella cartella del sito
    load_dotenv(dotenv_path=prod_env_path, override=False)
elif env_from_var == "prod":
    load_dotenv(dotenv_path=prod_env_path, override=False)
else:
    load_dotenv(dotenv_path=dev_env_path, override=False)

# === Impostazioni base ===

# SECURITY WARNING: non lasciare la secret key hardcodata in produzione.
# Leggila dal .env; se assente, usa il fallback (ok solo in dev).
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-9#!l2@tlc1wg%=hiu+^pjc*j47wvqg9!(ib+v+*c&*whk)3s=5"
)

# DEBUG: True in dev, False in prod (controllato da .env)
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

# ALLOWED_HOSTS: lista separata da virgole nel .env
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

# (Opzionale) CSRF_TRUSTED_ORIGINS: utile quando abiliterai HTTPS/host intranet
# Esempio in .env: CSRF_TRUSTED_ORIGINS=https://hr-data.intra.local,http://10.0.0.25
_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]

# === App e Middleware ===

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main",  # app minimale per la home
    "accounts",  # app per la gestione utenti + LDAP
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # 👇 Ordine corretto: prima AuthenticationMiddleware...
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # ...per utente fittizio in dev
    'core.middleware.fake_remote_user.FakeRemoteUserMiddleware',

    # ...poi RemoteUserMiddleware
    'django.contrib.auth.middleware.RemoteUserMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]


ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates",],  # aggiungerai qui eventuali cartelle di template personalizzate
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# === Database: mssql-django + pyodbc ===
# Tutto dal .env per evitare hardcode
DB_NAME    = os.environ.get("HRDATA_DB_NAME", "HR_Data_DB_Test")
DB_HOST    = os.environ.get("HRDATA_DB_HOST", "localhost")
DB_PORT    = os.environ.get("HRDATA_DB_PORT", "")  # "" = default 1433
DB_USER    = os.environ.get("HRDATA_DB_USER", "")
DB_PWD     = os.environ.get("HRDATA_DB_PWD", "")
DB_DRIVER  = os.environ.get("HRDATA_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
DB_TRUSTED = os.environ.get("HRDATA_TRUSTED", "no").lower()  # "yes" / "no"

DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": DB_NAME,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            "driver": DB_DRIVER,
            # Con SQL Login useremo USER/PASSWORD sotto;
            # con Windows Auth useremo trusted_connection="yes".
        },
    }
}

if DB_TRUSTED == "yes":
    # Autenticazione integrata Windows
    DATABASES["default"]["OPTIONS"]["trusted_connection"] = "yes"
else:
    # SQL Login
    DATABASES["default"]["USER"] = DB_USER
    DATABASES["default"]["PASSWORD"] = DB_PWD

# === Localizzazione ===
LANGUAGE_CODE = "it-it"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True

# === Statici: WhiteNoise ===
# In produzione: esegui "python manage.py collectstatic --noinput"
STATIC_URL = os.environ.get("STATIC_URL", "static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Solo in sviluppo: dove Django va a cercare i file statici prima di copiarli in staticfiles/
if os.environ.get("DJANGO_ENV", "dev") == "dev":
    STATICFILES_DIRS = [
        BASE_DIR / "main" / "static",
    ]

# === Campo ID di default per i modelli ===
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Directory aggiuntiva per i template di progetto (oltre a quelli delle app)
TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]

# Statici: oltre a STATIC_ROOT (per collectstatic) dichiariamo la sorgente locale
STATIC_URL = os.environ.get("STATIC_URL", "static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]  # <--- cartella sorgente per CSS/JS/immagini di progetto
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.RemoteUserBackend',
]