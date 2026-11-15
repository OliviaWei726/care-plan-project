"""
Celery app。

worker 启动命令：celery -A config worker -l info
  -A config → 去 config 包里找这个 `app` 对象
"""

import os

from celery import Celery

# worker 是一个独立进程，不经过 manage.py，所以要自己告诉它用哪个 settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("careplan")

# 从 Django settings 里读所有以 CELERY_ 开头的配置（比如 CELERY_BROKER_URL）
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动去每个 INSTALLED_APPS 里找 tasks.py，注册里面的 @shared_task
app.autodiscover_tasks()
