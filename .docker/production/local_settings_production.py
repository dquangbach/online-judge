import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Security & Debug ───────────────────────────────────────────────────────────
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
if SECRET_KEY.startswith("change-me") or len(SECRET_KEY) < 50:
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be a generated secret of at least 50 characters"
    )
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")
if DEBUG:
    raise RuntimeError("DJANGO_DEBUG must be False in the production image")

allowed_hosts_env = os.environ["DJANGO_ALLOWED_HOSTS"]
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(",") if h.strip()]
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS must list explicit production hosts")

# ── Database ───────────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DATABASE", "dmoj"),
        "USER": os.environ.get("MYSQL_USER", "root"),
        "PASSWORD": os.environ["MYSQL_PASSWORD"],
        "HOST": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.environ.get("MYSQL_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "sql_mode": "STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION",
        },
    }
}
if DATABASES["default"]["PASSWORD"].startswith("change-me"):
    raise RuntimeError("MYSQL_PASSWORD must be replaced in .env.production")

# ── Caching (Memcached in production, LocMem for dev fallback) ────────────────
memcached_host = os.environ.get("MEMCACHED_HOST")
if memcached_host:
    memcached_port = os.environ.get("MEMCACHED_PORT", "11211")
    CACHES = {
        "default": {
            "BACKEND": "judge.cache_handler.CacheHandler",
        },
        "primary": {
            "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
            "LOCATION": f"{memcached_host}:{memcached_port}",
        },
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    }

# ── Celery & Redis ────────────────────────────────────────────────────────────
CELERY_BROKER_URL_SECRET = os.environ.get(
    "CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"
)
CELERY_RESULT_BACKEND_SECRET = os.environ.get(
    "CELERY_RESULT_BACKEND", CELERY_BROKER_URL_SECRET
)

# ── Static / Media / Problems ─────────────────────────────────────────────────
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/static")
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/media")
DMOJ_PROBLEM_DATA_ROOT = os.environ.get("DMOJ_PROBLEM_DATA_ROOT", "/problems")

try:
    os.makedirs(STATIC_ROOT, exist_ok=True)
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    os.makedirs(DMOJ_PROBLEM_DATA_ROOT, exist_ok=True)
except OSError:
    pass

# ── Site Information ──────────────────────────────────────────────────────────
SITE_NAME = os.environ.get("SITE_NAME", "DUTOJ")
SITE_LONG_NAME = os.environ.get("SITE_LONG_NAME", "DUT Online Judge")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "localhost")
DMOJ_REQUIRE_STAFF_2FA = os.environ.get("DMOJ_REQUIRE_STAFF_2FA", "False").lower() in (
    "true",
    "1",
    "yes",
)
NODEJS = os.environ.get("NODEJS_PATH", "/usr/bin/node")

# ── Chat & Event Daemons ──────────────────────────────────────────────────────
CHAT_SECRET_KEY = os.environ["CHAT_SECRET_KEY"]
for secret_name, secret_value in (
    ("CHAT_SECRET_KEY", CHAT_SECRET_KEY),
    ("EVENT_DAEMON_KEY", os.environ["EVENT_DAEMON_KEY"]),
    ("EVENT_DAEMON_SUBMISSION_KEY", os.environ["EVENT_DAEMON_SUBMISSION_KEY"]),
):
    if secret_value.startswith("change-me") or len(secret_value) < 32:
        raise RuntimeError(f"{secret_name} must be replaced with a strong secret")
EVENT_DAEMON_KEY = os.environ["EVENT_DAEMON_KEY"]
EVENT_DAEMON_SUBMISSION_KEY = os.environ["EVENT_DAEMON_SUBMISSION_KEY"]
EVENT_DAEMON_URL = os.environ["EVENT_DAEMON_URL"]
EVENT_DAEMON_PUBLIC_URL = os.environ["EVENT_DAEMON_PUBLIC_URL"]

# ── Bridge (Judge ↔ Django) ───────────────────────────────────────────────────
bridge_judge_port = int(os.environ.get("BRIDGED_JUDGE_PORT", "9999"))
bridge_django_port = int(os.environ.get("BRIDGED_DJANGO_PORT", "9998"))
BRIDGED_JUDGE_ADDRESS = [("0.0.0.0", bridge_judge_port)]
BRIDGED_DJANGO_ADDRESS = [("0.0.0.0", bridge_django_port)]

bridge_connect_host = os.environ["BRIDGED_CONNECT_HOST"]
bridge_connect_port = int(os.environ.get("BRIDGED_CONNECT_PORT", "9998"))
BRIDGED_DJANGO_CONNECT = (bridge_connect_host, bridge_connect_port)

# Push problem data updates to judges via bridge when bridge is active
DMOJ_PROBLEM_DATA_PUSH_UPDATE = bool(bridge_connect_host)

# ── SSL & Production Hardening ────────────────────────────────────────────────
if not DEBUG and os.environ.get("DMOJ_SSL", "0") in ("1", "2"):
    DMOJ_SSL = int(os.environ.get("DMOJ_SSL", "1"))
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
