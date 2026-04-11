from django.conf import settings


def build_api_docs() -> dict:
    base_url = '/api/v1'
    return {
        'title': 'Vortexus Backend API',
        'version': '1.0',
        'base_url': base_url,
        'summary': 'Backend API for industrial ecommerce covering catalog, search, checkout, payments, marketplace, and operations.',
        'authentication': {
            'session_auth': True,
            'csrf_required_for_mutations': True,
            'flow': [
                'GET /api/v1/account/csrf/ to obtain csrf_token',
                'Send session cookie with credentials on subsequent requests',
                'Include X-CSRFToken header on POST, PUT, PATCH, DELETE requests',
            ],
        },
        'response_contracts': {
            'errors': {
                'shape': {
                    'error': {
                        'code': 'validation_error',
                        'detail': 'Request validation failed.',
                        'status': 400,
                        'errors': {'field': ['message']},
                    }
                }
            },
            'throttled': {
                'shape': {
                    'error': {
                        'code': 'throttled',
                        'detail': 'Request was throttled. Expected available in 3600 seconds.',
                        'status': 429,
                        'retry_after_seconds': 3600,
                    }
                }
            },
        },
        'environment': {
            'async_enabled': bool(getattr(settings, 'ENABLE_ASYNC_TASKS', False)),
            'default_currency': settings.OSCAR_DEFAULT_CURRENCY,
            'payment_methods': [method['code'] for method in settings.PAYMENT_METHODS],
        },
        'sections': [
            {
                'name': 'Health',
                'endpoints': [
                    {
                        'method': 'GET',
                        'path': f'{base_url}/health/live/',
                        'auth': 'public',
                        'description': 'Simple liveness probe.',
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/health/ready/',
                        'auth': 'public',
                        'description': 'Readiness/dependency probe for database, cache, OpenSearch, and async mode.',
                    },
                ],
            },
            {
                'name': 'Account',
                'endpoints': [
                    {
                        'method': 'GET',
                        'path': f'{base_url}/account/csrf/',
                        'auth': 'public',
                        'description': 'Fetch CSRF token for session-authenticated API usage.',
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/account/register/',
                        'auth': 'public',
                        'description': 'Register a customer account and start a session.',
                        'request_example': {
                            'email': 'buyer@example.com',
                            'password': 'Testpass123!',
                            'password_confirm': 'Testpass123!',
                            'first_name': 'Ronald',
                            'last_name': 'Ambundo',
                            'country_code': 'KE',
                        },
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/account/login/',
                        'auth': 'public',
                        'description': 'Login by username or email via identifier field.',
                        'request_example': {
                            'identifier': 'buyer@example.com',
                            'password': 'Testpass123!',
                        },
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/account/logout/',
                        'auth': 'session',
                        'description': 'Terminate the current authenticated session.',
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/account/me/',
                        'auth': 'session',
                        'description': 'Fetch current customer profile and settings.',
                    },
                    {
                        'method': 'PATCH',
                        'path': f'{base_url}/account/me/',
                        'auth': 'session',
                        'description': 'Update account profile fields and notification settings.',
                        'request_example': {
                            'first_name': 'Ronald',
                            'phone': '+254700000000',
                            'company': 'Vortexus',
                            'preferred_currency': 'KES',
                        },
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/account/password/',
                        'auth': 'session',
                        'description': 'Change the authenticated user password.',
                        'request_example': {
                            'current_password': 'OldPass123!',
                            'new_password': 'NewPass123!',
                            'new_password_confirm': 'NewPass123!',
                        },
                    },
                ],
            },
            {
                'name': 'Catalog And Search',
                'endpoints': [
                    {
                        'method': 'GET',
                        'path': f'{base_url}/catalog/categories/',
                        'auth': 'public',
                        'description': 'List top-level categories with immediate child categories.',
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/catalog/products/',
                        'auth': 'public',
                        'description': 'List/search public products with filters and pagination.',
                        'query_params': ['q', 'category', 'in_stock', 'min_price', 'max_price', 'sort_by', 'page', 'page_size'],
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/catalog/products/',
                        'auth': 'staff session',
                        'description': 'Create a catalog product.',
                        'request_example': {
                            'upc': 'PUMP-001',
                            'title': '3HP Borehole Pump',
                            'description': 'Industrial submersible pump',
                            'is_public': True,
                            'partner_name': 'Default Partner',
                            'price': '499.99',
                            'currency': 'USD',
                            'num_in_stock': 12,
                        },
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/catalog/products/<product_id>/',
                        'auth': 'public',
                        'description': 'Fetch product detail and related products.',
                    },
                    {
                        'method': 'PATCH',
                        'path': f'{base_url}/catalog/products/<product_id>/',
                        'auth': 'staff session',
                        'description': 'Partially update a catalog product.',
                    },
                    {
                        'method': 'DELETE',
                        'path': f'{base_url}/catalog/products/<product_id>/',
                        'auth': 'staff session',
                        'description': 'Delete a catalog product.',
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/search/',
                        'auth': 'public',
                        'description': 'Text search over products.',
                        'query_params': ['q', 'category', 'in_stock', 'page', 'page_size'],
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/search/image/',
                        'auth': 'public',
                        'description': 'Multipart image similarity search.',
                        'content_type': 'multipart/form-data',
                        'form_fields': ['image', 'category', 'top_k'],
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/recommendations/',
                        'auth': 'public',
                        'description': 'Get recommendations by product_id, user_id, or trending fallback.',
                        'query_params': ['product_id', 'user_id', 'limit'],
                    },
                ],
            },
            {
                'name': 'Checkout',
                'endpoints': [
                    {
                        'method': 'GET',
                        'path': f'{base_url}/checkout/basket/',
                        'auth': 'public session',
                        'description': 'Fetch current basket, totals, and reservation-aware basket lines.',
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/checkout/basket/items/',
                        'auth': 'public session',
                        'description': 'Add an item to the basket.',
                        'request_example': {'product_id': 1, 'quantity': 2},
                    },
                    {
                        'method': 'PATCH',
                        'path': f'{base_url}/checkout/basket/items/<line_id>/',
                        'auth': 'public session',
                        'description': 'Update basket line quantity.',
                        'request_example': {'quantity': 3},
                    },
                    {
                        'method': 'PUT',
                        'path': f'{base_url}/checkout/shipping/address/',
                        'auth': 'public session',
                        'description': 'Save shipping address for the active checkout session.',
                        'request_example': {
                            'first_name': 'Ronald',
                            'last_name': 'Ambundo',
                            'line1': 'Westlands Road',
                            'line4': 'Nairobi',
                            'country_code': 'KE',
                            'phone_number': '+254700000000',
                        },
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/checkout/shipping/select/',
                        'auth': 'public session',
                        'description': 'Select one available shipping method.',
                        'request_example': {'method_code': 'standard-freight'},
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/checkout/shipping/',
                        'auth': 'public session',
                        'description': 'Get checkout basket, address, methods, shipping metrics, and totals.',
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/checkout/orders/',
                        'auth': 'public session',
                        'description': 'Place an order from the current basket.',
                        'request_example': {
                            'guest_email': 'buyer@example.com',
                            'payment_reference': 'PAY-ABC123DEF456',
                        },
                    },
                ],
            },
            {
                'name': 'Payments',
                'endpoints': [
                    {
                        'method': 'GET',
                        'path': f'{base_url}/checkout/payments/methods/',
                        'auth': 'public session',
                        'description': 'List supported payment methods and requirements.',
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/checkout/payments/',
                        'auth': 'public session',
                        'description': 'Initialize a generic payment session.',
                        'request_example': {'method': 'cash_on_delivery', 'payer_email': 'buyer@example.com'},
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/checkout/payments/mpesa/initiate/',
                        'auth': 'public session',
                        'description': 'Initialize M-Pesa payment for the current basket.',
                        'request_example': {'phone_number': '+254700000011', 'payer_email': 'buyer@example.com'},
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/checkout/payments/airtel-money/initiate/',
                        'auth': 'public session',
                        'description': 'Initialize Airtel Money payment for the current basket.',
                        'request_example': {'phone_number': '+254700000011', 'payer_email': 'buyer@example.com'},
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/checkout/payments/cards/initiate/',
                        'auth': 'public session',
                        'description': 'Initialize credit/debit card payment using tokenized card data.',
                        'request_example': {
                            'method': 'credit_card',
                            'payer_email': 'buyer@example.com',
                            'payment_token': 'tok_test_visa',
                            'card_brand': 'visa',
                            'last4': '4242',
                            'expiry_month': 12,
                            'expiry_year': 2030,
                            'holder_name': 'Card Buyer',
                        },
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/checkout/payments/<reference>/',
                        'auth': 'public session',
                        'description': 'Fetch payment session state.',
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/checkout/payments/<reference>/confirm/',
                        'auth': 'public session',
                        'description': 'Confirm payment session for sandbox/testing callbacks.',
                        'request_example': {'success': True, 'external_reference': 'TXN-123'},
                    },
                ],
            },
            {
                'name': 'Orders',
                'endpoints': [
                    {
                        'method': 'GET',
                        'path': f'{base_url}/account/orders/',
                        'auth': 'session',
                        'description': 'List current user orders.',
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/account/orders/<order_number>/',
                        'auth': 'session',
                        'description': 'Fetch current user order detail.',
                    },
                    {
                        'method': 'GET',
                        'path': f'{base_url}/account/orders/<order_number>/status/',
                        'auth': 'session',
                        'description': 'Fetch order status timeline.',
                    },
                    {
                        'method': 'POST',
                        'path': f'{base_url}/account/orders/<order_number>/reorder/',
                        'auth': 'session',
                        'description': 'Re-add previous order items to the active basket.',
                    },
                ],
            },
            {
                'name': 'Wishlist And Reviews',
                'endpoints': [
                    {'method': 'GET', 'path': f'{base_url}/account/wishlist/', 'auth': 'session', 'description': 'Get default saved-items wishlist.'},
                    {'method': 'POST', 'path': f'{base_url}/account/wishlist/items/', 'auth': 'session', 'description': 'Add product to default wishlist.', 'request_example': {'product_id': 1}},
                    {'method': 'DELETE', 'path': f'{base_url}/account/wishlist/items/<product_id>/', 'auth': 'session', 'description': 'Remove product from default wishlist.'},
                    {'method': 'POST', 'path': f'{base_url}/account/wishlist/status/', 'auth': 'session', 'description': 'Check wishlist membership for product ids.', 'request_example': {'product_ids': [1, 2, 3]}},
                    {'method': 'GET', 'path': f'{base_url}/account/wishlists/', 'auth': 'session', 'description': 'List named wishlists.'},
                    {'method': 'POST', 'path': f'{base_url}/account/wishlists/', 'auth': 'session', 'description': 'Create named wishlist.', 'request_example': {'name': 'Project Phase 1'}},
                    {'method': 'GET', 'path': f'{base_url}/catalog/products/<product_id>/reviews/', 'auth': 'public', 'description': 'List public reviews for a product.'},
                    {'method': 'POST', 'path': f'{base_url}/catalog/products/<product_id>/reviews/', 'auth': 'session', 'description': 'Create product review.', 'request_example': {'title': 'Reliable pump', 'score': 5, 'body': 'Performed well on site.'}},
                    {'method': 'GET', 'path': f'{base_url}/account/reviews/', 'auth': 'session', 'description': 'List current user reviews.'},
                ],
            },
            {
                'name': 'Supplier Marketplace',
                'endpoints': [
                    {'method': 'GET', 'path': f'{base_url}/supplier/profile/', 'auth': 'session', 'description': 'Fetch supplier profile/applicability state.'},
                    {'method': 'POST', 'path': f'{base_url}/supplier/profile/', 'auth': 'session', 'description': 'Create supplier profile application.'},
                    {'method': 'PATCH', 'path': f'{base_url}/supplier/profile/', 'auth': 'session', 'description': 'Update supplier profile.'},
                    {'method': 'GET', 'path': f'{base_url}/supplier/dashboard/', 'auth': 'supplier session', 'description': 'Fetch supplier dashboard metrics.'},
                    {'method': 'GET', 'path': f'{base_url}/supplier/orders/', 'auth': 'supplier session', 'description': 'List supplier-visible order groups.'},
                    {'method': 'GET', 'path': f'{base_url}/supplier/orders/<order_number>/', 'auth': 'supplier session', 'description': 'Fetch supplier order detail.'},
                    {'method': 'POST', 'path': f'{base_url}/supplier/orders/<order_number>/lines/<line_id>/status/', 'auth': 'approved supplier session', 'description': 'Update supplier-owned line fulfillment status.', 'request_example': {'status': 'shipped', 'tracking_reference': 'TRK-1001'}},
                    {'method': 'GET', 'path': f'{base_url}/supplier/products/', 'auth': 'supplier session', 'description': 'List supplier-owned offers/products.'},
                    {'method': 'POST', 'path': f'{base_url}/supplier/products/', 'auth': 'approved supplier session', 'description': 'Create supplier-owned product/offer.'},
                ],
            },
            {
                'name': 'Admin',
                'endpoints': [
                    {'method': 'GET', 'path': f'{base_url}/admin/suppliers/', 'auth': 'staff session', 'description': 'List supplier profiles for approval workflow.'},
                    {'method': 'PATCH', 'path': f'{base_url}/admin/suppliers/<supplier_id>/', 'auth': 'staff session', 'description': 'Approve or suspend supplier profile.', 'request_example': {'status': 'approved'}},
                    {'method': 'GET', 'path': f'{base_url}/admin/audit-logs/', 'auth': 'staff session', 'description': 'List audit log entries with filtering.'},
                    {'method': 'GET', 'path': f'{base_url}/admin/audit-logs/<audit_log_id>/', 'auth': 'staff session', 'description': 'Fetch single audit log record.'},
                    {'method': 'GET', 'path': f'{base_url}/admin/users/', 'auth': 'staff session', 'description': 'List users with search, role/status filtering, pagination, and summary metrics.'},
                    {'method': 'POST', 'path': f'{base_url}/admin/users/', 'auth': 'staff session', 'description': 'Create a customer, staff, or admin account.', 'request_example': {'email': 'operator@example.com', 'password': 'TempPass123!', 'first_name': 'Ops', 'last_name': 'User', 'role': 'staff', 'status': 'active'}},
                    {'method': 'GET', 'path': f'{base_url}/admin/users/<user_id>/', 'auth': 'staff session', 'description': 'Fetch admin user detail including profile, access flags, and supplier state.'},
                    {'method': 'PATCH', 'path': f'{base_url}/admin/users/<user_id>/', 'auth': 'staff session', 'description': 'Update user profile basics, access role, status, or password.', 'request_example': {'status': 'suspended', 'company': 'SiteWorks Ltd'}},
                    {'method': 'GET', 'path': f'{base_url}/admin/orders/', 'auth': 'staff session', 'description': 'List admin-visible orders with search, status filtering, pagination, and summary metrics.'},
                    {'method': 'GET', 'path': f'{base_url}/admin/orders/<order_id>/', 'auth': 'staff session', 'description': 'Fetch admin order detail including customer, totals, tracking, and supplier groups.'},
                    {'method': 'PATCH', 'path': f'{base_url}/admin/orders/<order_id>/status/', 'auth': 'staff session', 'description': 'Update order workflow status, add tracking reference, and record an internal note.', 'request_example': {'status': 'Shipped', 'tracking_reference': 'TRK-1001', 'note': 'Released from warehouse'}} ,
                    {'method': 'GET', 'path': f'{base_url}/admin/integrations/', 'auth': 'staff session', 'description': 'List ERP/integration connections.'},
                    {'method': 'POST', 'path': f'{base_url}/admin/integrations/', 'auth': 'staff session', 'description': 'Create an ERP/integration connection. Prefer credential_source=env with secret_env_prefix for production.', 'request_example': {'name': 'ERPNext Norwa', 'connection_type': 'erpnext', 'base_url': 'https://erp.example.com', 'auth_type': 'token', 'credential_source': 'env', 'secret_env_prefix': 'ERPNEXT_NORWA'}},
                    {'method': 'PATCH', 'path': f'{base_url}/admin/integrations/<connection_id>/', 'auth': 'staff session', 'description': 'Update an ERP/integration connection, including switching between database-backed and environment-backed credentials.'},
                    {'method': 'POST', 'path': f'{base_url}/admin/integrations/<connection_id>/erpnext/test/', 'auth': 'staff session', 'description': 'Test an ERPNext connection.'},
                    {'method': 'GET', 'path': f'{base_url}/admin/integrations/<connection_id>/erpnext/preview/?resource=items', 'auth': 'staff session', 'description': 'Preview ERPNext items, stock, or prices.'},
                    {'method': 'POST', 'path': f'{base_url}/admin/integrations/<connection_id>/erpnext/import/', 'auth': 'staff session', 'description': 'Import ERPNext item groups and items into categories and catalog.'},
                    {'method': 'POST', 'path': f'{base_url}/admin/integrations/<connection_id>/erpnext/stock-sync/', 'auth': 'staff session', 'description': 'Sync ERPNext stock balances into stock records.'},
                    {'method': 'GET', 'path': f'{base_url}/admin/integrations/<connection_id>/logs/', 'auth': 'staff session', 'description': 'List recent integration logs.'},
                ],
            },
            {
                'name': 'Quotes',
                'endpoints': [
                    {
                        'method': 'POST',
                        'path': f'{base_url}/quotes/',
                        'auth': 'public',
                        'description': 'Submit a quote request with optional product reference.',
                        'request_example': {
                            'name': 'Project Engineer',
                            'email': 'engineer@example.com',
                            'phone': '+254700000000',
                            'company': 'SiteWorks Ltd',
                            'message': 'Need pricing for borehole pump + pressure tank.',
                            'product_id': 1,
                        },
                    }
                ],
            },
        ],
    }
