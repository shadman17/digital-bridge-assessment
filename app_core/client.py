# The script was written originally by the Author. Chatgpt helped to get the paginated response!

import logging
import time
from datetime import datetime
from typing import Any

import requests


logger = logging.getLogger(__name__)


class BookingSystemClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8888/index.php/api/v1",
        username: str = "admin",
        password: str = "admin123",
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.timeout = 10
        self.page_size = 100

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        normalized_endpoint = endpoint.strip("/")
        url = f"{self.base_url}/{normalized_endpoint}/"
        retries = 3
        backoff = 1

        for attempt in range(1, retries + 1):
            start = time.time()
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=self.timeout,
                )
                elapsed = time.time() - start

                logger.info(
                    "%s %s params=%s -> %s (%.2fs)",
                    method,
                    url,
                    params,
                    response.status_code,
                    elapsed,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    sleep_for = (
                        int(retry_after)
                        if retry_after and retry_after.isdigit()
                        else backoff
                    )
                    logger.warning("Rate limited (429). Retrying in %ss...", sleep_for)
                    time.sleep(sleep_for)
                    backoff *= 2
                    continue

                if 500 <= response.status_code < 600:
                    if attempt == retries:
                        raise Exception(
                            f"Server error {response.status_code}: {response.text}"
                        )
                    logger.warning(
                        "Server error %s on %s. Retrying in %ss...",
                        response.status_code,
                        url,
                        backoff,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                if 400 <= response.status_code < 500:
                    raise Exception(
                        f"Client error {response.status_code}: {response.text}"
                    )

                try:
                    return response.json()
                except ValueError as exc:
                    raise Exception(
                        f"Invalid JSON response from {url}: {response.text}"
                    ) from exc

            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
            ) as e:
                elapsed = time.time() - start
                logger.warning(
                    "%s %s params=%s -> network error after %.2fs: %s",
                    method,
                    url,
                    params,
                    elapsed,
                    e,
                )
                if attempt == retries:
                    raise Exception(
                        f"Network error after {retries} attempts: {e}"
                    ) from e
                time.sleep(backoff)
                backoff *= 2

            except requests.exceptions.RequestException as e:
                elapsed = time.time() - start
                logger.warning(
                    "%s %s params=%s -> request error after %.2fs: %s",
                    method,
                    url,
                    params,
                    elapsed,
                    e,
                )
                if attempt == retries:
                    raise Exception(
                        f"Request failed after {retries} attempts: {e}"
                    ) from e
                time.sleep(backoff)
                backoff *= 2

        raise Exception("Max retries reached")

    def _get_paginated(
        self, endpoint: str, extra_params: dict[str, Any] | None = None
    ) -> list[dict]:
        page = 1
        results: list[dict] = []
        extra_params = extra_params or {}

        while True:
            params = {
                "page": page,
                "length": self.page_size,
                **extra_params,
            }
            data = self._request("GET", endpoint, params=params)

            if not isinstance(data, list):
                raise Exception(
                    f"Expected list response for {endpoint}, got: {type(data).__name__}"
                )

            results.extend(data)

            if len(data) < self.page_size:
                break

            page += 1

        return results

    def test_connection(self) -> bool:
        try:
            self._request("GET", "providers", params={"page": 1, "length": 1})
            return True
        except Exception as e:
            logger.warning("Booking system connectivity check failed: %s", e)
            return False

    def get_providers(self) -> list[dict]:
        return self._get_paginated("providers")

    def get_customers(self) -> list[dict]:
        return self._get_paginated("customers")

    def get_services(self) -> list[dict]:
        return self._get_paginated("services")

    def get_appointments(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        appointments = self._get_paginated("appointments")

        if not start_date and not end_date:
            return appointments

        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        filtered: list[dict] = []

        for appt in appointments:
            raw_start = appt.get("start")
            if not raw_start:
                continue

            try:
                appt_start = datetime.fromisoformat(raw_start.replace(" ", "T"))
            except ValueError:
                logger.warning(
                    "Skipping appointment with invalid start date: %s", raw_start
                )
                continue

            if start_dt and appt_start < start_dt:
                continue
            if end_dt and appt_start > end_dt:
                continue

            filtered.append(appt)

        return filtered
