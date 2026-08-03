from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (
    AccountingAccount,
    AccountingBankTransaction,
    AccountingJournalEntry,
    AccountingJournalLine,
    AccountingPaymentLedgerEntry,
    AccountingReconciliationAllocation,
)


DEFAULT_ACCOUNTS = [
    ('1000', 'Cash and Bank', AccountingAccount.TYPE_ASSET),
    ('1100', 'Accounts Receivable', AccountingAccount.TYPE_ASSET),
    ('2000', 'Supplier Payables', AccountingAccount.TYPE_LIABILITY),
    ('2100', 'Tax Payable', AccountingAccount.TYPE_LIABILITY),
    ('4000', 'Sales Revenue', AccountingAccount.TYPE_INCOME),
    ('4100', 'Shipping Revenue', AccountingAccount.TYPE_INCOME),
    ('5000', 'Supplier Cost of Goods Sold', AccountingAccount.TYPE_EXPENSE),
    ('5100', 'Payment Gateway Fees', AccountingAccount.TYPE_EXPENSE),
    ('5200', 'Refunds and Returns', AccountingAccount.TYPE_EXPENSE),
    ('9999', 'Accounting Suspense', AccountingAccount.TYPE_ASSET),
]


def ensure_default_chart_of_accounts(currency='KES'):
    accounts = {}
    for code, name, account_type in DEFAULT_ACCOUNTS:
        account, _ = AccountingAccount.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'account_type': account_type,
                'currency': currency,
            },
        )
        accounts[code] = account
    return accounts


def account(code):
    ensure_default_chart_of_accounts()
    return AccountingAccount.objects.get(code=code)


def source_tuple(source):
    if not source:
        return None, ''
    return ContentType.objects.get_for_model(source, for_concrete_model=False), str(source.pk)


def decimal_amount(value):
    return Decimal(str(value or '0')).quantize(Decimal('0.01'))


@transaction.atomic
def submit_journal_entry(*, reference, entry_type, lines, source=None, memo='', currency='KES', user=None, posting_date=None):
    content_type, object_id = source_tuple(source)
    entry, created = AccountingJournalEntry.objects.get_or_create(
        reference=reference,
        defaults={
            'entry_type': entry_type,
            'posting_date': posting_date or timezone.localdate(),
            'memo': memo,
            'source_content_type': content_type,
            'source_object_id': object_id,
            'currency': currency,
        },
    )
    if not created:
        return entry

    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    for line in lines:
        debit = decimal_amount(line.get('debit'))
        credit = decimal_amount(line.get('credit'))
        total_debit += debit
        total_credit += credit
        AccountingJournalLine.objects.create(
            journal_entry=entry,
            account=line['account'],
            debit=debit,
            credit=credit,
            currency=line.get('currency') or currency,
            party_type=line.get('party_type', ''),
            party_id=str(line.get('party_id', '') or ''),
            party_name=line.get('party_name', ''),
            against_account=line.get('against_account', ''),
            remarks=line.get('remarks', ''),
        )

    if total_debit != total_credit:
        raise ValueError(f'Journal entry {reference} is not balanced: debit={total_debit} credit={total_credit}')

    entry.total_debit = total_debit
    entry.total_credit = total_credit
    entry.status = AccountingJournalEntry.STATUS_SUBMITTED
    entry.submitted_by = user
    entry.submitted_at = timezone.now()
    entry.save(update_fields=['total_debit', 'total_credit', 'status', 'submitted_by', 'submitted_at', 'updated_at'])
    return entry


def record_payment_ledger(*, account_type, account_obj, party_type, party_id, voucher_type, voucher_no, amount, source=None, against_voucher_type='', against_voucher_no='', journal_entry=None, currency='KES', party_name='', posting_date=None):
    content_type, object_id = source_tuple(source)
    return AccountingPaymentLedgerEntry.objects.get_or_create(
        account_type=account_type,
        party_type=party_type,
        party_id=str(party_id),
        voucher_type=voucher_type,
        voucher_no=voucher_no,
        against_voucher_type=against_voucher_type,
        against_voucher_no=against_voucher_no,
        defaults={
            'account': account_obj,
            'party_name': party_name,
            'amount': decimal_amount(amount),
            'currency': currency,
            'posting_date': posting_date or timezone.localdate(),
            'journal_entry': journal_entry,
            'source_content_type': content_type,
            'source_object_id': object_id,
        },
    )[0]


def trial_balance(currency='KES'):
    rows = []
    for acct in AccountingAccount.objects.filter(is_active=True).order_by('code'):
        totals = acct.journal_lines.filter(journal_entry__status=AccountingJournalEntry.STATUS_SUBMITTED).aggregate(
            debit=Sum('debit'),
            credit=Sum('credit'),
        )
        debit = decimal_amount(totals.get('debit'))
        credit = decimal_amount(totals.get('credit'))
        rows.append({
            'code': acct.code,
            'name': acct.name,
            'account_type': acct.account_type,
            'debit': debit,
            'credit': credit,
            'balance': debit - credit,
            'currency': currency,
        })
    return rows


def _customer_party(order=None, payment=None):
    user = getattr(order, 'user', None) or getattr(payment, 'user', None)
    email = getattr(user, 'email', '') or getattr(order, 'guest_email', '') or getattr(payment, 'payer_email', '')
    return {
        'party_type': 'customer',
        'party_id': str(getattr(user, 'id', '') or email or 'guest'),
        'party_name': email or 'Guest customer',
    }


def _supplier_party(payable=None, batch=None):
    supplier = getattr(payable, 'supplier', None) or getattr(batch, 'supplier', None)
    partner = getattr(payable, 'partner', None) or getattr(batch, 'partner', None)
    return {
        'party_type': 'supplier',
        'party_id': str(getattr(supplier, 'id', '') or getattr(partner, 'id', '') or 'supplier'),
        'party_name': getattr(supplier, 'company_name', '') or getattr(partner, 'name', '') or 'Supplier',
    }


def post_sales_order(order, *, user=None):
    currency = getattr(order, 'currency', 'KES') or 'KES'
    total_incl = decimal_amount(getattr(order, 'total_incl_tax', 0))
    total_excl = decimal_amount(getattr(order, 'total_excl_tax', 0))
    shipping_excl = min(decimal_amount(getattr(order, 'shipping_excl_tax', 0)), total_excl)
    item_revenue = total_excl - shipping_excl
    tax_amount = max(total_incl - total_excl, Decimal('0.00'))
    party = _customer_party(order=order)
    lines = [
        {'account': account('1100'), 'debit': total_incl, **party, 'remarks': f'Customer receivable for order {order.number}'},
        {'account': account('4000'), 'credit': item_revenue, **party, 'remarks': f'Item revenue for order {order.number}'},
    ]
    if shipping_excl:
        lines.append({'account': account('4100'), 'credit': shipping_excl, **party, 'remarks': f'Shipping revenue for order {order.number}'})
    if tax_amount:
        lines.append({'account': account('2100'), 'credit': tax_amount, **party, 'remarks': f'Tax payable for order {order.number}'})
    entry = submit_journal_entry(
        reference=f'SALES-{order.number}',
        entry_type=AccountingJournalEntry.TYPE_SALES,
        lines=lines,
        source=order,
        memo=f'Sales accounting for order {order.number}',
        currency=currency,
        user=user,
        posting_date=getattr(order, 'date_placed', None).date() if getattr(order, 'date_placed', None) else None,
    )
    record_payment_ledger(
        account_type=AccountingPaymentLedgerEntry.TYPE_RECEIVABLE,
        account_obj=account('1100'),
        voucher_type='Sales Order',
        voucher_no=order.number,
        against_voucher_type='Sales Order',
        against_voucher_no=order.number,
        amount=total_incl,
        source=order,
        journal_entry=entry,
        currency=currency,
        **party,
    )
    return entry


def post_payment_received(payment, *, user=None):
    if not getattr(payment, 'order_id', None):
        return None
    order = payment.order
    currency = getattr(payment, 'currency', 'KES') or 'KES'
    amount = decimal_amount(getattr(payment, 'amount', 0))
    party = _customer_party(order=order, payment=payment)
    entry = submit_journal_entry(
        reference=f'PAYMENT-{payment.reference}',
        entry_type=AccountingJournalEntry.TYPE_PAYMENT,
        lines=[
            {'account': account('1000'), 'debit': amount, **party, 'remarks': f'Payment received {payment.reference}'},
            {'account': account('1100'), 'credit': amount, **party, 'remarks': f'Clear receivable for order {order.number}'},
        ],
        source=payment,
        memo=f'Payment received for order {order.number}',
        currency=currency,
        user=user,
        posting_date=getattr(payment, 'paid_at', None).date() if getattr(payment, 'paid_at', None) else None,
    )
    record_payment_ledger(
        account_type=AccountingPaymentLedgerEntry.TYPE_RECEIVABLE,
        account_obj=account('1100'),
        voucher_type='Payment Entry',
        voucher_no=payment.reference,
        against_voucher_type='Sales Order',
        against_voucher_no=order.number,
        amount=-amount,
        source=payment,
        journal_entry=entry,
        currency=currency,
        **party,
    )
    return entry


@transaction.atomic
def reconcile_bank_transaction(*, bank_transaction, payment_session=None, order=None, allocated_amount=None, note='', user=None):
    if bank_transaction.status == AccountingBankTransaction.STATUS_CANCELLED:
        raise ValueError('Cancelled bank transactions cannot be reconciled.')
    if bank_transaction.status == AccountingBankTransaction.STATUS_RECONCILED:
        raise ValueError('This bank transaction is already reconciled.')

    amount = decimal_amount(allocated_amount if allocated_amount is not None else bank_transaction.deposit)
    if amount <= 0:
        raise ValueError('Reconciliation amount must be greater than zero.')

    payment_order = getattr(payment_session, 'order', None) if payment_session else None
    resolved_order = order or payment_order
    currency = bank_transaction.currency or getattr(payment_session, 'currency', 'KES') or 'KES'
    party = _customer_party(order=resolved_order, payment=payment_session)

    journal = None
    if payment_session and resolved_order:
        journal = post_payment_received(payment_session, user=user)
    else:
        journal = submit_journal_entry(
            reference=f'BANK-RECON-{bank_transaction.id}',
            entry_type=AccountingJournalEntry.TYPE_PAYMENT,
            lines=[
                {'account': account('1000'), 'debit': amount, **party, 'remarks': f'Bank transaction {bank_transaction.reference_number or bank_transaction.transaction_id}'},
                {'account': account('9999'), 'credit': amount, **party, 'remarks': 'Unallocated customer collection held in suspense'},
            ],
            source=bank_transaction,
            memo=note or 'Manual bank reconciliation to suspense',
            currency=currency,
            user=user,
            posting_date=bank_transaction.transaction_date,
        )

    allocation = AccountingReconciliationAllocation.objects.create(
        bank_transaction=bank_transaction,
        payment_session=payment_session,
        order=resolved_order,
        journal_entry=journal,
        allocated_amount=amount,
        currency=currency,
        status=AccountingReconciliationAllocation.STATUS_RECONCILED,
        note=note,
        reconciled_by=user,
        reconciled_at=timezone.now(),
    )

    bank_transaction.status = AccountingBankTransaction.STATUS_RECONCILED
    bank_transaction.matched_payment_session = payment_session
    bank_transaction.matched_order = resolved_order
    bank_transaction.clearance_date = timezone.localdate()
    bank_transaction.reconciled_by = user
    bank_transaction.reconciled_at = timezone.now()
    bank_transaction.notes = note or bank_transaction.notes
    bank_transaction.save(update_fields=[
        'status',
        'matched_payment_session',
        'matched_order',
        'clearance_date',
        'reconciled_by',
        'reconciled_at',
        'notes',
        'updated_at',
    ])
    return allocation


@transaction.atomic
def cancel_bank_transaction(*, bank_transaction, note='', user=None):
    if bank_transaction.status == AccountingBankTransaction.STATUS_RECONCILED:
        raise ValueError('Reconciled bank transactions cannot be cancelled.')
    bank_transaction.status = AccountingBankTransaction.STATUS_CANCELLED
    bank_transaction.cancelled_by = user
    bank_transaction.cancelled_at = timezone.now()
    bank_transaction.notes = note or bank_transaction.notes
    bank_transaction.save(update_fields=['status', 'cancelled_by', 'cancelled_at', 'notes', 'updated_at'])
    return bank_transaction


def post_supplier_payable(payable, *, user=None):
    if str(getattr(payable, 'status', '') or '').strip().lower() not in {'payable', 'approved', 'paid'}:
        return None
    currency = getattr(payable, 'currency', 'KES') or 'KES'
    amount = decimal_amount(getattr(payable, 'payable_total', 0))
    if amount <= 0:
        return None
    party = _supplier_party(payable=payable)
    order_number = getattr(payable.order, 'number', str(payable.order_id))
    entry = submit_journal_entry(
        reference=f'SUPP-PAYABLE-{payable.id}',
        entry_type=AccountingJournalEntry.TYPE_SUPPLIER_PAYABLE,
        lines=[
            {'account': account('5000'), 'debit': amount, **party, 'remarks': f'Supplier cost for order {order_number}'},
            {'account': account('2000'), 'credit': amount, **party, 'remarks': f'Supplier payable for order {order_number}'},
        ],
        source=payable,
        memo=f'Supplier payable for order {order_number}',
        currency=currency,
        user=user,
    )
    record_payment_ledger(
        account_type=AccountingPaymentLedgerEntry.TYPE_PAYABLE,
        account_obj=account('2000'),
        voucher_type='Supplier Payable',
        voucher_no=str(payable.id),
        against_voucher_type='Order',
        against_voucher_no=order_number,
        amount=amount,
        source=payable,
        journal_entry=entry,
        currency=currency,
        **party,
    )
    return entry


def post_supplier_payout(batch, *, user=None):
    currency = getattr(batch, 'currency', 'KES') or 'KES'
    amount = decimal_amount(getattr(batch, 'total_amount', 0))
    if amount <= 0:
        return None
    party = _supplier_party(batch=batch)
    entry = submit_journal_entry(
        reference=f'SUPP-PAYOUT-{batch.batch_reference}',
        entry_type=AccountingJournalEntry.TYPE_SUPPLIER_PAYOUT,
        lines=[
            {'account': account('2000'), 'debit': amount, **party, 'remarks': f'Supplier payout {batch.batch_reference}'},
            {'account': account('1000'), 'credit': amount, **party, 'remarks': f'Cash paid to supplier {batch.batch_reference}'},
        ],
        source=batch,
        memo=f'Supplier payout {batch.batch_reference}',
        currency=currency,
        user=user,
        posting_date=getattr(batch, 'paid_at', None).date() if getattr(batch, 'paid_at', None) else None,
    )
    record_payment_ledger(
        account_type=AccountingPaymentLedgerEntry.TYPE_PAYABLE,
        account_obj=account('2000'),
        voucher_type='Supplier Payout',
        voucher_no=batch.batch_reference,
        against_voucher_type='Supplier Payout',
        against_voucher_no=batch.batch_reference,
        amount=-amount,
        source=batch,
        journal_entry=entry,
        currency=currency,
        **party,
    )
    return entry


def post_refund(refund, *, user=None):
    currency = getattr(refund, 'currency', 'KES') or 'KES'
    amount = decimal_amount(getattr(refund, 'amount', 0))
    if amount <= 0:
        return None
    order_number = getattr(getattr(refund, 'order', None), 'number', '') or getattr(getattr(refund, 'payment_session', None), 'reference', '')
    party = _customer_party(order=getattr(refund, 'order', None), payment=getattr(refund, 'payment_session', None))
    entry = submit_journal_entry(
        reference=f'REFUND-{refund.refund_reference}',
        entry_type=AccountingJournalEntry.TYPE_REFUND,
        lines=[
            {'account': account('5200'), 'debit': amount, **party, 'remarks': f'Refund {refund.refund_reference}'},
            {'account': account('1000'), 'credit': amount, **party, 'remarks': f'Cash refunded {refund.refund_reference}'},
        ],
        source=refund,
        memo=f'Refund for {order_number}',
        currency=currency,
        user=user,
        posting_date=getattr(refund, 'processed_at', None).date() if getattr(refund, 'processed_at', None) else None,
    )
    return entry
