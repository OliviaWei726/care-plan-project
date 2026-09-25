from django.db import models


class Provider(models.Model):
    npi  = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} (NPI: {self.npi})"


class Patient(models.Model):
    mrn           = models.CharField(max_length=10, unique=True)
    first_name    = models.CharField(max_length=100)
    last_name     = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (MRN: {self.mrn})"


class Order(models.Model):
    patient             = models.ForeignKey(Patient,  on_delete=models.CASCADE, related_name="orders")
    provider            = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="orders")
    medication_name     = models.CharField(max_length=200)
    primary_diagnosis   = models.CharField(max_length=20)
    additional_diagnoses = models.TextField(blank=True, help_text="One ICD-10 code per line")
    medication_history  = models.TextField(blank=True, help_text="One entry per line")
    patient_records     = models.TextField(blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} — {self.patient} / {self.medication_name}"


class CarePlan(models.Model):
    STATUS_PENDING   = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED    = "failed"
    STATUS_CHOICES   = [
        (STATUS_PENDING,   "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED,    "Failed"),
    ]

    order        = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="care_plan")
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    content      = models.TextField(blank=True)   # 还没生成时为空
    generated_at = models.DateTimeField(null=True, blank=True)  # 生成完才填

    def __str__(self):
        return f"CarePlan for Order #{self.order_id} [{self.status}]"
