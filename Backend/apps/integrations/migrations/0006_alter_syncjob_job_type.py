from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0005_alter_integrationconnection_auth_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='syncjob',
            name='job_type',
            field=models.CharField(
                choices=[
                    ('products_import', 'Products Import'),
                    ('stock_import', 'Stock Import'),
                    ('prices_import', 'Prices Import'),
                    ('customers_import', 'Customers Import'),
                    ('suppliers_import', 'Suppliers Import'),
                    ('orders_export', 'Orders Export'),
                    ('fulfillment_import', 'Fulfillment Import'),
                    ('connection_test', 'Connection Test'),
                    ('google_sheets_export', 'Google Sheets Export'),
                ],
                max_length=32,
            ),
        ),
    ]
