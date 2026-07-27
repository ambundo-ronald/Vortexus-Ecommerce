import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalogue', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='ShopperList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160)),
                ('note', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('shared', 'Shared'), ('viewed', 'Viewed'), ('added_to_cart', 'Added to cart'), ('archived', 'Archived')], db_index=True, default='draft', max_length=24)),
                ('share_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('viewed_at', models.DateTimeField(blank=True, null=True)),
                ('added_to_cart_at', models.DateTimeField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_shopper_lists', to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopper_lists', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-date_updated', '-id')},
        ),
        migrations.CreateModel(
            name='ShopperListItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('note', models.CharField(blank=True, max_length=300)),
                ('position', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shopper_list_items', to='catalogue.product')),
                ('shopper_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='personal_shopper.shopperlist')),
            ],
            options={'ordering': ('position', 'id')},
        ),
        migrations.AddConstraint(model_name='shopperlistitem', constraint=models.UniqueConstraint(fields=('shopper_list', 'product'), name='unique_product_per_shopper_list')),
    ]

