from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0009_merge_supplier_and_security_email_updates'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(max_length=80)),
                ('event_key', models.CharField(blank=True, max_length=160)),
                ('title', models.CharField(max_length=160)),
                ('message', models.TextField(blank=True)),
                ('severity', models.CharField(choices=[('info', 'Info'), ('success', 'Success'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical')], default='info', max_length=16)),
                ('action_url', models.CharField(blank=True, max_length=255)),
                ('related_object_type', models.CharField(blank=True, max_length=64)),
                ('related_object_id', models.CharField(blank=True, max_length=64)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admin_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='PushSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('admin', 'Admin'), ('storefront', 'Storefront')], default='storefront', max_length=32)),
                ('endpoint', models.TextField(unique=True)),
                ('p256dh', models.CharField(max_length=255)),
                ('auth', models.CharField(max_length=255)),
                ('browser', models.CharField(blank=True, max_length=120)),
                ('user_agent', models.TextField(blank=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('last_seen_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='PushDeliveryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('skipped', 'Skipped')], default='pending', max_length=16)),
                ('endpoint_hash', models.CharField(blank=True, max_length=64)),
                ('event_type', models.CharField(blank=True, max_length=80)),
                ('title', models.CharField(blank=True, max_length=160)),
                ('error_message', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notification', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='push_delivery_logs', to='notifications.adminnotification')),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delivery_logs', to='notifications.pushsubscription')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='adminnotification',
            index=models.Index(fields=['user', 'read_at', '-created_at'], name='notificatio_user_id_66e356_idx'),
        ),
        migrations.AddIndex(
            model_name='adminnotification',
            index=models.Index(fields=['event_type', '-created_at'], name='notificatio_event_t_727cec_idx'),
        ),
        migrations.AddIndex(
            model_name='adminnotification',
            index=models.Index(fields=['severity', '-created_at'], name='notificatio_severit_d8084a_idx'),
        ),
        migrations.AddConstraint(
            model_name='adminnotification',
            constraint=models.UniqueConstraint(condition=~models.Q(event_key=''), fields=('user', 'event_key'), name='unique_admin_notification_event_per_user'),
        ),
        migrations.AddIndex(
            model_name='pushsubscription',
            index=models.Index(fields=['user', 'channel', 'is_enabled'], name='notificatio_user_id_e03349_idx'),
        ),
        migrations.AddIndex(
            model_name='pushdeliverylog',
            index=models.Index(fields=['status', '-created_at'], name='notificatio_status_370a60_idx'),
        ),
        migrations.AddIndex(
            model_name='pushdeliverylog',
            index=models.Index(fields=['event_type', '-created_at'], name='notificatio_event_t_726565_idx'),
        ),
    ]
