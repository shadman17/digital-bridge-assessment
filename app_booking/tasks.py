import logging

from celery import shared_task
from django.utils import timezone

from app_booking.models import BookingSystem
from app_booking.sync import DataSyncHandler

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(), retry_backoff=False)
def sync_booking_system_task(self, booking_system_id: int) -> dict:
    """
    Full sync in strict order:
    providers -> customers -> services -> appointments
    """
    booking_system = BookingSystem.objects.filter(id=booking_system_id).first()
    if not booking_system:
        logger.error("BookingSystem not found for sync: id=%s", booking_system_id)
        raise ValueError(f"BookingSystem {booking_system_id} not found")

    handler = DataSyncHandler(booking_system)

    booking_system.sync_status = BookingSystem.SyncStatus.PENDING
    booking_system.last_error = ""
    booking_system.save(update_fields=["sync_status", "last_error", "updated_at"])

    try:
        summary = {
            "providers": handler.sync_providers(),
            "customers": handler.sync_customers(),
            "services": handler.sync_services(),
            "appointments": handler.sync_appointments(),
        }
    except Exception as exc:
        logger.exception(
            "Full sync failed for booking_system=%s error=%s",
            booking_system_id,
            exc,
        )
        booking_system.sync_status = BookingSystem.SyncStatus.ERROR
        booking_system.last_error = str(exc)
        booking_system.save(update_fields=["sync_status", "last_error", "updated_at"])
        raise

    booking_system.sync_status = BookingSystem.SyncStatus.SYNCED
    booking_system.last_synced_at = timezone.now()
    booking_system.last_error = ""
    booking_system.save(
        update_fields=["sync_status", "last_synced_at", "last_error", "updated_at"]
    )

    logger.info(
        "Full sync completed for booking_system=%s summary=%s",
        booking_system_id,
        summary,
    )
    return summary


@shared_task
def sync_providers_task(booking_system_id: int) -> int:
    booking_system = BookingSystem.objects.get(id=booking_system_id)
    count = DataSyncHandler(booking_system).sync_providers()
    logger.info(
        "Provider-only sync completed booking_system=%s count=%s",
        booking_system_id,
        count,
    )
    return count


@shared_task
def sync_appointments_task(booking_system_id: int) -> int:
    booking_system = BookingSystem.objects.get(id=booking_system_id)
    count = DataSyncHandler(booking_system).sync_appointments()
    logger.info(
        "Appointment-only sync completed booking_system=%s count=%s",
        booking_system_id,
        count,
    )
    return count


@shared_task
def sync_all_active_booking_systems_task() -> list[dict]:
    results = []
    ids = list(
        BookingSystem.objects.filter(is_active=True).values_list("id", flat=True)
    )

    for booking_system_id in ids:
        try:
            summary = sync_booking_system_task(booking_system_id)
            results.append(
                {
                    "booking_system_id": booking_system_id,
                    "status": "synced",
                    "summary": summary,
                }
            )
        except Exception as exc:
            logger.exception(
                "Periodic sync failed for booking_system=%s error=%s",
                booking_system_id,
                exc,
            )
            results.append(
                {
                    "booking_system_id": booking_system_id,
                    "status": "error",
                    "error": str(exc),
                }
            )

    logger.info("Scheduled active booking systems sync: %s", results)
    return results
