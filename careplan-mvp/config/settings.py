import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "mvp-secret-key-change-in-production"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.auth",
    "app",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     os.environ.get("DB_NAME",     "careplan"),
        "USER":     os.environ.get("DB_USER",     "careplan"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "careplan"),
        "HOST":     os.environ.get("DB_HOST",     "db"),
        "PORT":     os.environ.get("DB_PORT",     "5432"),
    }
}

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,   # auto-finds app/templates/
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

STATIC_URL = "/static/"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

LLM_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-5-5")

# LLM_MOCK=1：worker 不调用真实 API，sleep 几秒后返回一段假的 care plan（不花钱，用来练异步流程）
LLM_MOCK = os.environ.get("LLM_MOCK", "") == "1"
LLM_MOCK_DELAY = int(os.environ.get("LLM_MOCK_DELAY", 10))  # 假装 LLM 要算多少秒

# ── Celery ──
# broker = 存放"待执行任务"的地方。直接复用已有的 Redis：
# .delay() 会把任务 LPUSH 到 Redis 里一个叫 "celery" 的 list，worker 从那里取。
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
# 不配置 result backend：任务结果（成功/失败）已经写在 CarePlan.status 里了，不需要 Celery 再存一份

# 指数退避的基数（秒）：第 n 次重试前等 base * 2**n 秒。测试重试时可以设小一点，比如 5
CARE_PLAN_RETRY_BACKOFF = int(os.environ.get("CARE_PLAN_RETRY_BACKOFF", 60))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{asctime} {levelname} {name} — {message}",
            "style": "{",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
