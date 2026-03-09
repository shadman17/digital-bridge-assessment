# This was written by the ChatGPT to test the API client. It is not a complete test suite, but it covers the main functionality and error handling of the client.

from unittest import TestCase
from unittest.mock import Mock, patch
import requests

from app_core.client import BookingSystemClient


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text="", headers=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else []
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._json_data


class BookingSystemClientTests(TestCase):
    def setUp(self):
        self.client = BookingSystemClient(
            base_url="http://localhost:8888/index.php/api/v1",
            username="admin",
            password="admin123",
        )
        self.client.page_size = 2

    @patch("app_core.client.requests.Session.request")
    def test_test_connection_returns_true_on_success(self, mock_request):
        mock_request.return_value = FakeResponse(status_code=200, json_data=[{"id": 1}])

        result = self.client.test_connection()

        self.assertTrue(result)
        mock_request.assert_called_once()

    @patch("app_core.client.requests.Session.request")
    def test_test_connection_returns_false_on_failure(self, mock_request):
        mock_request.return_value = FakeResponse(status_code=401, text="Unauthorized")

        result = self.client.test_connection()

        self.assertFalse(result)
        mock_request.assert_called_once()

    @patch("app_core.client.requests.Session.request")
    def test_get_providers_handles_pagination(self, mock_request):
        mock_request.side_effect = [
            FakeResponse(status_code=200, json_data=[{"id": 1}, {"id": 2}]),
            FakeResponse(status_code=200, json_data=[{"id": 3}]),
        ]

        result = self.client.get_providers()

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[2]["id"], 3)
        self.assertEqual(mock_request.call_count, 2)

        first_call = mock_request.call_args_list[0]
        second_call = mock_request.call_args_list[1]

        self.assertEqual(first_call.kwargs["params"]["page"], 1)
        self.assertEqual(second_call.kwargs["params"]["page"], 2)

    @patch("app_core.client.requests.Session.request")
    def test_get_customers_handles_pagination(self, mock_request):
        mock_request.side_effect = [
            FakeResponse(status_code=200, json_data=[{"id": 10}, {"id": 11}]),
            FakeResponse(status_code=200, json_data=[]),
        ]

        result = self.client.get_customers()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 10)
        self.assertEqual(result[1]["id"], 11)

    @patch("app_core.client.requests.Session.request")
    def test_get_services_handles_pagination(self, mock_request):
        mock_request.side_effect = [
            FakeResponse(status_code=200, json_data=[{"id": 21}, {"id": 22}]),
            FakeResponse(status_code=200, json_data=[{"id": 23}]),
        ]

        result = self.client.get_services()

        self.assertEqual(len(result), 3)
        self.assertEqual([item["id"] for item in result], [21, 22, 23])

    @patch("app_core.client.requests.Session.request")
    def test_get_appointments_without_date_filters(self, mock_request):
        mock_request.side_effect = [
            FakeResponse(
                status_code=200,
                json_data=[
                    {"id": 1, "start": "2026-03-01 10:00:00"},
                    {"id": 2, "start": "2026-03-05 11:00:00"},
                ],
            ),
            FakeResponse(
                status_code=200,
                json_data=[
                    {"id": 3, "start": "2026-03-10 12:00:00"},
                ],
            ),
        ]

        result = self.client.get_appointments()

        self.assertEqual(len(result), 3)
        self.assertEqual([a["id"] for a in result], [1, 2, 3])

    @patch("app_core.client.requests.Session.request")
    def test_get_appointments_with_date_filters(self, mock_request):
        mock_request.side_effect = [
            FakeResponse(
                status_code=200,
                json_data=[
                    {"id": 1, "start": "2026-03-01 10:00:00"},
                    {"id": 2, "start": "2026-03-05 11:00:00"},
                ],
            ),
            FakeResponse(
                status_code=200,
                json_data=[
                    {"id": 3, "start": "2026-03-10 12:00:00"},
                ],
            ),
        ]

        result = self.client.get_appointments(
            start_date="2026-03-02T00:00:00",
            end_date="2026-03-07T23:59:59",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 2)

    @patch("app_core.client.requests.Session.request")
    def test_get_appointments_skips_invalid_dates(self, mock_request):
        mock_request.side_effect = [
            FakeResponse(
                status_code=200,
                json_data=[
                    {"id": 1, "start": "invalid-date"},
                    {"id": 2, "start": "2026-03-05 11:00:00"},
                ],
            ),
            FakeResponse(status_code=200, json_data=[]),
        ]

        result = self.client.get_appointments(
            start_date="2026-03-01T00:00:00",
            end_date="2026-03-10T23:59:59",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 2)

    @patch("app_core.client.time.sleep")
    @patch("app_core.client.requests.Session.request")
    def test_request_retries_on_500_then_succeeds(self, mock_request, mock_sleep):
        mock_request.side_effect = [
            FakeResponse(status_code=500, text="Server error"),
            FakeResponse(status_code=200, json_data=[{"id": 1}]),
        ]

        result = self.client.get_providers()

        self.assertEqual(result, [{"id": 1}])
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch("app_core.client.time.sleep")
    @patch("app_core.client.requests.Session.request")
    def test_request_retries_on_429_then_succeeds(self, mock_request, mock_sleep):
        mock_request.side_effect = [
            FakeResponse(status_code=429, text="Too Many Requests"),
            FakeResponse(status_code=200, json_data=[{"id": 1}]),
        ]

        result = self.client.get_providers()

        self.assertEqual(result, [{"id": 1}])
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch("app_core.client.time.sleep")
    @patch("app_core.client.requests.Session.request")
    def test_request_uses_retry_after_header_for_429(self, mock_request, mock_sleep):
        mock_request.side_effect = [
            FakeResponse(
                status_code=429,
                text="Too Many Requests",
                headers={"Retry-After": "3"},
            ),
            FakeResponse(status_code=200, json_data=[{"id": 1}]),
        ]

        result = self.client.get_providers()

        self.assertEqual(result, [{"id": 1}])
        mock_sleep.assert_called_once_with(3)

    @patch("app_core.client.time.sleep")
    @patch("app_core.client.requests.Session.request")
    def test_request_retries_on_timeout_then_succeeds(self, mock_request, mock_sleep):
        mock_request.side_effect = [
            requests.exceptions.Timeout("Request timed out"),
            FakeResponse(status_code=200, json_data=[{"id": 1}]),
        ]

        result = self.client.get_providers()

        self.assertEqual(result, [{"id": 1}])
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch("app_core.client.time.sleep")
    @patch("app_core.client.requests.Session.request")
    def test_request_retries_on_connection_error_then_succeeds(
        self, mock_request, mock_sleep
    ):
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            FakeResponse(status_code=200, json_data=[{"id": 1}]),
        ]

        result = self.client.get_providers()

        self.assertEqual(result, [{"id": 1}])
        self.assertEqual(mock_request.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch("app_core.client.requests.Session.request")
    def test_request_raises_on_400(self, mock_request):
        mock_request.return_value = FakeResponse(status_code=400, text="Bad Request")

        with self.assertRaises(Exception) as ctx:
            self.client.get_providers()

        self.assertIn("Client error 400", str(ctx.exception))

    @patch("app_core.client.time.sleep")
    @patch("app_core.client.requests.Session.request")
    def test_request_raises_after_max_retries_on_500(self, mock_request, mock_sleep):
        mock_request.side_effect = [
            FakeResponse(status_code=500, text="Server error"),
            FakeResponse(status_code=502, text="Bad gateway"),
            FakeResponse(status_code=503, text="Service unavailable"),
        ]

        with self.assertRaises(Exception) as ctx:
            self.client.get_providers()

        self.assertIn("Server error 503", str(ctx.exception))
        self.assertEqual(mock_request.call_count, 3)

    @patch("app_core.client.time.sleep")
    @patch("app_core.client.requests.Session.request")
    def test_request_raises_after_max_retries_on_network_error(
        self, mock_request, mock_sleep
    ):
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("fail-1"),
            requests.exceptions.ConnectionError("fail-2"),
            requests.exceptions.ConnectionError("fail-3"),
        ]

        with self.assertRaises(Exception) as ctx:
            self.client.get_providers()

        self.assertIn("Network error after 3 attempts", str(ctx.exception))
        self.assertEqual(mock_request.call_count, 3)

    @patch("app_core.client.requests.Session.request")
    def test_request_raises_on_invalid_json(self, mock_request):
        bad_response = Mock()
        bad_response.status_code = 200
        bad_response.text = "not-json"
        bad_response.headers = {}
        bad_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = bad_response

        with self.assertRaises(Exception) as ctx:
            self.client.get_providers()

        self.assertIn("Invalid JSON response", str(ctx.exception))

    @patch("app_core.client.requests.Session.request")
    def test_get_paginated_raises_if_response_is_not_list(self, mock_request):
        mock_request.return_value = FakeResponse(
            status_code=200,
            json_data={"results": []},
        )

        with self.assertRaises(Exception) as ctx:
            self.client.get_providers()

        self.assertIn("Expected list response", str(ctx.exception))

    @patch("app_core.client.requests.Session.request")
    def test_get_appointments_skips_missing_start(self, mock_request):
        mock_request.side_effect = [
            FakeResponse(
                status_code=200,
                json_data=[
                    {"id": 1},
                    {"id": 2, "start": "2026-03-05 11:00:00"},
                ],
            ),
            FakeResponse(status_code=200, json_data=[]),
        ]

        result = self.client.get_appointments(
            start_date="2026-03-01T00:00:00",
            end_date="2026-03-10T23:59:59",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 2)
