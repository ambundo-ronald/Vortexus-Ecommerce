from django.shortcuts import render
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .docs import build_api_docs


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
