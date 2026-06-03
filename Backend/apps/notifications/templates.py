from django.apps import apps


CUSTOM_COMMUNICATION_TEMPLATES = [
    {
        'code': 'account_registered',
        'name': 'Account Registered',
        'category': 'Account',
        'email_subject_template': 'Welcome to {{ shop_name }}',
        'email_body_template': (
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
        'email_subject_template': 'Verify your {{ shop_name }} email',
        'email_body_template': (
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
        'email_subject_template': 'Reset your {{ shop_name }} password',
        'email_body_template': (
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
        'email_subject_template': 'Your {{ shop_name }} sign-in code',
        'email_body_template': (
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
        'email_subject_template': 'Your {{ shop_name }} password was changed',
        'email_body_template': (
            'Hello {{ display_name }},\n\n'
            'Your {{ shop_name }} password was changed successfully.\n\n'
            'If this was not you, please reset your password immediately and contact support.\n\n'
            '{{ shop_name }}\n'
        ),
    },
]


def ensure_custom_communication_templates() -> None:
    CommunicationEventType = apps.get_model('communication', 'CommunicationEventType')
    for template in CUSTOM_COMMUNICATION_TEMPLATES:
        defaults = {
            'name': template['name'],
            'category': template['category'],
            'email_subject_template': template['email_subject_template'],
            'email_body_template': template['email_body_template'],
            'email_body_html_template': template.get('email_body_html_template', ''),
            'sms_template': template.get('sms_template', ''),
        }
        CommunicationEventType.objects.get_or_create(code=template['code'], defaults=defaults)
