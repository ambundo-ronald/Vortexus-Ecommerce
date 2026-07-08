from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchAnalyticsEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(db_index=True, max_length=60)),
                ('source', models.CharField(blank=True, db_index=True, default='', max_length=40)),
                ('query', models.CharField(blank=True, db_index=True, default='', max_length=255)),
                ('search_context_id', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('anonymous_id', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('user_email', models.EmailField(blank=True, db_index=True, default='', max_length=254)),
                ('category', models.CharField(blank=True, db_index=True, default='', max_length=120)),
                ('brand', models.CharField(blank=True, db_index=True, default='', max_length=120)),
                ('result_count', models.PositiveIntegerField(blank=True, null=True)),
                ('product_id', models.PositiveIntegerField(blank=True, db_index=True, null=True)),
                ('product_title', models.CharField(blank=True, default='', max_length=255)),
                ('order_number', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('path', models.CharField(blank=True, default='', max_length=255)),
                ('ip_hash', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('user_agent', models.CharField(blank=True, default='', max_length=255)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='search_analytics_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-id'],
                'indexes': [
                    models.Index(fields=['event_type', 'created_at'], name='auditlog_se_event_t_3b4c83_idx'),
                    models.Index(fields=['query', 'created_at'], name='auditlog_se_query_a0b9f8_idx'),
                    models.Index(fields=['search_context_id', 'event_type'], name='auditlog_se_search_2e0bf7_idx'),
                ],
            },
        ),
    ]
