from django.urls import path

from app_booking.views import (
    AppointmentListView,
    BookingSystemConnectView,
    BookingSystemStatusView,
    CustomerListView,
    ProviderListView,
    ServiceListView,
)

urlpatterns = [
    path(
        "booking-systems/connect/",
        BookingSystemConnectView.as_view(),
        name="booking-system-connect",
    ),
    path(
        "booking-systems/<int:booking_system_id>/status/",
        BookingSystemStatusView.as_view(),
        name="booking-system-status",
    ),
    path(
        "booking-systems/<int:booking_system_id>/providers/",
        ProviderListView.as_view(),
        name="provider-list",
    ),
    path(
        "booking-systems/<int:booking_system_id>/customers/",
        CustomerListView.as_view(),
        name="customer-list",
    ),
    path(
        "booking-systems/<int:booking_system_id>/services/",
        ServiceListView.as_view(),
        name="service-list",
    ),
    path(
        "booking-systems/<int:booking_system_id>/appointments/",
        AppointmentListView.as_view(),
        name="appointment-list",
    ),
    path(
        "booking-systems/<int:booking_system_id>/appointments/",
        AppointmentListView.as_view(),
        name="appointment-list-legacy",
    ),
]
