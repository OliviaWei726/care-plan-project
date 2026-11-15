"""
Celery 异步任务：生成 Care Plan。

流程：
    web (views.submit_order)          Redis (broker)            worker (这个文件)
    CarePlan(status=pending) ──.delay()──> list "celery" ──取出──> 调 LLM → 存库 → completed

完成后只写数据库，不通知前端（没有 polling / SSE / WebSocket）：
不刷新 /orders/ 页面就看不到 care plan 已经完成。
"""

import logging
import time

import anthropic
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import CarePlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a clinical pharmacist writing a pharmacist care plan for a specialty "
    "pharmacy order. Use these sections: Problem List, Goals, Pharmacist Interventions, "
    "Monitoring Plan. Base everything only on the information provided; if something "
    "important is missing, say so instead of inventing it."
)

# 只有"临时性"的错误才值得重试：等一会儿再试，有可能就成功了。
# 对照 anthropic SDK 2.8 源码（_error_classes.py / _exceptions.py）：
#   RateLimitError      ← 429 限流
#   InternalServerError ← 所有 >=500（529 OverloadedError、503 等都是它的子类）
#   APIConnectionError  ← 网络断开 / DNS 失败等，没收到 HTTP 响应
#   APITimeoutError     ← 超时（其实是 APIConnectionError 的子类，单独列出来是为了可读性）
# 不在这里的错误（400 余额不足/参数错误、401 key 无效、403、404 模型名不对……）
# 重试多少次结果都一样，所以直接标记 failed，不浪费 7 分钟。
RETRYABLE_EXCEPTIONS = (
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
)


@shared_task(
    bind=True,  # 让函数第一个参数 self 是 task 本身，才能读 self.request.retries
    # 只对临时性错误自动重试，其他异常直接让任务失败（见上面 RETRYABLE_EXCEPTIONS）
    autoretry_for=RETRYABLE_EXCEPTIONS,
    # 第 n 次重试前等待 min(retry_backoff_max, retry_backoff * 2**n) 秒
    # （公式见 celery/utils/time.py: get_exponential_backoff_interval）。
    # 默认 60 → 60s, 120s, 240s。测试时在 .env 里设 CARE_PLAN_RETRY_BACKOFF=5 → 5s, 10s, 20s。
    retry_backoff=settings.CARE_PLAN_RETRY_BACKOFF,
    retry_backoff_max=600,
    # Celery 默认 retry_jitter=True：实际等待时间在 [0, 上面的值] 里随机取，
    # 用来避免大量任务同一时刻一起重试、把 LLM API 打爆。
    # 学习阶段关掉，日志里的 "Retry in 5s / 10s / 20s" 才是确定的，方便观察。
    retry_jitter=False,
    # 首次执行 + 最多 3 次重试 = 最多一共 4 次尝试
    max_retries=3,
)
def generate_care_plan(self, careplan_id: int):
    attempt = self.request.retries + 1          # 第几次尝试（request.retries 第一次是 0）
    total_attempts = self.max_retries + 1
    logger.info("[worker] careplan_id=%s 开始处理（第 %d/%d 次尝试）",
                careplan_id, attempt, total_attempts)

    try:
        care_plan = CarePlan.objects.select_related(
            "order__patient", "order__provider"
        ).get(pk=careplan_id)
    except CarePlan.DoesNotExist:
        # 排队期间记录被删掉了：重试也没用，直接结束（不抛异常 → 不触发重试）
        logger.warning("[worker] careplan_id=%s 不存在，跳过", careplan_id)
        return

    # 同一个任务可能被执行两次（比如上一次已经存好了，但 worker 在确认消息前挂了），
    # 已经完成的就不再花钱调一次 LLM
    if care_plan.status == CarePlan.STATUS_COMPLETED:
        logger.info("[worker] careplan_id=%s 已经完成过，跳过", careplan_id)
        return

    try:
        content = _call_llm(_build_prompt(care_plan.order))
    except Exception as e:
        # 两个条件都满足才会重试：是临时性错误，并且还有重试次数
        retryable = isinstance(e, RETRYABLE_EXCEPTIONS)
        will_retry = retryable and self.request.retries < self.max_retries
        if will_retry:
            # 还会重试：任务其实又回到队列里等下一次执行了，所以状态保持 pending，
            # 不能标成 failed（否则用户刷新时会看到 failed，过一会又变成 completed）
            logger.warning("[worker] careplan_id=%s 第 %d/%d 次失败，将重试：%r",
                           careplan_id, attempt, total_attempts, e)
        else:
            care_plan.status = CarePlan.STATUS_FAILED
            care_plan.save(update_fields=["status"])
            if retryable:
                logger.error("[worker] careplan_id=%s 全部 %d 次尝试都失败，标记 failed：%r",
                             careplan_id, total_attempts, e)
            else:
                logger.error("[worker] careplan_id=%s 遇到不可重试的错误，直接标记 failed：%r",
                             careplan_id, e)
        # 重新抛出：如果是临时性错误，autoretry_for 会接住它并安排下一次重试；
        # 其他错误（或者没有重试次数了），Celery 就把这个任务标成 FAILURE
        raise

    care_plan.content = content
    care_plan.status = CarePlan.STATUS_COMPLETED
    care_plan.generated_at = timezone.now()
    care_plan.save(update_fields=["content", "status", "generated_at"])

    # 到这里就结束了：没有通知前端
    logger.info("[worker] careplan_id=%s 已完成并存入 DB（%d 字）", careplan_id, len(content))
    return {"careplan_id": careplan_id, "status": "completed"}


def _build_prompt(order) -> str:
    patient = order.patient
    return f"""Patient: {patient.first_name} {patient.last_name} (MRN {patient.mrn}), DOB {patient.date_of_birth or "unknown"}
Referring provider: {order.provider.name} (NPI {order.provider.npi})
Medication ordered: {order.medication_name}
Primary diagnosis (ICD-10): {order.primary_diagnosis}
Additional diagnoses (ICD-10):
{order.additional_diagnoses or "None"}
Medication history:
{order.medication_history or "None"}
Clinical notes:
{order.patient_records or "None"}

Write the pharmacist care plan."""


MOCK_CARE_PLAN = """[MOCK] 这是 LLM_MOCK=1 时生成的假 care plan，没有调用真实的 API。

## Problem List
- (mock) Problem 1

## Goals
- (mock) Goal 1

## Pharmacist Interventions
- (mock) Intervention 1

## Monitoring Plan
- (mock) Monitor 1
"""


def _call_llm(prompt: str) -> str:
    if settings.LLM_MOCK:
        # 假 LLM：不花钱，但用 sleep 模拟"真实调用要等很久"。
        # 异步流程（入队 → worker 处理 → 写 DB → 必须刷新才能看到）和真实调用完全一样。
        time.sleep(settings.LLM_MOCK_DELAY)
        return MOCK_CARE_PLAN

    # 同步阻塞调用，可能要几十秒：这正是它必须放在 worker 里、不能放在 HTTP 请求里的原因
    client = anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        # SDK 默认会对 429/5xx/网络错误自己静默重试 2 次，会和 Celery 的重试叠在一起
        # （最坏情况 4 × 3 = 12 次请求），日志里也看不到。关掉它，让 Celery 成为唯一的重试层，
        # 每一次重试都会在 worker 日志里显示出来。
        max_retries=0,
    )
    message = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    # 只取文本块（返回里也可能有别的类型的 block）
    return "".join(block.text for block in message.content if block.type == "text")
