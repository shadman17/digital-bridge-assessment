import requests
import logging
import time


logger = logging.getLogger(__name__)


class BookingSystemClient:

    def __init__(
        self,
        base_url: str = "http://localhost:8888/index.php/api/v1",
        username: str = "admin",
        password: str = "admin123",
    ):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.timeout = 10

    def _request(self, method, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"

        retries = 3
        backoff = 1

        for attempt in range(retries):

            try:
                start = time.time()

                response = self.session.request(
                    method, url, params=params, timeout=self.timeout
                )

                elapsed = time.time() - start

                logger.info(
                    f"{method} {url} -> {response.status_code} ({elapsed:.2f}s)"
                )

                if response.status_code == 429:
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                if response.status_code >= 500:
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                if response.status_code >= 400:
                    raise Exception(
                        f"Client error {response.status_code}: {response.text}"
                    )

                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(f"Network error: {e}")
                time.sleep(backoff)
                backoff *= 2

        raise Exception("Max retries reached")

    def test_connection(self):
        try:
            self._request("GET", "providers")
            return True
        except Exception as e:
            logger.warning("Booking system connectivity check failed: %s", e)
            return False

    def get_providers(self):
        return self._request("GET", "providers")

    def get_customers(self):
        return self._request("GET", "customers")

    def get_services(self):
        return self._request("GET", "services")

    def get_appointments(self, start_date=None, end_date=None):

        appointments = self._request("GET", "appointments")

        if start_date or end_date:

            filtered = []

            for appt in appointments:

                date = appt.get("start")

                if start_date and date < start_date:
                    continue

                if end_date and date > end_date:
                    continue

                filtered.append(appt)

            return filtered

        return appointments
