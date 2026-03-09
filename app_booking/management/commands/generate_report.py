# AI-assisted snippet (ChatGPT) used for initial implementation and structure.
# Modified and integrated into the project by the author such as top 3 providers and services logic, formatting, and error handling.

import json
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncMonth

from app_booking.models import Appointment, BookingSystem


class Command(BaseCommand):
    help = "Generate analytics report for a booking system in a date range"

    def add_arguments(self, parser):
        parser.add_argument("--booking_system_id", type=int, required=True)
        parser.add_argument("--start_date", type=str, required=True)
        parser.add_argument("--end_date", type=str, required=True)

    @staticmethod
    def _to_float(value):
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        return float(value)

    def handle(self, *args, **options):
        booking_system_id = options["booking_system_id"]
        start_date = options["start_date"]
        end_date = options["end_date"]

        try:
            booking_system = BookingSystem.objects.only("id", "name").get(
                id=booking_system_id
            )
        except BookingSystem.DoesNotExist as exc:
            raise CommandError(
                f"Booking system with id={booking_system_id} does not exist"
            ) from exc

        appointments_qs = Appointment.objects.filter(
            booking_system_id=booking_system_id,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date,
        )

        summary_data = appointments_qs.aggregate(
            total_appointments=Count("id"),
            unique_customers=Count("customer_id", distinct=True),
            total_revenue=Sum("service__price"),
            avg_appointment_value=Avg("service__price"),
        )

        monthly_data = (
            appointments_qs.annotate(month=TruncMonth("start_time"))
            .values("month")
            .annotate(
                appointments=Count("id"),
                unique_customers=Count("customer_id", distinct=True),
                revenue=Sum("service__price"),
            )
            .order_by("month")
        )

        top_providers_data = (
            appointments_qs.values("provider__first_name", "provider__last_name")
            .annotate(
                total_appointments=Count("id"),
                total_revenue=Sum("service__price"),
            )
            .order_by("-total_revenue", "provider__last_name", "provider__first_name")[
                :3
            ]
        )

        top_services_data = (
            appointments_qs.values("service__name")
            .annotate(times_booked=Count("id"), total_revenue=Sum("service__price"))
            .order_by("-total_revenue", "service__name")[:3]
        )

        report = {
            "booking_system": booking_system.name,
            "period": f"{start_date} to {end_date}",
            "summary": {
                "total_appointments": summary_data["total_appointments"] or 0,
                "unique_customers": summary_data["unique_customers"] or 0,
                "total_revenue": round(
                    self._to_float(summary_data["total_revenue"]), 2
                ),
                "avg_appointment_value": round(
                    self._to_float(summary_data["avg_appointment_value"]), 2
                ),
            },
            "monthly_breakdown": [
                {
                    "month": item["month"].strftime("%Y-%m"),
                    "appointments": item["appointments"],
                    "unique_customers": item["unique_customers"],
                    "revenue": round(self._to_float(item["revenue"]), 2),
                }
                for item in monthly_data
            ],
            "top_providers": [
                {
                    "name": (
                        f"{item['provider__first_name']} {item['provider__last_name']}"
                    ).strip(),
                    "total_appointments": item["total_appointments"],
                    "total_revenue": round(self._to_float(item["total_revenue"]), 2),
                }
                for item in top_providers_data
            ],
            "top_services": [
                {
                    "name": item["service__name"],
                    "times_booked": item["times_booked"],
                    "total_revenue": round(self._to_float(item["total_revenue"]), 2),
                }
                for item in top_services_data
            ],
        }

        self.stdout.write(json.dumps(report, indent=2))
