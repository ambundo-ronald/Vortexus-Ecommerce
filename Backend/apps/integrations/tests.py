from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase

from .erpnext_sync import ERPNextSyncService
from .models import IntegrationConnection, IntegrationMapping, SyncEventLog, SyncJob


class _FakeLines:
    def __init__(self, lines):
        self._lines = lines

    def select_related(self, *args):
        return self

    def order_by(self, *args):
        return self._lines


class _FakeERPNextClient:
    def __init__(self):
        self.created = []
        self.called = []

    def create_resource(self, doctype, data):
        self.created.append((doctype, data))
        return {'name': 'SO-VX-1001'}

    def call_method(self, method, data=None):
        self.called.append((method, data or {}))
        if method.endswith('create_sales_order'):
            return {'sales_order': 'SO-ECOM-1001', 'created': True}
        if method.endswith('create_sales_invoice'):
            return {'sales_invoice': 'SI-ECOM-1001', 'payment_entry': 'PE-ECOM-1001', 'created': True}
        if method.endswith('cancel_sales_order'):
            return {'sales_order': data['payload']['sales_order'], 'cancelled': [{'doctype': 'Sales Order', 'name': data['payload']['sales_order']}]}
        if method.endswith('create_credit_note'):
            return {'credit_note': 'CN-ECOM-1001', 'created': True}
        if method.endswith('upsert_customer'):
            return {'customer': 'CUST-ECOM-1', 'created': True}
        return {}


class ERPNextOrderExportTests(TestCase):
    def _connection(self):
        return IntegrationConnection.objects.create(
            name='ERPNext',
            connection_type=IntegrationConnection.TYPE_ERPNEXT,
            base_url='https://erp.example.com',
            api_key='key',
            api_secret='secret',
            default_company='Vortexus',
            metadata={'default_customer': 'Online Customer', 'export_orders': True},
        )

    def _order(self):
        line = SimpleNamespace(
            id=10,
            product_id=25,
            partner_sku='SKU-25',
            upc='UPC-25',
            quantity=2,
            unit_price_incl_tax=Decimal('150.00'),
            line_price_incl_tax=Decimal('300.00'),
            title='Industrial Pump',
        )
        return SimpleNamespace(
            id=99,
            number='VX-1001',
            currency='KES',
            guest_email='buyer@example.com',
            user=None,
            lines=_FakeLines([line]),
        )

    def test_export_order_creates_sales_order_mapping_and_log(self):
        connection = self._connection()
        IntegrationMapping.objects.create(
            connection=connection,
            entity_type=IntegrationMapping.ENTITY_PRODUCT,
            external_id='ERP-ITEM-25',
            internal_model='catalogue.Product',
            internal_id='25',
        )
        service = ERPNextSyncService(connection)
        service.client = _FakeERPNextClient()

        result = service.export_order(self._order())

        self.assertEqual(result['status'], 'exported')
        self.assertEqual(service.client.created[0][0], 'Sales Order')
        payload = service.client.created[0][1]
        self.assertEqual(payload['customer'], 'Online Customer')
        self.assertEqual(payload['items'][0]['item_code'], 'ERP-ITEM-25')
        self.assertEqual(payload['items'][0]['qty'], 2)
        self.assertTrue(IntegrationMapping.objects.filter(entity_type=IntegrationMapping.ENTITY_ORDER, external_id='SO-VX-1001').exists())
        self.assertTrue(SyncJob.objects.filter(job_type=SyncJob.TYPE_ORDERS_EXPORT, status=SyncJob.STATUS_SUCCEEDED).exists())
        self.assertTrue(SyncEventLog.objects.filter(entity_type='order', status=SyncEventLog.STATUS_PROCESSED).exists())

    def test_export_order_is_idempotent_when_mapping_exists(self):
        connection = self._connection()
        IntegrationMapping.objects.create(
            connection=connection,
            entity_type=IntegrationMapping.ENTITY_ORDER,
            external_id='SO-VX-1001',
            internal_model='order.Order',
            internal_id='99',
        )
        service = ERPNextSyncService(connection)
        service.client = _FakeERPNextClient()

        result = service.export_order(self._order())

        self.assertEqual(result['status'], 'already_exported')
        self.assertEqual(service.client.created, [])

    def test_bridge_order_export_calls_vortexus_app_method(self):
        connection = self._connection()
        connection.metadata = {'default_customer': 'Online Customer', 'export_orders': True, 'use_vortexus_bridge_app': True}
        connection.default_warehouse = 'Stores - VI'
        connection.save(update_fields=['metadata', 'default_warehouse'])
        IntegrationMapping.objects.create(
            connection=connection,
            entity_type=IntegrationMapping.ENTITY_PRODUCT,
            external_id='ERP-ITEM-25',
            internal_model='catalogue.Product',
            internal_id='25',
        )
        service = ERPNextSyncService(connection)
        service.client = _FakeERPNextClient()

        result = service.export_order(self._order())

        self.assertEqual(result['status'], 'exported')
        self.assertEqual(result['erpnext_sales_order'], 'SO-ECOM-1001')
        method, data = service.client.called[0]
        self.assertEqual(method, 'vortexus_ecommerce_integration.api.order.create_sales_order')
        payload = data['payload']
        self.assertEqual(payload['order_id'], '99')
        self.assertEqual(payload['order_number'], 'VX-1001')
        self.assertEqual(payload['warehouse'], 'Stores - VI')
        self.assertEqual(payload['items'][0]['item_code'], 'ERP-ITEM-25')

    def test_bridge_customer_sync_calls_vortexus_app_method(self):
        connection = self._connection()
        connection.metadata = {'sync_customers': True, 'use_vortexus_bridge_app': True}
        connection.save(update_fields=['metadata'])
        user = SimpleNamespace(
            id=7,
            email='buyer@example.com',
            first_name='Jane',
            last_name='Buyer',
            get_full_name=lambda: 'Jane Buyer',
            customer_profile=SimpleNamespace(phone='+254700000000', company='', country_code='KE'),
        )
        service = ERPNextSyncService(connection)
        service.client = _FakeERPNextClient()

        result = service.sync_customer(user)

        self.assertEqual(result['status'], 'synced')
        self.assertEqual(result['erpnext_customer'], 'CUST-ECOM-1')
        method, data = service.client.called[0]
        self.assertEqual(method, 'vortexus_ecommerce_integration.api.customer.upsert_customer')
        payload = data['payload']
        self.assertEqual(payload['user_id'], '7')
        self.assertEqual(payload['email'], 'buyer@example.com')
        self.assertEqual(payload['customer_group'], 'Ecommerce')

    def test_bridge_accounting_export_creates_invoice_and_payment_entry(self):
        connection = self._connection()
        connection.metadata = {'use_vortexus_bridge_app': True}
        connection.save(update_fields=['metadata'])
        IntegrationMapping.objects.create(
            connection=connection,
            entity_type=IntegrationMapping.ENTITY_ORDER,
            external_id='SO-ECOM-1001',
            internal_model='order.Order',
            internal_id='99',
        )
        order = self._order()
        payment = SimpleNamespace(
            reference='PAY-123',
            external_reference='PESA-123',
            provider='pesapal',
            method='pesapal',
            amount=Decimal('300.00'),
            paid_at=None,
            order=order,
        )
        service = ERPNextSyncService(connection)
        service.client = _FakeERPNextClient()

        result = service.export_paid_order_accounting(payment)

        self.assertEqual(result['status'], 'exported')
        self.assertEqual(result['sales_invoice'], 'SI-ECOM-1001')
        self.assertEqual(result['payment_entry'], 'PE-ECOM-1001')
        method, data = service.client.called[0]
        self.assertEqual(method, 'vortexus_ecommerce_integration.api.order.create_sales_invoice')
        payload = data['payload']
        self.assertEqual(payload['sales_order'], 'SO-ECOM-1001')
        self.assertEqual(payload['payment_reference'], 'PESA-123')
        mapping = IntegrationMapping.objects.get(entity_type=IntegrationMapping.ENTITY_ORDER, internal_id='99')
        self.assertEqual(mapping.metadata['sales_invoice'], 'SI-ECOM-1001')
        self.assertEqual(mapping.metadata['payment_entry'], 'PE-ECOM-1001')

    def test_bridge_cancellation_calls_vortexus_app_method(self):
        connection = self._connection()
        connection.metadata = {'use_vortexus_bridge_app': True}
        connection.save(update_fields=['metadata'])
        IntegrationMapping.objects.create(
            connection=connection,
            entity_type=IntegrationMapping.ENTITY_ORDER,
            external_id='SO-ECOM-1001',
            internal_model='order.Order',
            internal_id='99',
        )
        service = ERPNextSyncService(connection)
        service.client = _FakeERPNextClient()

        result = service.sync_order_cancellation(self._order(), reason='Customer requested cancellation.')

        self.assertEqual(result['status'], 'cancelled')
        method, data = service.client.called[0]
        self.assertEqual(method, 'vortexus_ecommerce_integration.api.order.cancel_sales_order')
        self.assertEqual(data['payload']['sales_order'], 'SO-ECOM-1001')
        self.assertEqual(data['payload']['reason'], 'Customer requested cancellation.')

    def test_bridge_refund_export_creates_credit_note(self):
        connection = self._connection()
        connection.metadata = {'use_vortexus_bridge_app': True}
        connection.save(update_fields=['metadata'])
        IntegrationMapping.objects.create(
            connection=connection,
            entity_type=IntegrationMapping.ENTITY_ORDER,
            external_id='SO-ECOM-1001',
            internal_model='order.Order',
            internal_id='99',
            metadata={'sales_invoice': 'SI-ECOM-1001', 'payment_entry': 'PE-ECOM-1001'},
        )
        order = self._order()
        payment = SimpleNamespace(
            reference='PAY-123',
            external_reference='PESA-123',
            provider='pesapal',
            method='pesapal',
            amount=Decimal('300.00'),
            order=order,
        )
        service = ERPNextSyncService(connection)
        service.client = _FakeERPNextClient()

        result = service.export_refund_credit_note(
            payment,
            refund_amount='100.00',
            reason='Returned item.',
            refund_reference='REFUND-1',
        )

        self.assertEqual(result['status'], 'exported')
        self.assertEqual(result['credit_note'], 'CN-ECOM-1001')
        method, data = service.client.called[0]
        self.assertEqual(method, 'vortexus_ecommerce_integration.api.order.create_credit_note')
        payload = data['payload']
        self.assertEqual(payload['sales_invoice'], 'SI-ECOM-1001')
        self.assertEqual(payload['refund_reference'], 'REFUND-1')
        mapping = IntegrationMapping.objects.get(entity_type=IntegrationMapping.ENTITY_ORDER, internal_id='99')
        self.assertEqual(mapping.metadata['refunds'][0]['credit_note'], 'CN-ECOM-1001')
