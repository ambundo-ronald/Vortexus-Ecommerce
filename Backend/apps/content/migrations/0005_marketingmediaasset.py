from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0004_alter_marketingblock_placement'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketingMediaAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('marketing_block', 'Marketing block')], db_index=True, default='marketing_block', max_length=40)),
                ('title', models.CharField(blank=True, max_length=160)),
                ('image', models.ImageField(upload_to='marketing-blocks/%Y/%m/')),
                ('alt_text', models.CharField(blank=True, max_length=160)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='marketing_media_assets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-id'],
                'indexes': [models.Index(fields=['category', '-created_at'], name='content_mar_categor_f1e2f3_idx')],
            },
        ),
    ]
