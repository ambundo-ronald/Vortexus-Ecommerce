from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auditlog.services import record_audit_event

from .user_serializers import AdminUserDetailSerializer, AdminUserListSerializer, AdminUserWriteSerializer

User = get_user_model()


def _admin_users_queryset():
    return User.objects.select_related('customer_profile').order_by('-date_joined', '-id')


def _filter_admin_users_queryset(queryset, *, search: str = '', role: str = '', status_filter: str = ''):
    if search:
        queryset = queryset.filter(
            Q(email__icontains=search)
            | Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(customer_profile__company__icontains=search)
            | Q(customer_profile__phone__icontains=search)
        )

    if role == 'admin':
        queryset = queryset.filter(is_superuser=True)
    elif role == 'staff':
        queryset = queryset.filter(is_staff=True, is_superuser=False)
    elif role == 'customer':
        queryset = queryset.filter(is_staff=False, is_superuser=False, supplier_profile__isnull=True)
    elif role == 'supplier':
        queryset = queryset.filter(supplier_profile__isnull=False)

    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'suspended':
        queryset = queryset.filter(is_active=False)

    return queryset


class AdminUserCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        queryset = _admin_users_queryset()
        search = (request.query_params.get('q') or '').strip()
        role = (request.query_params.get('role') or '').strip().lower()
        status_filter = (request.query_params.get('status') or '').strip().lower()

        queryset = _filter_admin_users_queryset(queryset, search=search, role=role, status_filter=status_filter)

        sort_by = (request.query_params.get('sort_by') or '').strip()
        if sort_by == 'email':
            queryset = queryset.order_by('email', '-id')
        elif sort_by == 'role':
            queryset = queryset.order_by('-is_superuser', '-is_staff', 'email')
        elif sort_by == 'status':
            queryset = queryset.order_by('-is_active', 'email')
        elif sort_by == 'name':
            queryset = queryset.order_by('first_name', 'last_name', 'email')
        else:
            queryset = queryset.order_by('-date_joined', '-id')

        try:
            page = max(int(request.query_params.get('page', 1) or 1), 1)
            page_size = min(max(int(request.query_params.get('page_size', 20) or 20), 1), 100)
        except (TypeError, ValueError):
            return Response(
                {
                    'error': {
                        'code': 'invalid_pagination',
                        'detail': 'Page and page_size must be integers.',
                        'status': 400,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = AdminUserListSerializer(page_obj.object_list, many=True)

        summary_queryset = _filter_admin_users_queryset(_admin_users_queryset(), search=search)

        return Response(
            {
                'results': serializer.data,
                'pagination': {
                    'page': page_obj.number,
                    'page_size': page_size,
                    'total': paginator.count,
                    'num_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                },
                'summary': {
                    'total': summary_queryset.count(),
                    'active': summary_queryset.filter(is_active=True).count(),
                    'suspended': summary_queryset.filter(is_active=False).count(),
                    'staff': summary_queryset.filter(is_staff=True).count(),
                },
            }
        )

    def post(self, request):
        serializer = AdminUserWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        record_audit_event(
            event_type='account.admin_user_created',
            request=request,
            actor=request.user,
            target=user,
            message='Admin created a user account.',
            metadata={'email': user.email, 'is_staff': user.is_staff, 'is_superuser': user.is_superuser},
        )
        return Response({'user': AdminUserDetailSerializer(user).data}, status=status.HTTP_201_CREATED)


class AdminUserDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, user_id: int):
        user = get_object_or_404(_admin_users_queryset(), id=user_id)
        return Response({'user': AdminUserDetailSerializer(user).data})

    def patch(self, request, user_id: int):
        user = get_object_or_404(_admin_users_queryset(), id=user_id)
        previous_state = {
            'email': user.email,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        serializer = AdminUserWriteSerializer(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        record_audit_event(
            event_type='account.admin_user_updated',
            request=request,
            actor=request.user,
            target=user,
            message='Admin updated a user account.',
            metadata={
                'previous_email': previous_state['email'],
                'current_email': user.email,
                'previous_is_active': previous_state['is_active'],
                'current_is_active': user.is_active,
                'previous_is_staff': previous_state['is_staff'],
                'current_is_staff': user.is_staff,
                'previous_is_superuser': previous_state['is_superuser'],
                'current_is_superuser': user.is_superuser,
            },
        )
        return Response({'user': AdminUserDetailSerializer(user).data})
