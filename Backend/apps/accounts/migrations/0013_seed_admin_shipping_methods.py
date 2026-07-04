from decimal import Decimal

from django.db import migrations


DEFAULT_METHODS = [
    {
        'code': 'dispatch-hub-pickup',
        'name': 'Dispatch Hub Pickup',
        'description': 'Collect stocked parts and equipment from the Reesolmart dispatch hub.',
        'default_weight': Decimal('1.000'),
        'bands': [
            {'upper_limit': Decimal('999999.000'), 'charge': Decimal('0.00')},
        ],
    },
    {
        'code': 'standard-freight',
        'name': 'Standard Freight',
        'description': 'Standard freight for stocked pumps, filters, treatment systems, and accessories.',
        'default_weight': Decimal('1.000'),
        'bands': [
            {'upper_limit': Decimal('250.000'), 'charge': Decimal('35.00')},
        ],
    },
    {
        'code': 'priority-dispatch',
        'name': 'Priority Dispatch',
        'description': 'Priority dispatch for urgent replacements and service-critical equipment.',
        'default_weight': Decimal('1.000'),
        'bands': [
            {'upper_limit': Decimal('80.000'), 'charge': Decimal('85.00')},
        ],
    },
]


def seed_admin_shipping_methods(apps, schema_editor):
    WeightBased = apps.get_model('shipping', 'WeightBased')
    WeightBand = apps.get_model('shipping', 'WeightBand')

    for data in DEFAULT_METHODS:
        method, created = WeightBased.objects.get_or_create(
            code=data['code'],
            defaults={
                'name': data['name'],
                'description': data['description'],
                'default_weight': data['default_weight'],
            },
        )
        if not created:
            continue

        for band in data['bands']:
            WeightBand.objects.create(
                method=method,
                upper_limit=band['upper_limit'],
                charge=band['charge'],
            )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_productmongoreference'),
        ('shipping', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_admin_shipping_methods, migrations.RunPython.noop),
    ]
