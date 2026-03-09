from rest_framework import serializers

from app_booking.models import Appointment, BookingSystem, Customer, Provider, Service


class BookingSystemConnectSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = BookingSystem
        fields = [
            "id",
            "name",
            "base_url",
            "username",
            "password",
            "is_active",
            "sync_status",
        ]
        read_only_fields = ["id", "is_active", "sync_status"]

    def create(self, validated_data):
        username = validated_data.pop("username")
        password = validated_data.pop("password")
        validated_data["credentials"] = {
            "base_url": validated_data["base_url"],
            "username": username,
            "password": password,
        }
        return super().create(validated_data)


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = "__all__"
