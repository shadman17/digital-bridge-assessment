-- Provider performance query for a booking system and date range.
-- Parameters:
--   1) booking_system_id
--   2) start_date (YYYY-MM-DD)
--   3) end_date (YYYY-MM-DD)
SELECT
    CONCAT(p.first_name, ' ', p.last_name) AS provider_name,
    COUNT(a.id) AS total_appointments,
    COALESCE(SUM(s.price), 0) AS total_revenue,
    COUNT(DISTINCT a.customer_id) AS unique_customers_served,
    COALESCE(AVG(s.price), 0) AS avg_appointment_value
FROM app_booking_appointment AS a
INNER JOIN app_booking_provider AS p
    ON p.id = a.provider_id
INNER JOIN app_booking_service AS s
    ON s.id = a.service_id
WHERE
    a.booking_system_id = %s
    AND DATE(a.start_time) >= %s
    AND DATE(a.start_time) <= %s
GROUP BY p.id, p.first_name, p.last_name
ORDER BY total_revenue DESC, provider_name;