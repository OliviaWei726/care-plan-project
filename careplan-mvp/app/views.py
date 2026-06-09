import uuid
import anthropic
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

# ─────────────────────────────────────────────
# In-memory store  (lost on restart — MVP only)
# ─────────────────────────────────────────────
ORDERS = {}   # order_id -> dict


# ─────────────────────────────────────────────
# LLM
# ─────────────────────────────────────────────
def generate_care_plan(order: dict) -> str:
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    additional_dx = ", ".join(order["additional_diagnoses"]) or "None"
    med_history   = "\n".join(f"  - {m}" for m in order["medication_history"]) or "  None provided"

    prompt = f"""You are a clinical pharmacist at a specialty pharmacy.
Generate a care plan for the following patient and medication order.

--- PATIENT & ORDER ---
Patient: {order["patient_first_name"]} {order["patient_last_name"]}
MRN: {order["patient_mrn"]}
Primary Diagnosis (ICD-10): {order["primary_diagnosis"]}
Additional Diagnoses: {additional_dx}
Medication: {order["medication_name"]}
Referring Provider: {order["referring_provider"]} (NPI: {order["referring_provider_npi"]})

Medication History:
{med_history}

Patient Records / Clinical Notes:
{order["patient_records"]}

--- INSTRUCTIONS ---
Write a care plan with exactly these four sections, in order:

1. Problem List / Drug Therapy Problems (DTPs)
   List each problem as a bullet point.

2. Goals (SMART)
   Include: primary outcome goal, safety goal, process goal.

3. Pharmacist Interventions / Plan
   Cover: dosing & administration, premedication, monitoring during therapy,
   hydration/organ protection as relevant, adverse event management.

4. Monitoring Plan & Lab Schedule
   Specify: pre-treatment labs/vitals, monitoring during treatment, post-treatment follow-up.

Be specific to this patient's diagnosis and medication. Use clinical language appropriate
for a pharmacist audience. Do not add any section beyond the four above.
"""

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ─────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def order_form(request):
    return render(request, "form.html")


@require_http_methods(["POST"])
def submit_order(request):
    # Parse form — split textarea lines into lists
    def lines(field):
        raw = request.POST.get(field, "")
        return [l.strip() for l in raw.splitlines() if l.strip()]

    order = {
        "id":                    str(uuid.uuid4())[:8],
        "patient_first_name":    request.POST.get("patient_first_name", "").strip(),
        "patient_last_name":     request.POST.get("patient_last_name", "").strip(),
        "patient_mrn":           request.POST.get("patient_mrn", "").strip(),
        "referring_provider":    request.POST.get("referring_provider", "").strip(),
        "referring_provider_npi":request.POST.get("referring_provider_npi", "").strip(),
        "primary_diagnosis":     request.POST.get("primary_diagnosis", "").strip(),
        "medication_name":       request.POST.get("medication_name", "").strip(),
        "additional_diagnoses":  lines("additional_diagnoses"),
        "medication_history":    lines("medication_history"),
        "patient_records":       request.POST.get("patient_records", "").strip(),
        "care_plan":             None,
    }

    # Call LLM synchronously — user waits
    order["care_plan"] = generate_care_plan(order)

    ORDERS[order["id"]] = order

    return render(request, "result.html", {"order": order})


@require_http_methods(["GET"])
def order_list(request):
    return render(request, "orders.html", {"orders": list(ORDERS.values())})
