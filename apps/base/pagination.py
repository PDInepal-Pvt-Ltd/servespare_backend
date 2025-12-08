from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for API list endpoints.
    Provides configurable page size with query parameter support.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    page_size_query_description = 'Number of results to return per page.'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Format paginated response with metadata.
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': self.page_size,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


# class SmallResultsSetPagination(PageNumberPagination):
#     """
#     Small pagination class for mobile or compact list views.
#     Default 5 items per page.
#     """
#     page_size = 5
#     page_size_query_param = 'page_size'
#     max_page_size = 50
#     
#     def get_paginated_response(self, data):
#         """
#         Format paginated response with metadata.
#         """
#         return Response({
#             'count': self.page.paginator.count,
#             'next': self.get_next_link(),
#             'previous': self.get_previous_link(),
#             'page_size': self.page_size,
#             'total_pages': self.page.paginator.num_pages,
#             'current_page': self.page.number,
#             'results': data
#         })


# class LargeResultsSetPagination(PageNumberPagination):
#     """
#     Large pagination class for high-volume data endpoints.
#     Default 50 items per page.
#     """
#     page_size = 50
#     page_size_query_param = 'page_size'
#     max_page_size = 500
#     
#     def get_paginated_response(self, data):
#         """
#         Format paginated response with metadata.
#         """
#         return Response({
#             'count': self.page.paginator.count,
#             'next': self.get_next_link(),
#             'previous': self.get_previous_link(),
#             'page_size': self.page_size,
#             'total_pages': self.page.paginator.num_pages,
#             'current_page': self.page.number,
#             'results': data
#         })
