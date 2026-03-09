# Easy!Appointments API Discovery

External API used by this project:

- `http://localhost:8888/index.php/api/v1` (as provided in the task).
- As it was running from the docker, I had to use `http://host.docker.internal:8888/index.php/api/v1` for BookingSystemClient.

## Authentication

### Mechanism

- The client uses HTTP Basic Authentication (`Authorization: Basic ...`) via `requests.Session.auth = (username, password)`.

## Endpoints currently used

The integration currently pulls from these resources (GET):

- `/providers`
- `/customers`
- `/services`
- `/appointments`

These are called with Page Number Pagination:

- `GET /{resource}/?page={n}&length={m}`

## Pagination

### Parameters observed

- `page`: page number.
- `length`: page size. (default 20)

## Field naming

- It uses CamelCase

## Rate Limiting
- I got blocked after several tries, don't know the exact rate limiting logic