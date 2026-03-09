from app_booking.pagination import EnvelopePaginator
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from app_booking.models import Appointment, BookingSystem, Customer, Provider, Service
from app_booking.renderers import EnvelopeJSONRenderer
from app_booking.serializers import (
    AppointmentSerializer,
    BookingSystemConnectSerializer,
    CustomerSerializer,
    ProviderSerializer,
    ServiceSerializer,
)
from .tasks import sync_booking_system_task


class BaseEnvelopeAPIView(APIView):
    renderer_classes = [EnvelopeJSONRenderer]

    @staticmethod
    def paginated_response(queryset, serializer_class, request):
        paginator = EnvelopePaginator(request)
        return paginator.get_paginated_response(queryset, serializer_class)


class BookingSystemConnectView(BaseEnvelopeAPIView):
    def post(self, request):
        serializer = BookingSystemConnectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking_system = serializer.save()

        return Response(
            {
                "data": {
                    "id": booking_system.id,
                    "name": booking_system.name,
                    "base_url": booking_system.base_url,
                    "sync_status": booking_system.sync_status,
                },
                "errors": [],
                "meta": None,
            },
            status=status.HTTP_201_CREATED,
        )


class BookingSystemStatusView(BaseEnvelopeAPIView):
    def get(self, request, booking_system_id):
        booking_system = BookingSystem.objects.filter(id=booking_system_id).first()
        if not booking_system:
            return Response(
                {
                    "data": None,
                    "errors": [{"message": "Booking system not found."}],
                    "meta": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        counts = {
            "providers": booking_system.providers.count(),
            "customers": booking_system.customers.count(),
            "services": booking_system.services.count(),
            "appointments": booking_system.appointments.count(),
        }
        return Response(
            {
                "data": {
                    "id": booking_system.id,
                    "sync_status": booking_system.sync_status,
                    "last_synced_at": booking_system.last_synced_at,
                    "record_counts": counts,
                },
                "errors": [],
                "meta": None,
            }
        )


class ProviderListView(BaseEnvelopeAPIView):
    def get(self, request, booking_system_id):
        queryset = Provider.objects.filter(
            booking_system_id=booking_system_id
        ).order_by("id")
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
        return self.paginated_response(queryset, ProviderSerializer, request)


class CustomerListView(BaseEnvelopeAPIView):
    def get(self, request, booking_system_id):
        queryset = Customer.objects.filter(
            booking_system_id=booking_system_id
        ).order_by("id")
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
        return self.paginated_response(queryset, CustomerSerializer, request)


class ServiceListView(BaseEnvelopeAPIView):
    def get(self, request, booking_system_id):
        queryset = Service.objects.filter(booking_system_id=booking_system_id).order_by(
            "id"
        )
        return self.paginated_response(queryset, ServiceSerializer, request)


# Took help from ChatGPT for identifying the parse date and validation logic.
class AppointmentListView(BaseEnvelopeAPIView):
    def get(self, request, booking_system_id):
        queryset = Appointment.objects.filter(
            booking_system_id=booking_system_id
        ).order_by("start_time")

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date:
            parsed_start = parse_date(start_date)
            if not parsed_start:
                raise ValidationError({"start_date": "Invalid format. Use YYYY-MM-DD."})
            queryset = queryset.filter(start_time__date__gte=parsed_start)

        if end_date:
            parsed_end = parse_date(end_date)
            if not parsed_end:
                raise ValidationError({"end_date": "Invalid format. Use YYYY-MM-DD."})
            queryset = queryset.filter(start_time__date__lte=parsed_end)

        return self.paginated_response(queryset, AppointmentSerializer, request)


class BookingSystemSyncTriggerView(BaseEnvelopeAPIView):
    def post(self, request, booking_system_id):
        booking_system = BookingSystem.objects.filter(id=booking_system_id).first()
        if not booking_system:
            return Response(
                {
                    "data": None,
                    "errors": [{"message": "Booking system not found."}],
                    "meta": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        task = sync_booking_system_task.delay(booking_system.id)

        return Response(
            {
                "data": {
                    "booking_system_id": booking_system.id,
                    "task_id": task.id,
                    "sync_status": booking_system.sync_status,
                },
                "errors": [],
                "meta": None,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class BookingSystemSyncStatusView(BaseEnvelopeAPIView):
    def get(self, request, booking_system_id):
        booking_system = BookingSystem.objects.filter(id=booking_system_id).first()
        if not booking_system:
            return Response(
                {
                    "data": None,
                    "errors": [{"message": "Booking system not found."}],
                    "meta": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "data": {
                    "id": booking_system.id,
                    "sync_status": booking_system.sync_status,
                    "last_error": booking_system.last_error,
                    "last_synced_at": booking_system.last_synced_at,
                },
                "errors": [],
                "meta": None,
            }
        )
