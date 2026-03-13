from django.db import migrations


COUNTRIES = [
    {
        'iso_3166_1_a2': 'KE',
        'iso_3166_1_a3': 'KEN',
        'iso_3166_1_numeric': '404',
        'name': 'Kenya',
        'printable_name': 'Kenya',
        'display_order': 1,
        'is_shipping_country': True,
    },
    {
        'iso_3166_1_a2': 'UG',
        'iso_3166_1_a3': 'UGA',
        'iso_3166_1_numeric': '800',
        'name': 'Uganda',
        'printable_name': 'Uganda',
        'display_order': 2,
        'is_shipping_country': True,
    },
    {
        'iso_3166_1_a2': 'TZ',
        'iso_3166_1_a3': 'TZA',
        'iso_3166_1_numeric': '834',
        'name': 'Tanzania, United Republic of',
        'printable_name': 'Tanzania',
        'display_order': 3,
        'is_shipping_country': True,
    },
    {
        'iso_3166_1_a2': 'RW',
        'iso_3166_1_a3': 'RWA',
        'iso_3166_1_numeric': '646',
        'name': 'Rwanda',
        'printable_name': 'Rwanda',
        'display_order': 4,
        'is_shipping_country': True,
    },
    {
        'iso_3166_1_a2': 'ET',
        'iso_3166_1_a3': 'ETH',
        'iso_3166_1_numeric': '231',
        'name': 'Ethiopia',
        'printable_name': 'Ethiopia',
        'display_order': 5,
        'is_shipping_country': True,
    },
]


def seed_countries(apps, schema_editor):
    Country = apps.get_model('address', 'Country')

    for payload in COUNTRIES:
        Country.objects.update_or_create(
            iso_3166_1_a2=payload['iso_3166_1_a2'],
            defaults=payload,
        )


def unseed_countries(apps, schema_editor):
    Country = apps.get_model('address', 'Country')
    Country.objects.filter(iso_3166_1_a2__in=[item['iso_3166_1_a2'] for item in COUNTRIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('address', '0006_auto_20181115_1953'),
    ]

    operations = [
        migrations.RunPython(seed_countries, unseed_countries),
    ]
