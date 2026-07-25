import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalogue', '0001_initial'),
        ('notifications', '0010_admin_push_notifications'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CallbackRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160)),
                ('phone_number', models.CharField(max_length=32)),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('contacted', 'Contacted'), ('resolved', 'Resolved'), ('cancelled', 'Cancelled')], default='pending', max_length=16)),
                ('respond_by', models.DateTimeField()),
                ('staff_notes', models.TextField(blank=True)),
                ('contacted_at', models.DateTimeField(blank=True, null=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_callback_requests', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='callback_requests', to='catalogue.product')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='callback_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['respond_by', '-created_at']},
        ),
        migrations.AddIndex(
            model_name='callbackrequest',
            index=models.Index(fields=['status', 'respond_by'], name='notificatio_status_737379_idx'),
        ),
        migrations.AddIndex(
            model_name='callbackrequest',
            index=models.Index(fields=['product', '-created_at'], name='notificatio_product_b9ec68_idx'),
        ),
        migrations.AddIndex(
            model_name='callbackrequest',
            index=models.Index(fields=['phone_number', '-created_at'], name='notificatio_phone_n_4a2f46_idx'),
        ),
    ]
