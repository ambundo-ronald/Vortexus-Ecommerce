from django.db import migrations


TEMPLATE_UPDATES = {
    'email_verification': (
        'Hello {{ display_name }},\n\n'
        'Please verify your email address for {{ shop_name }}:\n\n'
        '{{ verification_url }}\n\n'
        'This verification link expires in 30 minutes.\n\n'
        'This helps protect your account and keeps order, quote, and security notifications going to the right inbox.\n\n'
        'If you did not create or update this account, please ignore this email or contact our support team.\n\n'
        '{{ shop_name }}\n'
    ),
    'password_reset': (
        'Hello {{ display_name }},\n\n'
        'We received a request to reset your {{ shop_name }} password.\n\n'
        'Set a new password here:\n\n'
        '{{ reset_url }}\n\n'
        'This password reset link expires in 30 minutes.\n\n'
        'If you did not request this, you can ignore this email. Your password will stay unchanged.\n\n'
        '{{ shop_name }}\n'
    ),
}


def update_templates(apps, schema_editor):
    CommunicationEventType = apps.get_model('communication', 'CommunicationEventType')
    for code, body in TEMPLATE_UPDATES.items():
        CommunicationEventType.objects.filter(code=code).update(email_body_template=body)


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0007_account_reactivation_request_choice'),
    ]

    operations = [
        migrations.RunPython(update_templates, migrations.RunPython.noop),
    ]
