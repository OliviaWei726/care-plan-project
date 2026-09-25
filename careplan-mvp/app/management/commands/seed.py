"""
python manage.py seed
Clears existing data and inserts fresh mock records.
"""
from django.core.management.base import BaseCommand
from app.models import Provider, Patient, Order, CarePlan


PROVIDERS = [
    {"npi": "1234567890", "name": "Dr. Sarah Chen"},
    {"npi": "9876543210", "name": "Dr. Marcus Webb"},
]

PATIENTS = [
    {"mrn": "001001", "first_name": "Alice",   "last_name": "Brennan",  "date_of_birth": "1979-06-08"},
    {"mrn": "001002", "first_name": "Robert",  "last_name": "Nguyen",   "date_of_birth": "1965-03-22"},
    {"mrn": "001003", "first_name": "Maria",   "last_name": "Delgado",  "date_of_birth": "1988-11-15"},
    {"mrn": "001004", "first_name": "James",   "last_name": "Okafor",   "date_of_birth": "1952-07-30"},
]

ORDERS = [
    {
        "patient_mrn":        "001001",
        "provider_npi":       "1234567890",
        "medication_name":    "IVIG (Gamunex-C)",
        "primary_diagnosis":  "G70.01",
        "additional_diagnoses": "I10\nK21.0",
        "medication_history": "Pyridostigmine 60 mg PO q6h\nPrednisone 10 mg PO daily\nLisinopril 10 mg PO daily",
        "patient_records":    "46-year-old female with AChR+ generalized myasthenia gravis MGFA IIb. "
                              "Progressive proximal weakness and ptosis over 2 weeks. "
                              "Neurology recommends IVIG 2 g/kg over 5 days for rapid immunomodulation.",
        "care_plan":          """1. Problem List / Drug Therapy Problems (DTPs)
- Need for rapid immunomodulation to reduce myasthenic symptoms
- Risk of infusion-related reactions (headache, fever, chills)
- Risk of renal dysfunction or volume overload
- Risk of thromboembolic events (IgG hyperviscosity)
- Drug–drug interaction screening required
- Patient education gap on IVIG therapy

2. Goals (SMART)
- Primary: Clinically meaningful improvement in muscle strength within 2 weeks of completing IVIG course
- Safety: No severe infusion reaction (grade ≥3), no acute kidney injury (creatinine rise <0.5 mg/dL)
- Process: Complete full 2 g/kg course (split over 5 days) with documented vitals every 15–30 min per infusion

3. Pharmacist Interventions / Plan
- Dosing & Administration: 2 g/kg total divided over 5 days (0.4 g/kg/day); use ideal body weight
- Premedication: Acetaminophen 650 mg PO + diphenhydramine 25 mg IV 30 min before each infusion
- Infusion rate: Start at 0.5 mL/kg/hr; titrate up by 0.5 mL/kg/hr q30 min if tolerated; max 4 mL/kg/hr
- Hydration: Encourage oral fluids; monitor urine output; hold if creatinine rises >25% from baseline
- Adverse event management: Slow or stop infusion for headache, rigors, or O2 sat drop; have epinephrine available

4. Monitoring Plan & Lab Schedule
- Pre-infusion (Day 1): CBC, BMP, LFTs, baseline vitals, weight
- During each infusion: Vitals (BP, HR, SpO2, temp) q15 min × first hour, then q30 min
- Day 3 check-in: BMP (renal function), fluid status assessment
- Post-course Day 5–7: BMP, clinical reassessment of muscle strength and ptosis""",
    },
    {
        "patient_mrn":        "001002",
        "provider_npi":       "9876543210",
        "medication_name":    "Rituximab (Rituxan)",
        "primary_diagnosis":  "M05.79",
        "additional_diagnoses": "E11.9\nI10",
        "medication_history": "Methotrexate 15 mg PO weekly\nFolic acid 1 mg PO daily\nMetformin 500 mg PO BID",
        "patient_records":    "58-year-old male with seropositive rheumatoid arthritis, inadequate response "
                              "to methotrexate after 6 months. Rheumatology recommends rituximab biologic therapy. "
                              "Type 2 diabetes well-controlled. Hypertension stable on lisinopril.",
        "care_plan":          """1. Problem List / Drug Therapy Problems (DTPs)
- Active RA with inadequate MTX response requiring biologic escalation
- Risk of infusion-related reactions (cytokine release syndrome)
- Risk of serious infection (B-cell depletion lasting 6–9 months)
- Hepatitis B reactivation risk — screening required before initiation
- Drug interaction: MTX to be continued concurrently per protocol

2. Goals (SMART)
- Primary: Achieve ACR 20 response at 24 weeks post first cycle
- Safety: No serious infection within 6 months; no HBV reactivation
- Process: Complete 2-dose cycle (Day 1 and Day 15) with full premedication protocol

3. Pharmacist Interventions / Plan
- Dosing: Rituximab 1000 mg IV on Day 1 and Day 15 (one cycle); repeat cycle at 24 weeks PRN
- Premedication: Methylprednisolone 100 mg IV + acetaminophen 1000 mg PO + diphenhydramine 50 mg IV 30 min prior
- Infusion rate: Start 50 mg/hr; increase by 50 mg/hr q30 min; max 400 mg/hr if no reaction
- Infection prophylaxis: Ensure PCP prophylaxis (TMP-SMX) given B-cell depletion; hold live vaccines
- Continue MTX 15 mg/week and folic acid throughout

4. Monitoring Plan & Lab Schedule
- Pre-treatment: HBsAg, HBcAb, CBC with differential, CMP, quantitative immunoglobulins
- Day 1 and Day 15 infusions: Vitals q15 min × 1 hr, then q30 min; observe 1 hr post-infusion
- Week 4 and Week 12: CBC (neutrophil count), CMP
- Week 24: Clinical reassessment, repeat CBC, immunoglobulins before next cycle""",
    },
    {
        "patient_mrn":        "001003",
        "provider_npi":       "1234567890",
        "medication_name":    "Pembrolizumab (Keytruda)",
        "primary_diagnosis":  "C34.11",
        "additional_diagnoses": "J44.1",
        "medication_history": "Carboplatin AUC5 IV q3w (cycle 1 completed)\nPaclitaxel 200 mg/m² IV q3w",
        "patient_records":    "35-year-old female, non-smoker, stage IIIA non-small cell lung cancer (adenocarcinoma). "
                              "PD-L1 TPS 65%. EGFR/ALK negative. Completed 1 cycle of carboplatin/paclitaxel. "
                              "Oncology adding pembrolizumab for checkpoint inhibition. Mild COPD.",
        "care_plan":          """1. Problem List / Drug Therapy Problems (DTPs)
- Active NSCLC requiring immunotherapy intensification
- Risk of immune-related adverse events (irAEs): pneumonitis, colitis, hepatitis, endocrinopathies
- Overlapping pulmonary risk: pre-existing COPD complicates pneumonitis detection
- Drug interaction: corticosteroids (used for irAE management) may blunt checkpoint inhibitor efficacy

2. Goals (SMART)
- Primary: Achieve partial or complete radiographic response at first restaging (Week 9)
- Safety: Identify and manage irAEs early; no grade 3–4 irAE requiring permanent discontinuation in cycle 1–2
- Process: Administer pembrolizumab 200 mg IV q3w on schedule; complete 35 cycles or until progression

3. Pharmacist Interventions / Plan
- Dosing: Pembrolizumab 200 mg IV fixed dose over 30 min q3 weeks (no weight-based adjustment)
- No standard premedication required; do NOT use routine antihistamines or steroids pre-infusion
- irAE management protocol: Grade 1 — monitor; Grade 2 — hold + prednisone 1 mg/kg/day; Grade 3–4 — permanently discontinue + high-dose corticosteroids
- Patient counseling: Instruct on irAE symptoms (new cough, diarrhea, rash, fatigue) and when to call

4. Monitoring Plan & Lab Schedule
- Pre-cycle 1: LFTs, TFTs (TSH, free T4), CBC, CMP, fasting glucose, chest CT baseline
- Before each infusion (q3w): LFTs, TSH, CBC, symptom review
- Week 9: CT chest/abdomen/pelvis for restaging
- Ongoing: Monitor for hypothyroidism (fatigue, weight gain) — common late irAE""",
    },
    {
        "patient_mrn":        "001004",
        "provider_npi":       "9876543210",
        "medication_name":    "Enoxaparin (Lovenox)",
        "primary_diagnosis":  "I26.99",
        "additional_diagnoses": "C61\nN18.3",
        "medication_history": "Leuprolide 7.5 mg IM monthly\nAspirin 81 mg PO daily",
        "patient_records":    "71-year-old male with unprovoked submassive PE diagnosed 3 days ago. "
                              "Background of prostate cancer on hormonal therapy. CKD stage 3 (eGFR 38). "
                              "Hematology recommends therapeutic enoxaparin bridge while evaluating for DOAC transition.",
        "care_plan":          """1. Problem List / Drug Therapy Problems (DTPs)
- Active submassive PE requiring therapeutic anticoagulation
- Renal impairment (CKD stage 3, eGFR 38) requiring dose adjustment of enoxaparin
- Elevated bleeding risk (age 71, aspirin use, cancer)
- Cancer-associated thrombosis — long-term anticoagulation strategy needed
- Drug interaction: aspirin increases bleeding risk when combined with enoxaparin

2. Goals (SMART)
- Primary: Therapeutic anti-Xa levels (0.5–1.0 IU/mL peak) achieved within 48 hours
- Safety: No major bleeding event (hemoglobin drop >2 g/dL or transfusion requirement)
- Process: Dose-adjust for renal function; anti-Xa level checked 4 hr after 3rd or 4th dose

3. Pharmacist Interventions / Plan
- Dosing: 1 mg/kg SQ q12h (renally adjusted — avoid 1.5 mg/kg q24h in CKD eGFR <30; eGFR 38 → use q12h)
- Administer SQ into abdomen, alternating sides; avoid IM
- Aspirin: discuss holding with oncology and hematology given dual anticoagulation/antiplatelet use
- Transition plan: reassess at Day 5–7 for DOAC eligibility (apixaban preferred in cancer patients)
- Patient/caregiver injection training required prior to home discharge

4. Monitoring Plan & Lab Schedule
- Pre-treatment: CBC, CMP (eGFR), coagulation panel (PT/INR, aPTT), stool guaiac
- Day 2 (after 3rd dose): Anti-Xa level drawn 4 hr post-dose; target 0.5–1.0 IU/mL
- Daily: CBC for thrombocytopenia (HIT monitoring), renal function q48h
- Day 5–7: Clinical reassessment, HIT antibody if platelets drop >50%""",
    },
]


class Command(BaseCommand):
    help = "Seed the database with mock pharmacy data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing existing data...")
        CarePlan.objects.all().delete()
        Order.objects.all().delete()
        Patient.objects.all().delete()
        Provider.objects.all().delete()

        self.stdout.write("Creating providers...")
        providers = {}
        for p in PROVIDERS:
            obj = Provider.objects.create(**p)
            providers[obj.npi] = obj
            self.stdout.write(f"  + {obj}")

        self.stdout.write("Creating patients...")
        patients = {}
        for p in PATIENTS:
            obj = Patient.objects.create(**p)
            patients[obj.mrn] = obj
            self.stdout.write(f"  + {obj}")

        self.stdout.write("Creating orders and care plans...")
        for o in ORDERS:
            order = Order.objects.create(
                patient=patients[o["patient_mrn"]],
                provider=providers[o["provider_npi"]],
                medication_name=o["medication_name"],
                primary_diagnosis=o["primary_diagnosis"],
                additional_diagnoses=o["additional_diagnoses"],
                medication_history=o["medication_history"],
                patient_records=o["patient_records"],
            )
            CarePlan.objects.create(order=order, content=o["care_plan"])
            self.stdout.write(f"  + Order #{order.pk}: {order.patient} / {order.medication_name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {Provider.objects.count()} providers, "
            f"{Patient.objects.count()} patients, "
            f"{Order.objects.count()} orders, "
            f"{CarePlan.objects.count()} care plans."
        ))
