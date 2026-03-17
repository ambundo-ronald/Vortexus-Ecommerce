import csv
from decimal import Decimal
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.utils import timezone
from oscar.core.loading import get_model
from PIL import Image, ImageDraw

from apps.marketplace.orders import ensure_supplier_order_groups


class Command(BaseCommand):
    help = 'Create idempotent demo/bootstrap data for local development, demos, and API integration.'

    def add_arguments(self, parser):
        parser.add_argument('--with-order', action='store_true', help='Create a sample customer order.')
        parser.add_argument('--with-reviews', action='store_true', help='Create sample product reviews.')
        parser.add_argument('--with-wishlist', action='store_true', help='Create a sample wishlist for the demo customer.')

    @transaction.atomic
    def handle(self, *args, **options):
        self.User = get_user_model()
        self.CustomerProfile = apps.get_model('accounts', 'CustomerProfile')
        self.Partner = apps.get_model('partner', 'Partner')
        self.StockRecord = apps.get_model('partner', 'StockRecord')
        self.Product = apps.get_model('catalogue', 'Product')
        self.SupplierProfile = apps.get_model('marketplace', 'SupplierProfile')
        self.Country = apps.get_model('address', 'Country')
        self.Order = get_model('order', 'Order')
        self.Line = get_model('order', 'Line')
        self.OrderStatusChange = get_model('order', 'OrderStatusChange')
        self.ShippingAddress = get_model('order', 'ShippingAddress')
        self.Review = get_model('reviews', 'ProductReview')
        self.WishList = get_model('wishlists', 'WishList')
        self.WishListLine = get_model('wishlists', 'Line')
        self.Site = get_model('sites', 'Site')

        sample_dir = Path(settings.BASE_DIR) / 'sample_data' / 'demo_bootstrap'
        sample_dir.mkdir(parents=True, exist_ok=True)
        image_dir = sample_dir / 'images'
        image_dir.mkdir(parents=True, exist_ok=True)

        csv_path = sample_dir / 'demo_catalog.csv'
        self._generate_demo_images(image_dir)
        self._write_demo_csv(csv_path)

        call_command(
            'import_industrial_catalog',
            str(csv_path),
            '--partner',
            'Demo House Partner',
            '--product-class',
            'Industrial Product',
            '--default-currency',
            'USD',
        )

        self._ensure_admin_user()
        customer_user = self._ensure_customer_user()
        supplier_a = self._ensure_supplier_user(
            username='supplier_alpha',
            email='supplier.alpha@vortexus.demo',
            company_name='AquaFlow Pumps Ltd',
            code='demo_supplier_alpha',
        )
        supplier_b = self._ensure_supplier_user(
            username='supplier_beta',
            email='supplier.beta@vortexus.demo',
            company_name='ClearWater Treatment Systems',
            code='demo_supplier_beta',
        )

        imported_products = {
            product.upc: product
            for product in self.Product.objects.filter(upc__in=['DEMO-PUMP-001', 'DEMO-TANK-001']).prefetch_related('stockrecords')
        }

        self._assign_house_partner_stock(imported_products['DEMO-PUMP-001'], 'Demo House Partner', Decimal('1299.00'), 18)
        self._assign_house_partner_stock(imported_products['DEMO-TANK-001'], 'Demo House Partner', Decimal('349.00'), 25)

        supplier_product_a = self._upsert_supplier_product(
            supplier_profile=supplier_a,
            upc='DEMO-SUP-RO-001',
            title='Reverse Osmosis Skid 2500LPH',
            description='Supplier-owned reverse osmosis treatment skid for commercial installations.',
            category_path='Water Treatment > Reverse Osmosis Systems',
            price=Decimal('4250.00'),
            num_in_stock=6,
        )
        supplier_product_b = self._upsert_supplier_product(
            supplier_profile=supplier_b,
            upc='DEMO-SUP-SOLAR-001',
            title='Solar Borehole Pump Controller',
            description='Supplier-owned smart controller for solar-powered borehole pump systems.',
            category_path='Controllers > Solar Pump Controllers',
            price=Decimal('899.00'),
            num_in_stock=14,
        )

        if options['with_order']:
            self._ensure_demo_order(customer_user, imported_products['DEMO-PUMP-001'], supplier_product_a)

        if options['with_reviews']:
            self._ensure_demo_review(customer_user, imported_products['DEMO-PUMP-001'])

        if options['with_wishlist']:
            self._ensure_demo_wishlist(customer_user, [imported_products['DEMO-TANK-001'], supplier_product_b])

        self.stdout.write(self.style.SUCCESS('Demo/bootstrap data is ready.'))
        self.stdout.write('Admin user: admin@vortexus.demo / Adminpass123!')
        self.stdout.write('Customer user: customer@vortexus.demo / Customerpass123!')
        self.stdout.write('Supplier user: supplier.alpha@vortexus.demo / Supplierpass123!')
        self.stdout.write('Supplier user: supplier.beta@vortexus.demo / Supplierpass123!')
        self.stdout.write(f'Demo catalog CSV: {csv_path}')

    def _generate_demo_images(self, image_dir: Path) -> None:
        images = {
            'demo_pump.png': ('#0f5cc0', 'Borehole Pump'),
            'demo_tank.png': ('#118a55', 'Pressure Tank'),
            'demo_ro.png': ('#b3531a', 'RO System'),
            'demo_controller.png': ('#6b4cc2', 'Solar Ctrl'),
        }
        for filename, (color, label) in images.items():
            image_path = image_dir / filename
            if image_path.exists():
                continue
            image = Image.new('RGB', (1600, 1200), color=color)
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((110, 110, 1490, 1090), radius=42, outline='white', width=8)
            draw.text((140, 520), f'Vortexus Demo\n{label}', fill='white')
            image.save(image_path, format='PNG')

    def _write_demo_csv(self, csv_path: Path) -> None:
        rows = [
            {
                'upc': 'DEMO-PUMP-001',
                'title': 'Industrial Borehole Pump 5HP',
                'description': '5HP borehole pump for agricultural and commercial water supply projects.',
                'category_path': 'Pumps > Borehole Pumps',
                'price': '1299.00',
                'num_in_stock': '18',
                'partner_sku': 'DEMO-PUMP-001',
                'is_public': 'true',
                'image_path': 'images/demo_pump.png',
                'image_caption': 'Borehole pump',
                'attr__brand': 'Vortexus Demo',
                'attr__flow_rate': '7m3/h',
                'attr__head': '110m',
            },
            {
                'upc': 'DEMO-TANK-001',
                'title': 'Pressure Tank 300L',
                'description': 'Heavy-duty pressure tank for pump systems and booster applications.',
                'category_path': 'Accessories > Pressure Tanks',
                'price': '349.00',
                'num_in_stock': '25',
                'partner_sku': 'DEMO-TANK-001',
                'is_public': 'true',
                'image_path': 'images/demo_tank.png',
                'image_caption': 'Pressure tank',
                'attr__brand': 'Vortexus Demo',
                'attr__capacity': '300L',
                'attr__material': 'Powder-coated steel',
            },
        ]
        with csv_path.open('w', encoding='utf-8', newline='') as handle:
            fieldnames = []
            for row in rows:
                for key in row.keys():
                    if key not in fieldnames:
                        fieldnames.append(key)
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _ensure_admin_user(self):
        user, _ = self.User.objects.get_or_create(
            username='admin_demo',
            defaults={'email': 'admin@vortexus.demo', 'is_staff': True, 'is_superuser': True},
        )
        user.email = 'admin@vortexus.demo'
        user.is_staff = True
        user.is_superuser = True
        user.set_password('Adminpass123!')
        user.save()
        return user

    def _ensure_customer_user(self):
        user, _ = self.User.objects.get_or_create(
            username='customer_demo',
            defaults={'email': 'customer@vortexus.demo', 'first_name': 'Demo', 'last_name': 'Customer'},
        )
        user.email = 'customer@vortexus.demo'
        user.first_name = 'Demo'
        user.last_name = 'Customer'
        user.set_password('Customerpass123!')
        user.save()

        profile, _ = self.CustomerProfile.objects.get_or_create(user=user)
        profile.phone = '+254700111222'
        profile.company = 'Demo Project Co.'
        profile.country_code = 'KE'
        profile.preferred_currency = 'KES'
        profile.receive_order_updates = True
        profile.receive_marketing_emails = False
        profile.save()
        return user

    def _ensure_supplier_user(self, *, username: str, email: str, company_name: str, code: str):
        user, _ = self.User.objects.get_or_create(username=username, defaults={'email': email, 'first_name': 'Demo'})
        user.email = email
        user.first_name = company_name.split()[0]
        user.last_name = 'Supplier'
        user.set_password('Supplierpass123!')
        user.save()

        partner, _ = self.Partner.objects.get_or_create(code=code, defaults={'name': company_name})
        partner.name = company_name
        partner.save(update_fields=['name'])

        supplier_profile, _ = self.SupplierProfile.objects.get_or_create(
            user=user,
            defaults={
                'partner': partner,
                'company_name': company_name,
                'contact_name': f'{company_name} Rep',
                'phone': '+254700333444',
                'country_code': 'KE',
                'status': self.SupplierProfile.STATUS_APPROVED,
            },
        )
        supplier_profile.partner = partner
        supplier_profile.company_name = company_name
        supplier_profile.contact_name = f'{company_name} Rep'
        supplier_profile.phone = '+254700333444'
        supplier_profile.country_code = 'KE'
        supplier_profile.status = self.SupplierProfile.STATUS_APPROVED
        supplier_profile.save()
        return supplier_profile

    def _assign_house_partner_stock(self, product, partner_name: str, price: Decimal, num_in_stock: int):
        partner = self.Partner.objects.get(name=partner_name)
        stockrecord, _ = self.StockRecord.objects.get_or_create(
            product=product,
            partner=partner,
            defaults={
                'partner_sku': product.upc,
                'price_currency': 'USD',
                'price': price,
                'num_in_stock': num_in_stock,
            },
        )
        stockrecord.partner_sku = product.upc
        stockrecord.price_currency = 'USD'
        stockrecord.price = price
        stockrecord.num_in_stock = num_in_stock
        stockrecord.save()

    def _upsert_supplier_product(self, *, supplier_profile, upc: str, title: str, description: str, category_path: str, price: Decimal, num_in_stock: int):
        ProductClass = apps.get_model('catalogue', 'ProductClass')
        product_class, _ = ProductClass.objects.get_or_create(name='Industrial Product')
        product, _ = self.Product.objects.get_or_create(
            upc=upc,
            defaults={
                'title': title,
                'description': description,
                'is_public': True,
                'product_class': product_class,
                'structure': getattr(self.Product, 'STANDALONE', 'standalone'),
            },
        )
        product.title = title
        product.description = description
        product.is_public = True
        product.product_class = product_class
        product.structure = getattr(self.Product, 'STANDALONE', 'standalone')
        product.save()

        category = self._ensure_category_path(category_path)
        if category:
            product.categories.set([category])

        stockrecord, _ = self.StockRecord.objects.get_or_create(
            product=product,
            partner=supplier_profile.partner,
            defaults={
                'partner_sku': upc,
                'price_currency': 'USD',
                'price': price,
                'num_in_stock': num_in_stock,
            },
        )
        stockrecord.partner_sku = upc
        stockrecord.price_currency = 'USD'
        stockrecord.price = price
        stockrecord.num_in_stock = num_in_stock
        stockrecord.save()
        return product

    def _ensure_category_path(self, category_path: str):
        Category = apps.get_model('catalogue', 'Category')
        segments = [segment.strip() for segment in category_path.split('>') if segment.strip()]
        if not segments:
            return None
        parent = None
        for segment in segments:
            slug = segment.lower().replace(' ', '-')
            if parent is None:
                node = Category.get_root_nodes().filter(name__iexact=segment).first()
                if node is None:
                    node = Category.add_root(name=segment, slug=slug, is_public=True)
            else:
                node = parent.get_children().filter(name__iexact=segment).first()
                if node is None:
                    node = parent.add_child(name=segment, slug=slug, is_public=True)
            parent = node
        return parent

    def _ensure_demo_order(self, customer_user, product_a, product_b):
        country = self.Country.objects.get(iso_3166_1_a2='KE')
        shipping_address, _ = self.ShippingAddress.objects.get_or_create(
            first_name='Demo',
            last_name='Customer',
            line1='Westlands Road',
            line4='Nairobi',
            postcode='00100',
            country=country,
            defaults={'phone_number': '+254700111222', 'notes': 'Demo delivery address'},
        )
        shipping_address.phone_number = '+254700111222'
        shipping_address.notes = 'Demo delivery address'
        shipping_address.save()

        site = self.Site.objects.get(id=settings.SITE_ID)
        order, _ = self.Order.objects.get_or_create(
            number='DEMO-ORDER-1001',
            defaults={
                'site': site,
                'user': customer_user,
                'currency': 'USD',
                'total_incl_tax': Decimal('0.00'),
                'total_excl_tax': Decimal('0.00'),
                'shipping_incl_tax': Decimal('0.00'),
                'shipping_excl_tax': Decimal('0.00'),
                'shipping_tax_code': 'KE-shipping',
                'shipping_address': shipping_address,
                'shipping_method': 'Standard Freight',
                'shipping_code': 'standard-freight',
                'status': 'Pending',
                'date_placed': timezone.now(),
            },
        )
        order.user = customer_user
        order.site = site
        order.currency = 'USD'
        order.shipping_address = shipping_address
        order.shipping_method = 'Standard Freight'
        order.shipping_code = 'standard-freight'
        order.shipping_tax_code = 'KE-shipping'
        order.status = 'Pending'
        order.date_placed = timezone.now()
        order.save()

        self.Line.objects.filter(order=order).delete()
        self.OrderStatusChange.objects.filter(order=order).delete()

        totals_excl = Decimal('0.00')
        totals_incl = Decimal('0.00')
        for index, product in enumerate([product_a, product_b], start=1):
            stockrecord = product.stockrecords.select_related('partner').order_by('id').first()
            quantity = 1
            unit_excl = stockrecord.price or Decimal('0.00')
            unit_incl = (unit_excl * Decimal('1.16')).quantize(Decimal('0.01'))
            line_excl = unit_excl * quantity
            line_incl = unit_incl * quantity
            self.Line.objects.create(
                order=order,
                partner=stockrecord.partner,
                partner_name=stockrecord.partner.name,
                partner_sku=stockrecord.partner_sku or product.upc,
                stockrecord=stockrecord,
                product=product,
                title=product.title,
                upc=product.upc,
                quantity=quantity,
                line_price_incl_tax=line_incl,
                line_price_excl_tax=line_excl,
                line_price_before_discounts_incl_tax=line_incl,
                line_price_before_discounts_excl_tax=line_excl,
                unit_price_incl_tax=unit_incl,
                unit_price_excl_tax=unit_excl,
                tax_code='KE-standard',
                status='processing' if index == 1 else 'pending',
                num_allocated=quantity,
                allocation_cancelled=0,
            )
            totals_excl += line_excl
            totals_incl += line_incl

        order.total_excl_tax = totals_excl + Decimal('35.00')
        order.total_incl_tax = totals_incl + Decimal('40.60')
        order.shipping_excl_tax = Decimal('35.00')
        order.shipping_incl_tax = Decimal('40.60')
        order.save(update_fields=['total_excl_tax', 'total_incl_tax', 'shipping_excl_tax', 'shipping_incl_tax', 'status', 'date_placed'])

        self.OrderStatusChange.objects.create(order=order, old_status='', new_status='Pending')
        ensure_supplier_order_groups(order)
        return order

    def _ensure_demo_review(self, customer_user, product):
        review, _ = self.Review.objects.get_or_create(
            product=product,
            user=customer_user,
            defaults={
                'title': 'Strong field performance',
                'score': 5,
                'body': 'Installed smoothly and delivered consistent output for our demo project.',
                'status': self.Review.APPROVED,
            },
        )
        review.title = 'Strong field performance'
        review.score = 5
        review.body = 'Installed smoothly and delivered consistent output for our demo project.'
        review.status = self.Review.APPROVED
        review.save()

    def _ensure_demo_wishlist(self, customer_user, products):
        wishlist, _ = self.WishList.objects.get_or_create(owner=customer_user, name='Saved Items')
        for product in products:
            self.WishListLine.objects.get_or_create(wishlist=wishlist, product=product)
