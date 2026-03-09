from django.contrib import admin

# Register your models here.
from .models import BookingSystem, Customer, Provider, Service, Appointment

admin.site.register(BookingSystem)
admin.site.register(Customer)
admin.site.register(Provider)
admin.site.register(Service)
admin.site.register(Appointment)
