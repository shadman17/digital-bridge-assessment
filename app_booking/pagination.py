from django.core.paginator import Paginator
from rest_framework.response import Response


class EnvelopePaginator:
    def __init__(self, request):
        self.request = request

    def get_page_number(self):
        return int(self.request.query_params.get("page", 1))

    def get_page_size(self):
        return int(self.request.query_params.get("page_size", 10))

    def get_paginated_response(self, queryset, serializer_class):
        page_number = self.get_page_number()
        page_size = self.get_page_size()

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        return Response(
            {
                "data": serializer_class(page.object_list, many=True).data,
                "errors": [],
                "meta": {
                    "page": page.number,
                    "total_pages": paginator.num_pages,
                    "total_count": paginator.count,
                },
            }
        )
