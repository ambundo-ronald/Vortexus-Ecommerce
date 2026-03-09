from urllib.parse import urlparse

from django.conf import settings
from opensearchpy import OpenSearch


def get_opensearch_client() -> OpenSearch:
    host = settings.OPENSEARCH['HOST']
    user = settings.OPENSEARCH.get('USER')
    password = settings.OPENSEARCH.get('PASSWORD')

    parsed = urlparse(host)
    if not parsed.hostname:
        raise ValueError('Invalid OPENSEARCH_HOST value')

    connection = {
        'host': parsed.hostname,
        'port': parsed.port or (443 if parsed.scheme == 'https' else 80),
        'scheme': parsed.scheme or 'http',
    }

    kwargs = {'hosts': [connection]}
    if user and password:
        kwargs['http_auth'] = (user, password)

    return OpenSearch(**kwargs)
