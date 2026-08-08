from django.conf import settings
from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.views import APIView

from apps.integrations.google_merchant_feed import (
    build_google_merchant_feed_rows,
    render_google_merchant_feed_csv,
)


class GoogleMerchantProductFeedAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        token = getattr(settings, 'GOOGLE_MERCHANT_FEED_TOKEN', '')
        if token and request.query_params.get('token') != token:
            return HttpResponse('Forbidden', status=403, content_type='text/plain')

        country_code = (request.query_params.get('country') or 'KE').upper()[:2]
        rows = build_google_merchant_feed_rows(tax_country_code=country_code)
        response = HttpResponse(render_google_merchant_feed_csv(rows), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'inline; filename="google-merchant-products.csv"'
        response['Cache-Control'] = 'public, max-age=900'
        return response
