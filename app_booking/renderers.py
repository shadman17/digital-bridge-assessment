# AI-assisted snippet (ChatGPT) used for custom renderer
# Modified and integrated into the project by the author

from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        if data is None or (
            isinstance(data, dict) and {"data", "errors", "meta"}.issubset(data.keys())
        ):
            return super().render(data, accepted_media_type, renderer_context)

        if response is not None and response.status_code >= 400:
            data = {"data": None, "errors": self._build_errors(data), "meta": None}
        else:
            data = {"data": data, "errors": [], "meta": None}

        return super().render(data, accepted_media_type, renderer_context)

    def _build_errors(self, data):
        if isinstance(data, dict):
            if "detail" in data:
                detail = data["detail"]
                return [{"message": str(detail), "detail": detail}]

            errors = []
            for key, value in data.items():
                detail = value[0] if isinstance(value, list) and value else value
                errors.append(
                    {
                        "field": key,
                        "message": f"{key}: {detail}",
                        "detail": value,
                    }
                )
            return errors

        return [{"message": str(data), "detail": data}]
