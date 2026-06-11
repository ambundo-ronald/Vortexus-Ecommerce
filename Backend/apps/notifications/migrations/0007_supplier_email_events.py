from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0006_emailsuppression'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailnotification',
            name='event_type',
            field=models.CharField(
                choices=[
                    ('account_registered', 'Account Registered'),
                    ('email_verification', 'Email Verification'),
                    ('email_two_factor', 'Email Two Factor'),
                    ('password_reset', 'Password Reset'),
                    ('password_changed', 'Password Changed'),
                    ('quote_request_customer', 'Quote Request Customer'),
                    ('quote_request_internal', 'Quote Request Internal'),
                    ('order_confirmation', 'Order Confirmation'),
                    ('shipping_update', 'Shipping Update'),
                    ('supplier_application_submitted', 'Supplier Application Submitted'),
                    ('supplier_status_changed', 'Supplier Status Changed'),
                ],
                max_length=64,
            ),
        ),
    ]
