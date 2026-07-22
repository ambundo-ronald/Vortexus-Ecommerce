from django.apps import apps


def is_platform_admin(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, 'is_superuser', False))


def is_account_manager(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and getattr(user, 'is_staff', False)
        and not getattr(user, 'is_superuser', False)
    )


def can_access_all_admin_data(user) -> bool:
    return is_platform_admin(user)


def assigned_supplier_queryset(user):
    SupplierProfile = apps.get_model('marketplace', 'SupplierProfile')
    queryset = SupplierProfile.objects.select_related('user', 'partner', 'account_manager')
    if can_access_all_admin_data(user):
        return queryset
    if is_account_manager(user):
        return queryset.filter(account_manager=user)
    return queryset.none()


def assigned_partner_ids(user):
    return assigned_supplier_queryset(user).values_list('partner_id', flat=True)


def scope_orders_queryset(queryset, user):
    if can_access_all_admin_data(user):
        return queryset
    if is_account_manager(user):
        return queryset.filter(supplier_groups__partner_id__in=assigned_partner_ids(user)).distinct()
    return queryset.none()


def scope_payment_sessions_queryset(queryset, user):
    if can_access_all_admin_data(user):
        return queryset
    if is_account_manager(user):
        return queryset.filter(order__supplier_groups__partner_id__in=assigned_partner_ids(user)).distinct()
    return queryset.none()

