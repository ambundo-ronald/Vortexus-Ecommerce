from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .health import readiness_payload


class LivenessAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({'status': 'ok', 'service': 'vortexus-backend'})


class ReadinessAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        payload = readiness_payload()
        status_code = 200 if payload['status'] in {'healthy', 'degraded'} else 503
        return JsonResponse(payload, status=status_code)
