from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.api.marketing_content_serializers import MarketingBlockSerializer

from .models import MarketingBlock


class MarketingBlockSerializerTests(TestCase):
    def test_image_placement_requires_image(self):
        serializer = MarketingBlockSerializer(
            data={
                'title': 'Homepage hero',
                'slug': 'homepage-hero',
                'placement': MarketingBlock.PLACEMENT_HOME_HERO,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('image_url', serializer.errors)

    def test_top_category_requires_storefront_link(self):
        serializer = MarketingBlockSerializer(
            data={
                'title': 'Pumps',
                'slug': 'top-pumps',
                'placement': MarketingBlock.PLACEMENT_TOP_CATEGORY,
                'image_url': '/media/pumps.webp',
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('cta_url', serializer.errors)

    def test_rejects_unsafe_cta_url(self):
        serializer = MarketingBlockSerializer(
            data={
                'title': 'Featured pumps',
                'slug': 'featured-pumps',
                'placement': MarketingBlock.PLACEMENT_FEATURED,
                'cta_url': 'javascript:alert(1)',
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('cta_url', serializer.errors)


class PublicMarketingBlockCollectionTests(TestCase):
    endpoint = '/api/v1/content/marketing-blocks/'

    def setUp(self):
        self.client = APIClient()
        self.now = timezone.now()

    def create_block(self, **overrides):
        defaults = {
            'title': 'Announcement',
            'slug': f"announcement-{MarketingBlock.objects.count() + 1}",
            'placement': MarketingBlock.PLACEMENT_ANNOUNCEMENT,
            'is_active': True,
        }
        defaults.update(overrides)
        return MarketingBlock.objects.create(**defaults)

    def test_returns_current_renderable_blocks_grouped_and_sorted(self):
        second = self.create_block(title='Second', slug='second', sort_order=2)
        first = self.create_block(title='First', slug='first', sort_order=1)
        self.create_block(title='Inactive', slug='inactive', is_active=False)
        self.create_block(
            title='Future',
            slug='future',
            starts_at=self.now + timedelta(hours=1),
        )
        self.create_block(
            title='Expired',
            slug='expired',
            ends_at=self.now - timedelta(hours=1),
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [block['id'] for block in response.data['results']],
            [first.id, second.id],
        )
        self.assertEqual(
            [block['id'] for block in response.data['by_placement']['announcement']],
            [first.id, second.id],
        )
        self.assertIn('top_category', response.data['by_placement'])
        self.assertIn('generated_at', response.data)

    def test_omits_invalid_legacy_image_and_category_blocks(self):
        self.create_block(
            title='Broken hero',
            slug='broken-hero',
            placement=MarketingBlock.PLACEMENT_HOME_HERO,
            image_url='   ',
        )
        self.create_block(
            title='Broken category',
            slug='broken-category',
            placement=MarketingBlock.PLACEMENT_TOP_CATEGORY,
            image_url='/media/category.webp',
            cta_url=' ',
        )
        valid = self.create_block(
            title='Valid category',
            slug='valid-category',
            placement=MarketingBlock.PLACEMENT_TOP_CATEGORY,
            image_url='/media/category.webp',
            cta_url='/catalog/category/pumps',
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([block['id'] for block in response.data['results']], [valid.id])
