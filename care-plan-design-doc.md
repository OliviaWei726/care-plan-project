# Care Plan Generation Tool — Design Document

**Client:** CVS Specialty Pharmacy  
**Users:** CVS medical staff (pharmacists and medical assistants)  
**Last Updated:** 2026-06-02

---

## 1. Background & Problem Statement

Pharmacists currently spend 20–40 minutes manually generating care plans per patient. These plans are required for:

- Regulatory compliance
- Medicare reimbursement
- Pharma reporting

The team is severely short-staffed and backlogged. This tool eliminates manual care plan drafting by having a medical assistant input patient/order data into a validated web form, then auto-generating the care plan via LLM.

Patients do not interact with this system. The generated care plan is printed and handed to the patient by staff.

---

## 2. Scope

One care plan = one order = one medication.

### In Scope

- Web form for data entry with full validation
- Duplicate detection (patient and order)
- Provider deduplication
- LLM-generated care plan (downloadable as text file)
- Pharma reporting export

### Out of Scope

- Patient-facing portal
- EHR/EMR direct integration (v1)
- Multi-medication care plans

---

## 3. Inputs

The web form must accept the following fields:

| Field | Type | Validation |
|---|---|---|
| Patient First Name | String | Required, non-empty |
| Patient Last Name | String | Required, non-empty |
| Patient MRN | 6-digit unique ID | Required, exactly 6 digits, unique |
| Patient Date of Birth | Date | Required (used for duplicate detection) |
| Referring Provider | String | Required |
| Referring Provider NPI | 10-digit number | Required, exactly 10 digits |
| Primary Diagnosis | ICD-10 code | Required, valid ICD-10 format |
| Medication Name | String | Required |
| Additional Diagnoses | List of ICD-10 codes | Optional, each must be valid ICD-10 |
| Medication History | List of strings | Optional |
| Patient Records | String or PDF upload | At least one required |

---

## 4. Outputs

### 4.1 Care Plan (Text / Downloadable)

The LLM-generated care plan must contain these four sections:

1. **Problem List / Drug Therapy Problems (DTPs)** — clinical issues identified from the patient record
2. **Goals (SMART)** — primary outcome goal, safety goal, process goal
3. **Pharmacist Interventions / Plan** — dosing, premedication, infusion protocol, hydration, monitoring, adverse event management
4. **Monitoring Plan & Lab Schedule** — pre-, during-, and post-treatment labs and vitals

Example output structure (based on IVIG/MG case):

```
Problem List
- Need for rapid immunomodulation
- Risk of infusion-related reactions
- Risk of renal dysfunction / volume overload
- Risk of thromboembolic events
- Drug–drug interaction screening
- Patient education / adherence gap

Goals (SMART)
- Primary: Clinically meaningful improvement within 2 weeks
- Safety: No severe infusion reaction, no acute kidney injury
- Process: Complete full 2 g/kg course with documented monitoring

Pharmacist Interventions
- Dosing & Administration
- Premedication protocol
- Infusion rates & titration
- Hydration & renal protection
- Adverse event management

Monitoring Plan
- Pre-infusion: CBC, BMP, baseline vitals
- During infusion: Vitals q15–30 min
- Post-course (3–7 days): BMP for renal function
```

### 4.2 Pharma Export

Structured report (CSV or similar) covering all orders for a given period, exportable for pharma reporting.

---

## 5. Duplicate Detection Rules

### 5.1 Order Duplicates

| Scenario | Action | Reason |
|---|---|---|
| Same patient (MRN) + same medication + same date | ❌ **ERROR — block submission** | Definite duplicate submission |
| Same patient (MRN) + same medication + different date | ⚠️ **WARNING — require confirmation to proceed** | May be a refill |

### 5.2 Patient Duplicates

| Scenario | Action | Reason |
|---|---|---|
| MRN matches existing record but name or DOB differs | ⚠️ **WARNING — require confirmation to proceed** | Possible data entry error |
| Name + DOB match existing record but MRN differs | ⚠️ **WARNING — require confirmation to proceed** | Possible duplicate patient record |

### 5.3 Provider Deduplication

| Scenario | Action | Reason |
|---|---|---|
| NPI matches existing provider but name differs | ❌ **ERROR — must correct before submission** | NPI is the authoritative unique identifier |

Provider records are entered once and reused. The form should offer autocomplete/lookup against existing providers by NPI.

---

## 6. Functional Requirements

| Feature | Priority | Notes |
|---|---|---|
| Web form with validation | ✅ Must Have | Every field validated per rules above |
| Order duplicate detection | ✅ Must Have | Block or warn per rules in §5.1 |
| Patient duplicate detection | ✅ Must Have | Warn per rules in §5.2 |
| Provider deduplication | ✅ Must Have | Error + correct per §5.3 |
| LLM care plan generation | ✅ Must Have | Core value; must include 4 required sections |
| Care plan download | ✅ Must Have | Text file; staff prints and gives to patient |
| Pharma export | ✅ Must Have | Needed for reimbursement reporting |

---

## 7. Production-Ready Requirements

- **Validation:** Every input validated on both client and server side
- **Integrity:** Duplicate and consistency rules enforced at the data layer, not just UI
- **Error handling:** Errors are safe (no stack traces to users), clear (actionable messages), and contained (one failure doesn't cascade)
- **Modularity:** Code organized by domain (patient, order, provider, care-plan, export)
- **Automated tests:** Unit tests for all validation logic, duplicate detection rules, and LLM prompt construction
- **Run out of the box:** Single command setup (e.g., `docker compose up` or `npm install && npm start`)

---

## 8. Data Model (Draft)

### Patient
```
mrn (PK, 6-digit unique)
first_name
last_name
date_of_birth
sex
weight
allergies
```

### Provider
```
npi (PK, 10-digit unique)
name
```

### Order
```
order_id (PK)
mrn (FK → Patient)
npi (FK → Provider)
medication_name
primary_diagnosis (ICD-10)
additional_diagnoses (list of ICD-10)
medication_history (list of strings)
patient_records_text
patient_records_pdf_path
created_date
```

### CarePlan
```
care_plan_id (PK)
order_id (FK → Order, unique — one plan per order)
generated_at
content_text
```

---

## 9. System Architecture (High-Level)

```
[Web Form UI]
     │
     ▼
[API Server]
  ├── Validation layer (field + integrity rules)
  ├── Duplicate detection engine
  ├── Provider registry (NPI lookup + dedup)
  ├── LLM service (care plan generation)
  └── Export service (pharma reporting)
     │
     ▼
[Database]
  ├── Patients
  ├── Providers
  ├── Orders
  └── Care Plans
```

---

## 10. LLM Integration

- **Input:** Structured patient/order data + free-text patient records (or parsed PDF text)
- **Prompt:** System prompt instructs the model to act as a clinical pharmacist and generate a care plan with the four required sections
- **Output:** Plain text care plan, stored in DB and available for download
- **Guardrails:** Output must be reviewed by staff before printing — the tool assists, it does not replace pharmacist judgment

---

## 11. Open Questions

1. **Authentication:** How do staff log in? SSO with CVS credentials, or local accounts?
2. **PDF parsing:** Which library/service handles PDF-to-text extraction for patient records?
3. **LLM provider:** Is there a preferred vendor (OpenAI, Anthropic, Azure OpenAI)? Any data-handling constraints for PHI?
4. **Pharma export format:** Is there a specific format required by pharma partners (CSV, HL7, proprietary)?
5. **Audit logging:** Are there compliance requirements to log who generated/viewed each care plan?
6. **Deployment:** Cloud (AWS/Azure/GCP), on-prem, or CVS-internal infrastructure?
