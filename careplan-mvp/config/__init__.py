# Django 启动时就加载 Celery app。
# 这样 web 进程里调用 generate_care_plan.delay() 时，task 已经绑定到这个 app，
# 知道该把消息发到哪个 broker（Redis）。
from .celery import app as celery_app

__all__ = ("celery_app",)
