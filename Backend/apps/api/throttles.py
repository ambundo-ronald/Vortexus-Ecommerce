from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle


class IdentityRateThrottle(SimpleRateThrottle):
    identity_fields = ()

    def get_cache_key(self, request, view):
        identifier = self.get_ident(request)
        identity = self._resolve_identity(request)
        return self.cache_format % {'scope': self.scope, 'ident': f'{identifier}:{identity}'}

    def _resolve_identity(self, request) -> str:
        for field in self.identity_fields:
            value = self._lookup_value(request, field)
            if value not in (None, ''):
                return str(value).strip().lower()
        return 'anonymous'

    @staticmethod
    def _lookup_value(request, field):
        data = getattr(request, 'data', None)
        if hasattr(data, 'get'):
            value = data.get(field)
            if value not in (None, ''):
                return value

        query_params = getattr(request, 'query_params', None)
        if hasattr(query_params, 'get'):
            return query_params.get(field)
        return None


class AccountLoginIdentityThrottle(IdentityRateThrottle):
    scope = 'account_login_identity'
    identity_fields = ('identifier', 'email', 'username')


class AccountRegisterIdentityThrottle(IdentityRateThrottle):
    scope = 'account_register_identity'
    identity_fields = ('email',)


class EndpointScopedRateThrottle(ScopedRateThrottle):
    pass
