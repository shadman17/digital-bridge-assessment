# This is generated entirely by ChatGPT based on the request to add indexes for appointment reporting. It creates three composite indexes on the `app_booking_appointment` table to optimize common query patterns used in reporting, such as filtering by booking system and date, and grouping by provider or service. The migration includes both the SQL to create the indexes and the reverse SQL to drop them if the migration is rolled back.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app_booking", "0002_bookingsystem_last_error_and_more"),
    ]

    operations = [
        # Speeds up provider-performance aggregations by matching a safe immutable
        # index key shape: booking_system_id + start_time, then provider_id.
        #
        # Note: Using DATE(start_time) in a PostgreSQL index expression can fail for
        # timestamptz columns because it is not immutable.
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS appt_sys_date_provider_idx "
                "ON app_booking_appointment (booking_system_id, start_time, provider_id);"
            ),
            reverse_sql="DROP INDEX IF EXISTS appt_sys_date_provider_idx;",
        ),
        # Helps COUNT(DISTINCT customer_id) (and monthly/customer rollups) over the same
        # booking system + date range by making customer_id cheap to scan per day.
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS appt_sys_date_customer_idx "
                "ON app_booking_appointment (booking_system_id, start_time, customer_id);"
            ),
            reverse_sql="DROP INDEX IF EXISTS appt_sys_date_customer_idx;",
        ),
        # Supports top-services revenue aggregations that filter by booking system and
        # date window before grouping by service_id.
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS appt_sys_date_service_idx "
                "ON app_booking_appointment (booking_system_id, start_time, service_id);"
            ),
            reverse_sql="DROP INDEX IF EXISTS appt_sys_date_service_idx;",
        ),
    ]
