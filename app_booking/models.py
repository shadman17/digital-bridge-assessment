from django.db import models
from app_core.models import TimeStampedModel

# AI-assisted snippet (ChatGPT) used for model definitions, based on the project requirements. Adjusted and expanded to fit the specific needs of the project, including Indexes and Constraints. Unnecessary fields and models were removed to keep the code clean. For example, ChatGPT suggested external_id and external_data in a separate model for code reusability, but I don't wanted to use multilevel inheritance just for those two fields. Furthermore, several unnecessay fields were removed to keep the code clean and focused on the core functionality. The models are designed to be flexible and extensible, allowing for future additions as needed.


class BookingSystem(TimeStampedModel):
    class SyncStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SYNCED = "synced", "Synced"
        ERROR = "Error", "Error"

    name = models.CharField(max_length=255)
    base_url = models.URLField()
    credentials = models.JSONField(default=dict)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sync_status = models.CharField(
        max_length=20,
        choices=SyncStatus.choices,
        default=SyncStatus.PENDING,
        db_index=True,
    )

    class Meta:
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class Provider(TimeStampedModel):
    booking_system = models.ForeignKey(
        BookingSystem, on_delete=models.CASCADE, related_name="providers"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    external_id = models.CharField(max_length=255)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking_system", "external_id"],
                name="uniq_provider_external_id_per_system",
            )
        ]
        indexes = [models.Index(fields=["booking_system", "last_name", "first_name"])]


class Customer(TimeStampedModel):
    booking_system = models.ForeignKey(
        BookingSystem, on_delete=models.CASCADE, related_name="customers"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    external_id = models.CharField(max_length=255)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking_system", "external_id"],
                name="uniq_customer_external_id_per_system",
            )
        ]
        indexes = [models.Index(fields=["booking_system", "last_name", "first_name"])]


class Service(TimeStampedModel):
    booking_system = models.ForeignKey(
        BookingSystem, on_delete=models.CASCADE, related_name="services"
    )
    name = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    external_id = models.CharField(max_length=255)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking_system", "external_id"],
                name="uniq_service_external_id_per_system",
            )
        ]
        indexes = [models.Index(fields=["booking_system", "name"])]


class Appointment(TimeStampedModel):
    booking_system = models.ForeignKey(
        BookingSystem,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    provider = models.ForeignKey(
        Provider, on_delete=models.PROTECT, related_name="appointments"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="appointments"
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, related_name="appointments"
    )
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=50)
    location = models.CharField(max_length=255, blank=True)
    external_id = models.CharField(max_length=255)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking_system", "external_id"],
                name="uniq_appointment_external_id_per_system",
            )
        ]
        indexes = [models.Index(fields=["booking_system", "start_time"])]
