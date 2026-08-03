import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.apps import apps
from apps.accounting.models import (
    AccountingAccount,
    AccountingBankTransaction,
    AccountingJournalEntry,
    AccountingJournalLine,
    AccountingPaymentLedgerEntry,
    AccountingReconciliationAllocation,
)
from apps.accounting.services import (
    cancel_bank_transaction,
    ensure_default_chart_of_accounts,
    reconcile_bank_transaction,
    submit_journal_entry,
    trial_balance,
)
from apps.payments.models import PaymentSession

from .account_manager_scope import can_access_finance_data


class ManualJournalLineSerializer(serializers.Serializer):
    account_code = serializers.CharField(max_length=32)
    debit = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, min_value=0)
    credit = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, min_value=0)
    party_type = serializers.CharField(required=False, allow_blank=True, max_length=32)
    party_id = serializers.CharField(required=False, allow_blank=True, max_length=64)
    party_name = serializers.CharField(required=False, allow_blank=True, max_length=160)
    remarks = serializers.CharField(required=False, allow_blank=True, max_length=255)


class ManualJournalEntrySerializer(serializers.Serializer):
    reference = serializers.CharField(required=False, allow_blank=True, max_length=80)
    posting_date = serializers.DateField(required=False)
    memo = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    currency = serializers.CharField(required=False, allow_blank=True, max_length=12)
    lines = ManualJournalLineSerializer(many=True, allow_empty=False)

    def validate_lines(self, value):
        total_debit = sum((line.get('debit') or Decimal('0')) for line in value)
        total_credit = sum((line.get('credit') or Decimal('0')) for line in value)
        if total_debit != total_credit:
            raise serializers.ValidationError('Debit and credit totals must match.')
        if total_debit <= 0:
            raise serializers.ValidationError('Journal entry amount must be greater than zero.')
        for line in value:
            if line.get('debit') and line.get('credit'):
                raise serializers.ValidationError('A line cannot have both debit and credit.')
        return value


class BankTransactionSerializer(serializers.Serializer):
    transaction_date = serializers.DateField(required=False)
    bank_account = serializers.CharField(required=False, allow_blank=True, max_length=160)
    provider = serializers.CharField(required=False, allow_blank=True, max_length=64)
    reference_number = serializers.CharField(required=False, allow_blank=True, max_length=128)
    transaction_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
    deposit = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, min_value=0)
    withdrawal = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, min_value=0)
    currency = serializers.CharField(required=False, allow_blank=True, max_length=12)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        deposit = attrs.get('deposit') or Decimal('0')
        withdrawal = attrs.get('withdrawal') or Decimal('0')
        if deposit <= 0 and withdrawal <= 0:
            raise serializers.ValidationError('Enter either a deposit or withdrawal amount.')
        if deposit and withdrawal:
            raise serializers.ValidationError('A bank transaction cannot have both deposit and withdrawal.')
        return attrs


class ReconcileBankTransactionSerializer(serializers.Serializer):
    payment_reference = serializers.CharField(required=False, allow_blank=True, max_length=64)
    order_number = serializers.CharField(required=False, allow_blank=True, max_length=128)
    allocated_amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, min_value=0)
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class CancelBankTransactionSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class BankTransactionCsvImportSerializer(serializers.Serializer):
    file = serializers.FileField()
    provider = serializers.CharField(required=False, allow_blank=True, max_length=64)
    bank_account = serializers.CharField(required=False, allow_blank=True, max_length=160)
    currency = serializers.CharField(required=False, allow_blank=True, max_length=12)


def _pagination(request, queryset, default_page_size=50):
    page = max(1, int(request.query_params.get('page') or 1))
    page_size = min(200, max(1, int(request.query_params.get('page_size') or default_page_size)))
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    return page_obj, {
        'page': page_obj.number,
        'page_size': page_size,
        'num_pages': paginator.num_pages,
        'count': paginator.count,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    }


def _require_finance(request):
    return can_access_finance_data(request.user)


def _account_payload(account):
    return {
        'id': account.id,
        'code': account.code,
        'name': account.name,
        'account_type': account.account_type,
        'parent_id': account.parent_id,
        'parent_code': account.parent.code if account.parent_id else '',
        'is_group': account.is_group,
        'currency': account.currency,
        'is_active': account.is_active,
    }


def _journal_line_payload(line):
    return {
        'id': line.id,
        'account_id': line.account_id,
        'account_code': line.account.code,
        'account_name': line.account.name,
        'debit': float(line.debit),
        'credit': float(line.credit),
        'currency': line.currency,
        'party_type': line.party_type,
        'party_id': line.party_id,
        'party_name': line.party_name,
        'against_account': line.against_account,
        'remarks': line.remarks,
    }


def _journal_payload(entry, *, include_lines=False):
    payload = {
        'id': entry.id,
        'reference': entry.reference,
        'entry_type': entry.entry_type,
        'status': entry.status,
        'posting_date': entry.posting_date,
        'memo': entry.memo,
        'source_type': entry.source_content_type.model if entry.source_content_type_id else '',
        'source_object_id': entry.source_object_id,
        'total_debit': float(entry.total_debit),
        'total_credit': float(entry.total_credit),
        'currency': entry.currency,
        'submitted_by_email': entry.submitted_by.email if entry.submitted_by_id else '',
        'submitted_at': entry.submitted_at,
        'created_at': entry.created_at,
        'updated_at': entry.updated_at,
    }
    if include_lines:
        payload['lines'] = [_journal_line_payload(line) for line in entry.lines.select_related('account').all()]
    return payload


def _payment_ledger_payload(row):
    return {
        'id': row.id,
        'account_type': row.account_type,
        'account_code': row.account.code,
        'account_name': row.account.name,
        'party_type': row.party_type,
        'party_id': row.party_id,
        'party_name': row.party_name,
        'voucher_type': row.voucher_type,
        'voucher_no': row.voucher_no,
        'against_voucher_type': row.against_voucher_type,
        'against_voucher_no': row.against_voucher_no,
        'amount': float(row.amount),
        'currency': row.currency,
        'posting_date': row.posting_date,
        'journal_reference': row.journal_entry.reference if row.journal_entry_id else '',
        'created_at': row.created_at,
    }


def _bank_transaction_payload(row):
    return {
        'id': row.id,
        'transaction_date': row.transaction_date,
        'bank_account': row.bank_account,
        'provider': row.provider,
        'reference_number': row.reference_number,
        'transaction_id': row.transaction_id,
        'description': row.description,
        'deposit': float(row.deposit),
        'withdrawal': float(row.withdrawal),
        'amount': float(row.amount),
        'currency': row.currency,
        'status': row.status,
        'source': row.source,
        'matched_payment_reference': row.matched_payment_session.reference if row.matched_payment_session_id else '',
        'matched_order_number': row.matched_order.number if row.matched_order_id else '',
        'clearance_date': row.clearance_date,
        'notes': row.notes,
        'reconciled_by_email': row.reconciled_by.email if row.reconciled_by_id else '',
        'reconciled_at': row.reconciled_at,
        'created_at': row.created_at,
        'updated_at': row.updated_at,
    }


def _allocation_payload(row):
    return {
        'id': row.id,
        'bank_transaction_id': row.bank_transaction_id,
        'payment_reference': row.payment_session.reference if row.payment_session_id else '',
        'order_number': row.order.number if row.order_id else '',
        'journal_reference': row.journal_entry.reference if row.journal_entry_id else '',
        'allocated_amount': float(row.allocated_amount),
        'currency': row.currency,
        'status': row.status,
        'note': row.note,
        'reconciled_by_email': row.reconciled_by.email if row.reconciled_by_id else '',
        'reconciled_at': row.reconciled_at,
        'created_at': row.created_at,
    }


def _payment_candidate_payload(payment):
    return {
        'id': payment.id,
        'reference': payment.reference,
        'status': payment.status,
        'method': payment.method,
        'provider': payment.provider,
        'amount': float(payment.amount),
        'currency': payment.currency,
        'payer_email': payment.payer_email or (payment.user.email if payment.user_id else ''),
        'payer_phone': payment.payer_phone,
        'external_reference': payment.external_reference,
        'order_number': payment.order.number if payment.order_id else '',
        'created_at': payment.created_at,
        'paid_at': payment.paid_at,
    }


def _order_candidate_payload(order):
    return {
        'id': order.id,
        'number': order.number,
        'status': getattr(order, 'status', ''),
        'total_incl_tax': float(getattr(order, 'total_incl_tax', 0) or 0),
        'currency': getattr(order, 'currency', 'KES') or 'KES',
        'email': getattr(order, 'email', '') or getattr(getattr(order, 'user', None), 'email', ''),
        'date_placed': getattr(order, 'date_placed', None),
    }


CSV_HEADER_ALIASES = {
    'date': {'date', 'transaction date', 'completion time', 'paid in date', 'receipt date', 'time', 'timestamp'},
    'reference': {'reference', 'receipt no', 'receipt number', 'transaction id', 'transaction code', 'mpesa receipt', 'tracking id', 'confirmation code'},
    'description': {'description', 'details', 'narration', 'particulars', 'name', 'customer', 'transaction details'},
    'deposit': {'deposit', 'paid in', 'credit', 'money in', 'amount received', 'receipt amount', 'in'},
    'withdrawal': {'withdrawal', 'paid out', 'debit', 'money out', 'amount paid', 'out'},
    'amount': {'amount', 'transaction amount', 'total amount', 'value'},
    'currency': {'currency'},
}


def _normalize_header(value):
    return re.sub(r'[^a-z0-9]+', ' ', str(value or '').strip().lower()).strip()


def _csv_get(row, key):
    aliases = CSV_HEADER_ALIASES[key]
    for raw_key, value in row.items():
        if _normalize_header(raw_key) in aliases:
            return str(value or '').strip()
    return ''


def _parse_csv_decimal(value):
    cleaned = re.sub(r'[^\d\-.]', '', str(value or '').replace(',', ''))
    if not cleaned or cleaned in {'-', '.', '-.'}:
        return Decimal('0.00')
    try:
        return Decimal(cleaned).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return Decimal('0.00')


def _parse_csv_date(value):
    raw = str(value or '').strip()
    if not raw:
        return timezone.localdate()
    normalized = raw.split('+')[0].strip()
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%d/%m/%Y %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%d-%m-%Y %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(normalized[:19], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return timezone.localdate()


def _transaction_exists(*, transaction_id='', reference_number='', provider='', amount=None, transaction_date=None):
    queryset = AccountingBankTransaction.objects.all()
    if transaction_id and queryset.filter(transaction_id=transaction_id).exists():
        return True
    if not reference_number:
        return False
    duplicate_query = queryset.filter(reference_number=reference_number)
    if provider:
        duplicate_query = duplicate_query.filter(provider=provider)
    if amount is not None:
        duplicate_query = duplicate_query.filter(deposit=amount if amount > 0 else Decimal('0.00'))
    if transaction_date:
        duplicate_query = duplicate_query.filter(transaction_date=transaction_date)
    return duplicate_query.exists()


class AdminAccountingAccountCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        ensure_default_chart_of_accounts()
        queryset = AccountingAccount.objects.select_related('parent').order_by('code')
        search = (request.query_params.get('q') or '').strip()
        account_type = (request.query_params.get('account_type') or '').strip()
        if search:
            queryset = queryset.filter(Q(code__icontains=search) | Q(name__icontains=search))
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        return Response({'results': [_account_payload(account) for account in queryset]})


class AdminAccountingJournalCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        queryset = AccountingJournalEntry.objects.select_related('source_content_type', 'submitted_by').order_by('-posting_date', '-id')
        search = (request.query_params.get('q') or '').strip()
        entry_type = (request.query_params.get('entry_type') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        if search:
            queryset = queryset.filter(Q(reference__icontains=search) | Q(memo__icontains=search) | Q(source_object_id__icontains=search))
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        page_obj, pagination = _pagination(request, queryset)
        return Response({'results': [_journal_payload(entry) for entry in page_obj.object_list], 'pagination': pagination})

    def post(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ManualJournalEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ensure_default_chart_of_accounts()
        lines = []
        for line in data['lines']:
            account = AccountingAccount.objects.filter(code=line['account_code']).first()
            if not account:
                return Response({'detail': f"Account {line['account_code']} was not found."}, status=status.HTTP_400_BAD_REQUEST)
            lines.append({
                'account': account,
                'debit': line.get('debit') or Decimal('0'),
                'credit': line.get('credit') or Decimal('0'),
                'party_type': line.get('party_type', ''),
                'party_id': line.get('party_id', ''),
                'party_name': line.get('party_name', ''),
                'remarks': line.get('remarks', ''),
            })
        reference = data.get('reference') or f"JE-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        entry = submit_journal_entry(
            reference=reference,
            entry_type=AccountingJournalEntry.TYPE_MANUAL,
            lines=lines,
            memo=data.get('memo', ''),
            currency=data.get('currency') or 'KES',
            user=request.user,
            posting_date=data.get('posting_date') or timezone.localdate(),
        )
        return Response({'journal_entry': _journal_payload(entry, include_lines=True)}, status=status.HTTP_201_CREATED)


class AdminAccountingJournalDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, journal_id: int):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        entry = AccountingJournalEntry.objects.select_related('source_content_type', 'submitted_by').prefetch_related('lines__account').get(pk=journal_id)
        return Response({'journal_entry': _journal_payload(entry, include_lines=True)})


class AdminAccountingGeneralLedgerAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        queryset = AccountingJournalLine.objects.select_related('journal_entry', 'account').filter(journal_entry__status=AccountingJournalEntry.STATUS_SUBMITTED)
        search = (request.query_params.get('q') or '').strip()
        account_code = (request.query_params.get('account_code') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(journal_entry__reference__icontains=search)
                | Q(account__code__icontains=search)
                | Q(account__name__icontains=search)
                | Q(party_name__icontains=search)
                | Q(remarks__icontains=search)
            )
        if account_code:
            queryset = queryset.filter(account__code=account_code)
        queryset = queryset.order_by('-journal_entry__posting_date', '-journal_entry_id', '-id')
        page_obj, pagination = _pagination(request, queryset)
        results = []
        for line in page_obj.object_list:
            item = _journal_line_payload(line)
            item.update({
                'journal_id': line.journal_entry_id,
                'journal_reference': line.journal_entry.reference,
                'entry_type': line.journal_entry.entry_type,
                'posting_date': line.journal_entry.posting_date,
                'memo': line.journal_entry.memo,
            })
            results.append(item)
        totals = queryset.aggregate(debit=Sum('debit'), credit=Sum('credit'))
        return Response({
            'results': results,
            'pagination': pagination,
            'summary': {
                'debit': float(totals.get('debit') or 0),
                'credit': float(totals.get('credit') or 0),
            },
        })


class AdminAccountingPaymentLedgerAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        queryset = AccountingPaymentLedgerEntry.objects.select_related('account', 'journal_entry').order_by('-posting_date', '-id')
        search = (request.query_params.get('q') or '').strip()
        account_type = (request.query_params.get('account_type') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(party_id__icontains=search)
                | Q(party_name__icontains=search)
                | Q(voucher_no__icontains=search)
                | Q(against_voucher_no__icontains=search)
            )
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        page_obj, pagination = _pagination(request, queryset)
        return Response({'results': [_payment_ledger_payload(row) for row in page_obj.object_list], 'pagination': pagination})


class AdminAccountingTrialBalanceAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        ensure_default_chart_of_accounts()
        rows = trial_balance(currency=(request.query_params.get('currency') or 'KES').strip() or 'KES')
        totals = {
            'debit': float(sum(row['debit'] for row in rows)),
            'credit': float(sum(row['credit'] for row in rows)),
            'balance': float(sum(row['balance'] for row in rows)),
        }
        return Response({'results': [{**row, 'debit': float(row['debit']), 'credit': float(row['credit']), 'balance': float(row['balance'])} for row in rows], 'summary': totals})


class AdminAccountingBankTransactionCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        queryset = AccountingBankTransaction.objects.select_related(
            'matched_payment_session',
            'matched_order',
            'reconciled_by',
        ).order_by('-transaction_date', '-id')
        search = (request.query_params.get('q') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        provider = (request.query_params.get('provider') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search)
                | Q(transaction_id__icontains=search)
                | Q(description__icontains=search)
                | Q(matched_payment_session__reference__icontains=search)
                | Q(matched_order__number__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if provider:
            queryset = queryset.filter(provider__iexact=provider)
        page_obj, pagination = _pagination(request, queryset)
        totals = queryset.aggregate(deposit=Sum('deposit'), withdrawal=Sum('withdrawal'))
        return Response({
            'results': [_bank_transaction_payload(row) for row in page_obj.object_list],
            'pagination': pagination,
            'summary': {
                'deposit': float(totals.get('deposit') or 0),
                'withdrawal': float(totals.get('withdrawal') or 0),
                'unreconciled': queryset.filter(status=AccountingBankTransaction.STATUS_UNRECONCILED).count(),
            },
        })

    def post(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = BankTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        transaction = AccountingBankTransaction.objects.create(
            transaction_date=data.get('transaction_date') or timezone.localdate(),
            bank_account=data.get('bank_account') or 'Cash and Bank',
            provider=data.get('provider', ''),
            reference_number=data.get('reference_number', ''),
            transaction_id=data.get('transaction_id', ''),
            description=data.get('description', ''),
            deposit=data.get('deposit') or Decimal('0'),
            withdrawal=data.get('withdrawal') or Decimal('0'),
            currency=(data.get('currency') or 'KES').upper(),
            notes=data.get('notes', ''),
            created_by=request.user,
        )
        return Response({'bank_transaction': _bank_transaction_payload(transaction)}, status=status.HTTP_201_CREATED)


class AdminAccountingBankTransactionCsvImportAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = BankTransactionCsvImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data['file']
        provider = (serializer.validated_data.get('provider') or 'bank_transfer').strip()
        bank_account = (serializer.validated_data.get('bank_account') or 'Cash and Bank').strip()
        currency = (serializer.validated_data.get('currency') or 'KES').strip().upper()

        try:
            text = upload.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            upload.seek(0)
            text = upload.read().decode('latin-1')

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            return Response({'detail': 'CSV must have a header row.'}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        skipped = []
        errors = []
        for row_number, row in enumerate(reader, start=2):
            date_value = _csv_get(row, 'date')
            reference = _csv_get(row, 'reference')
            description = _csv_get(row, 'description')
            deposit = _parse_csv_decimal(_csv_get(row, 'deposit'))
            withdrawal = _parse_csv_decimal(_csv_get(row, 'withdrawal'))
            amount = _parse_csv_decimal(_csv_get(row, 'amount'))
            row_currency = (_csv_get(row, 'currency') or currency).upper()

            if deposit <= 0 and withdrawal <= 0 and amount != 0:
                if amount > 0:
                    deposit = amount
                else:
                    withdrawal = abs(amount)

            if deposit <= 0 and withdrawal <= 0:
                skipped.append({'row': row_number, 'reason': 'No deposit or withdrawal amount found.'})
                continue

            transaction_date = _parse_csv_date(date_value)
            transaction_id = reference[:128] if reference else ''
            if _transaction_exists(
                transaction_id=transaction_id,
                reference_number=reference,
                provider=provider,
                amount=deposit,
                transaction_date=transaction_date,
            ):
                skipped.append({'row': row_number, 'reference': reference, 'reason': 'Duplicate transaction.'})
                continue

            try:
                transaction = AccountingBankTransaction.objects.create(
                    transaction_date=transaction_date,
                    bank_account=bank_account,
                    provider=provider,
                    reference_number=reference[:128],
                    transaction_id=transaction_id,
                    description=description[:255],
                    deposit=deposit,
                    withdrawal=withdrawal,
                    currency=row_currency[:12],
                    source=AccountingBankTransaction.SOURCE_IMPORT,
                    notes=f'Imported from CSV file {upload.name}',
                    created_by=request.user,
                )
                created.append(_bank_transaction_payload(transaction))
            except Exception as exc:
                errors.append({'row': row_number, 'reference': reference, 'reason': str(exc)})

        return Response({
            'created': created,
            'summary': {
                'created': len(created),
                'skipped': len(skipped),
                'errors': len(errors),
            },
            'skipped': skipped[:50],
            'errors': errors[:50],
        }, status=status.HTTP_201_CREATED)


class AdminAccountingBankTransactionDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, transaction_id: int, action: str):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        bank_transaction = AccountingBankTransaction.objects.select_related('matched_payment_session', 'matched_order').get(pk=transaction_id)
        if action == 'reconcile':
            serializer = ReconcileBankTransactionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            payment = None
            order = None
            payment_reference = (data.get('payment_reference') or '').strip()
            order_number = (data.get('order_number') or '').strip()
            if payment_reference:
                payment = PaymentSession.objects.select_related('order', 'user').filter(reference=payment_reference).first()
                if not payment:
                    return Response({'detail': f'Payment {payment_reference} was not found.'}, status=status.HTTP_400_BAD_REQUEST)
            if order_number:
                Order = apps.get_model('order', 'Order')
                order = Order.objects.filter(number=order_number).first()
                if not order:
                    return Response({'detail': f'Order {order_number} was not found.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                allocation = reconcile_bank_transaction(
                    bank_transaction=bank_transaction,
                    payment_session=payment,
                    order=order,
                    allocated_amount=data.get('allocated_amount'),
                    note=data.get('note', ''),
                    user=request.user,
                )
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'bank_transaction': _bank_transaction_payload(allocation.bank_transaction),
                'allocation': _allocation_payload(allocation),
            })
        if action == 'cancel':
            serializer = CancelBankTransactionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                bank_transaction = cancel_bank_transaction(
                    bank_transaction=bank_transaction,
                    note=serializer.validated_data.get('note', ''),
                    user=request.user,
                )
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'bank_transaction': _bank_transaction_payload(bank_transaction)})
        return Response({'detail': 'Unsupported bank transaction action.'}, status=status.HTTP_400_BAD_REQUEST)


class AdminAccountingReconciliationCandidatesAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        q = (request.query_params.get('q') or '').strip()
        amount = (request.query_params.get('amount') or '').strip()
        payments = PaymentSession.objects.select_related('order', 'user').order_by('-created_at')
        orders = apps.get_model('order', 'Order').objects.select_related('user').order_by('-date_placed')
        if q:
            payments = payments.filter(
                Q(reference__icontains=q)
                | Q(external_reference__icontains=q)
                | Q(payer_email__icontains=q)
                | Q(payer_phone__icontains=q)
                | Q(order__number__icontains=q)
            )
            orders = orders.filter(Q(number__icontains=q) | Q(email__icontains=q) | Q(user__email__icontains=q))
        if amount:
            try:
                numeric_amount = Decimal(amount)
                payments = payments.filter(amount=numeric_amount)
                orders = orders.filter(total_incl_tax=numeric_amount)
            except Exception:
                pass
        payments = payments[:25]
        orders = orders[:25]
        return Response({
            'payments': [_payment_candidate_payload(payment) for payment in payments],
            'orders': [_order_candidate_payload(order) for order in orders],
        })


class AdminAccountingReconciliationAllocationCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not _require_finance(request):
            return Response({'detail': 'Finance access is required.'}, status=status.HTTP_403_FORBIDDEN)
        queryset = AccountingReconciliationAllocation.objects.select_related(
            'bank_transaction',
            'payment_session',
            'order',
            'journal_entry',
            'reconciled_by',
        ).order_by('-created_at', '-id')
        search = (request.query_params.get('q') or '').strip()
        if search:
            queryset = queryset.filter(
                Q(payment_session__reference__icontains=search)
                | Q(order__number__icontains=search)
                | Q(bank_transaction__reference_number__icontains=search)
                | Q(journal_entry__reference__icontains=search)
            )
        page_obj, pagination = _pagination(request, queryset)
        return Response({'results': [_allocation_payload(row) for row in page_obj.object_list], 'pagination': pagination})
