import json
import logging
import redis
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .models import Patient, Provider, Order, CarePlan

logger = logging.getLogger(__name__)

# Redis 连接（模块级别，复用同一个连接）
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
)

QUEUE_NAME = "careplan_queue"


# ─────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def order_form(request):
    return render(request, "form.html")


@require_http_methods(["POST"])
def submit_order(request):
    logger.info("=" * 50)
    logger.info("[1] POST /submit/ — 收到请求，来自 IP: %s", request.META.get("REMOTE_ADDR"))

    def lines(field):
        raw = request.POST.get(field, "")
        return "\n".join(l.strip() for l in raw.splitlines() if l.strip())

    # Provider — get or create by NPI
    npi           = request.POST.get("referring_provider_npi", "").strip()
    provider_name = request.POST.get("referring_provider", "").strip()
    provider, _   = Provider.objects.get_or_create(npi=npi, defaults={"name": provider_name})

    # Patient — get or create by MRN
    mrn        = request.POST.get("patient_mrn", "").strip()
    patient, _ = Patient.objects.get_or_create(mrn=mrn, defaults={
        "first_name": request.POST.get("patient_first_name", "").strip(),
        "last_name":  request.POST.get("patient_last_name", "").strip(),
    })

    # Order
    order = Order.objects.create(
        patient=patient,
        provider=provider,
        medication_name=request.POST.get("medication_name", "").strip(),
        primary_diagnosis=request.POST.get("primary_diagnosis", "").strip(),
        additional_diagnoses=lines("additional_diagnoses"),
        medication_history=lines("medication_history"),
        patient_records=request.POST.get("patient_records", "").strip(),
    )
    logger.info("[2] Order #%d 已存入 DB", order.pk)

    # CarePlan 先存 pending，内容为空
    care_plan = CarePlan.objects.create(order=order, status=CarePlan.STATUS_PENDING)
    logger.info("[3] CarePlan #%d 已存入 DB，status=pending", care_plan.pk)

    # 把 careplan_id 推进 Redis 队列
    task = {"careplan_id": care_plan.pk}
    redis_client.rpush(QUEUE_NAME, json.dumps(task))
    logger.info("[4] careplan_id=%d 已推入 Redis 队列 '%s'", care_plan.pk, QUEUE_NAME)
    logger.info("=" * 50)

    # 立刻返回，不等 LLM
    return JsonResponse({
        "status":      "accepted",
        "careplan_id": care_plan.pk,
        "message":     "订单已收到，care plan 正在后台生成",
    }, status=202)


@require_http_methods(["GET"])
def order_list(request):
    orders = Order.objects.select_related("patient", "provider").order_by("-created_at")
    return render(request, "orders.html", {"orders": orders})
