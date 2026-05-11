from django.shortcuts import render
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .docs import build_api_docs


class ApiRootAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        base_url = request.build_absolute_uri('/api/v1').rstrip('/')
        return Response(
            {
                'name': 'Vortexus API',
                'version': 'v1',
                'docs': {
                    'html': f'{base_url}/docs/',
                    'json': f'{base_url}/docs.json',
                },
                'health': {
                    'live': f'{base_url}/health/live/',
                    'ready': f'{base_url}/health/ready/',
                },
                'storefront': {
                    'categories': f'{base_url}/catalog/categories/',
                    'products': f'{base_url}/catalog/products/',
                    'search': f'{base_url}/search/',
                    'basket': f'{base_url}/checkout/basket/',
                },
                'admin': {
                    'dashboard': f'{base_url}/admin/dashboard/',
                    'summary': f'{base_url}/admin/dashboard/summary/',
                    'products': f'{base_url}/admin/products/',
                    'orders': f'{base_url}/admin/orders/',
                },
            }
        )


class ApiDocsJsonAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(build_api_docs())


class ApiDocsHtmlAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return render(request, 'api/docs.html', {'docs': build_api_docs()})
