from django.db import migrations


TEMPLATES = [
    {
        'code': 'account_registered',
        'name': 'Account Registered',
        'category': 'Account',
        'subject': 'Welcome to {{ shop_name }}',
        'body': (
            'Hello {{ display_name }},\n\n'
            'Your account has been created successfully on {{ shop_name }}.\n\n'
            'You can now sign in, manage your saved equipment lists, request quotes, and track your project-related orders.\n\n'
            'If you did not create this account, please contact our support team immediately.\n\n'
            '{{ shop_name }}\n'
        ),
    },
    {
        'code': 'email_verification',
        'name': 'Email Verification',
        'category': 'Account Security',
        'subject': 'Verify your {{ shop_name }} email',
        'body': (
            'Hello {{ display_name }},\n\n'
            'Please verify your email address for {{ shop_name }}:\n\n'
            '{{ verification_url }}\n\n'
            'This helps protect your account and keeps order, quote, and security notifications going to the right inbox.\n\n'
            'If you did not create or update this account, please ignore this email or contact our support team.\n\n'
            '{{ shop_name }}\n'
        ),
    },
    {
        'code': 'password_reset',
        'name': 'Password Reset',
        'category': 'Account Security',
        'subject': 'Reset your {{ shop_name }} password',
        'body': (
            'Hello {{ display_name }},\n\n'
            'We received a request to reset your {{ shop_name }} password.\n\n'
            'Set a new password here:\n\n'
            '{{ reset_url }}\n\n'
            'If you did not request this, you can ignore this email. Your password will stay unchanged.\n\n'
            '{{ shop_name }}\n'
        ),
    },
    {
        'code': 'email_two_factor',
        'name': 'Email Two-Factor Code',
        'category': 'Account Security',
        'subject': 'Your {{ shop_name }} sign-in code',
        'body': (
            'Hello {{ display_name }},\n\n'
            'Use this code to finish signing in to {{ shop_name }}:\n\n'
            '{{ code }}\n\n'
            'This code expires in 10 minutes.\n\n'
            'If you did not try to sign in, please change your password or contact support.\n\n'
            '{{ shop_name }}\n'
        ),
    },
    {
        'code': 'password_changed',
        'name': 'Password Changed',
        'category': 'Account Security',
        'subject': 'Your {{ shop_name }} password was changed',
        'body': (
            'Hello {{ display_name }},\n\n'
            'Your {{ shop_name }} password was changed successfully.\n\n'
            'If this was not you, please reset your password immediately and contact support.\n\n'
            '{{ shop_name }}\n'
        ),
    },
]


def seed_templates(apps, schema_editor):
    CommunicationEventType = apps.get_model('communication', 'CommunicationEventType')
    for template in TEMPLATES:
        CommunicationEventType.objects.get_or_create(
            code=template['code'],
            defaults={
                'name': template['name'],
                'category': template['category'],
                'email_subject_template': template['subject'],
                'email_body_template': template['body'],
                'email_body_html_template': '',
                'sms_template': '',
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ('communication', '__first__'),
        ('notifications', '0003_alter_emailnotification_event_type'),
    ]

    operations = [
        migrations.RunPython(seed_templates, migrations.RunPython.noop),
    ]
