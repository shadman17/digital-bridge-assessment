# AI-assisted snippet (ChatGPT) used for initial implementation and structure. Modified and integrated into the project by the author.
# Modified and integrated into the project by the author

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import IntegrityError, transaction
from django.utils.dateparse import parse_datetime

from app_booking.models import Appointment, BookingSystem, Customer, Provider, Service
from app_core.client import BookingSystemClient

logger = logging.getLogger(__name__)


class DataSyncHandler:
    def __init__(self, booking_system: BookingSystem):
        self.booking_system = booking_system
        credentials = booking_system.credentials or {}
        self.client = BookingSystemClient(
            base_url=credentials.get("base_url") or booking_system.base_url,
            username=credentials.get("username", ""),
            password=credentials.get("password", ""),
        )

    def sync_all(self) -> dict[str, int]:
        return {
            "providers": self.sync_providers(),
            "customers": self.sync_customers(),
            "services": self.sync_services(),
            "appointments": self.sync_appointments(),
        }

    def sync_providers(self) -> int:
        payload = self.client.get_providers()
        synced = 0

        with transaction.atomic():
            for row in payload:
                try:
                    with transaction.atomic():
                        external_id = self._required_external_id(row, "provider")
                        defaults = {
                            "first_name": self._to_str(row.get("firstName")),
                            "last_name": self._to_str(row.get("lastName")),
                            "email": self._to_str(row.get("email")),
                            "phone": self._to_str(row.get("phone")),
                            "extra_data": row or {},
                        }
                        Provider.objects.update_or_create(
                            booking_system=self.booking_system,
                            external_id=external_id,
                            defaults=defaults,
                        )
                        synced += 1
                except Exception as exc:
                    logger.exception(
                        "Provider sync failed for booking_system=%s payload=%s error=%s",
                        self.booking_system.id,
                        row,
                        exc,
                    )
                    continue

        logger.info(
            "Providers synced for booking_system=%s count=%s",
            self.booking_system.id,
            synced,
        )
        return synced

    def sync_customers(self) -> int:
        payload = self.client.get_customers()
        synced = 0

        with transaction.atomic():
            for row in payload:
                try:
                    with transaction.atomic():
                        external_id = self._required_external_id(row, "customer")
                        defaults = {
                            "first_name": self._to_str(row.get("firstName")),
                            "last_name": self._to_str(row.get("lastName")),
                            "email": self._to_str(row.get("email")),
                            "phone": self._to_str(row.get("phone")),
                            "extra_data": row or {},
                        }
                        Customer.objects.update_or_create(
                            booking_system=self.booking_system,
                            external_id=external_id,
                            defaults=defaults,
                        )
                        synced += 1
                except Exception as exc:
                    logger.exception(
                        "Customer sync failed for booking_system=%s payload=%s error=%s",
                        self.booking_system.id,
                        row,
                        exc,
                    )
                    continue

        logger.info(
            "Customers synced for booking_system=%s count=%s",
            self.booking_system.id,
            synced,
        )
        return synced

    def sync_services(self) -> int:
        payload = self.client.get_services()
        synced = 0

        with transaction.atomic():
            for row in payload:
                try:
                    with transaction.atomic():
                        external_id = self._required_external_id(row, "service")
                        defaults = {
                            "name": self._to_str(row.get("name")),
                            "duration_minutes": self._to_int(
                                row.get("duration"), default=0
                            ),
                            "price": self._to_decimal(row.get("price"), default="0.00"),
                            "currency": self._to_str(row.get("currency"), default=""),
                            "extra_data": row or {},
                        }
                        Service.objects.update_or_create(
                            booking_system=self.booking_system,
                            external_id=external_id,
                            defaults=defaults,
                        )
                        synced += 1
                except Exception as exc:
                    logger.exception(
                        "Service sync failed for booking_system=%s payload=%s error=%s",
                        self.booking_system.id,
                        row,
                        exc,
                    )
                    continue

        logger.info(
            "Services synced for booking_system=%s count=%s",
            self.booking_system.id,
            synced,
        )
        return synced

    def sync_appointments(self) -> int:
        payload = self.client.get_appointments()
        synced = 0

        provider_map = {
            item.external_id: item
            for item in Provider.objects.filter(booking_system=self.booking_system)
        }
        customer_map = {
            item.external_id: item
            for item in Customer.objects.filter(booking_system=self.booking_system)
        }
        service_map = {
            item.external_id: item
            for item in Service.objects.filter(booking_system=self.booking_system)
        }

        with transaction.atomic():
            for row in payload:
                try:
                    with transaction.atomic():
                        external_id = self._required_external_id(row, "appointment")

                        provider_external_id = self._maybe_external_id(
                            row.get("providerId")
                        )
                        customer_external_id = self._maybe_external_id(
                            row.get("customerId")
                        )
                        service_external_id = self._maybe_external_id(
                            row.get("serviceId")
                        )

                        provider = provider_map.get(provider_external_id)
                        customer = customer_map.get(customer_external_id)
                        service = service_map.get(service_external_id)

                        if not provider or not customer or not service:
                            logger.warning(
                                "Skipping appointment external_id=%s booking_system=%s because relation missing "
                                "(provider=%s customer=%s service=%s)",
                                external_id,
                                self.booking_system.id,
                                provider_external_id,
                                customer_external_id,
                                service_external_id,
                            )
                            continue

                        start_time = self._to_datetime(row.get("start"))
                        end_time = self._to_datetime(row.get("end"))

                        defaults = {
                            "provider": provider,
                            "customer": customer,
                            "service": service,
                            "start_time": start_time,
                            "end_time": end_time,
                            "status": self._to_str(row.get("status"), default="booked"),
                            "location": self._to_str(row.get("location")),
                            "extra_data": row or {},
                        }

                        Appointment.objects.update_or_create(
                            booking_system=self.booking_system,
                            external_id=external_id,
                            defaults=defaults,
                        )
                        synced += 1
                except IntegrityError as exc:
                    logger.exception(
                        "Integrity error syncing appointment booking_system=%s payload=%s error=%s",
                        self.booking_system.id,
                        row,
                        exc,
                    )
                    continue
                except Exception as exc:
                    logger.exception(
                        "Appointment sync failed for booking_system=%s payload=%s error=%s",
                        self.booking_system.id,
                        row,
                        exc,
                    )
                    continue

        logger.info(
            "Appointments synced for booking_system=%s count=%s",
            self.booking_system.id,
            synced,
        )
        return synced

    @staticmethod
    def _required_external_id(row: dict[str, Any], label: str) -> str:
        value = row.get("id")
        if value is None or value == "":
            raise ValueError(f"{label} payload missing id")
        return str(value)

    @staticmethod
    def _maybe_external_id(value: Any) -> str | None:
        if value is None or value == "":
            return None
        return str(value)

    @staticmethod
    def _to_str(value: Any, default: str = "") -> str:
        if value is None:
            return default
        return str(value).strip()

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        if value in (None, ""):
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_decimal(value: Any, default: str = "0.00") -> Decimal:
        if value in (None, ""):
            return Decimal(default)
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(default)

    @staticmethod
    def _to_datetime(value: Any):
        if not value:
            raise ValueError("datetime value is required")
        if isinstance(value, str):
            dt = parse_datetime(value.replace(" ", "T")) or parse_datetime(value)
            if dt is None:
                raise ValueError(f"Invalid datetime: {value}")
            return dt
        return value
