from django.conf import settings
from django.db import models
from django.utils import timezone


class MarketingBlock(models.Model):
    PLACEMENT_HOME_HERO = 'home_hero'
    PLACEMENT_ANNOUNCEMENT = 'announcement'
    PLACEMENT_PROMO_BANNER = 'promo_banner'
    PLACEMENT_FEATURED = 'featured'
    PLACEMENT_BRAND_STRIP = 'brand_strip'
    PLACEMENT_TOP_CATEGORY = 'top_category'

    PLACEMENT_CHOICES = [
        (PLACEMENT_HOME_HERO, 'Homepage hero'),
        (PLACEMENT_ANNOUNCEMENT, 'Announcement strip'),
        (PLACEMENT_PROMO_BANNER, 'Promo banner'),
        (PLACEMENT_FEATURED, 'Featured block'),
        (PLACEMENT_BRAND_STRIP, 'Brand strip'),
        (PLACEMENT_TOP_CATEGORY, 'Top Category'),
    ]

    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    placement = models.CharField(max_length=40, choices=PLACEMENT_CHOICES, db_index=True)
    headline = models.CharField(max_length=180, blank=True)
    body = models.TextField(blank=True)
    eyebrow = models.CharField(max_length=80, blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    image_alt = models.CharField(max_length=160, blank=True)
    cta_text = models.CharField(max_length=80, blank=True)
    cta_url = models.CharField(max_length=240, blank=True)
    background_color = models.CharField(max_length=24, blank=True)
    text_color = models.CharField(max_length=24, blank=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    starts_at = models.DateTimeField(null=True, blank=True, db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['placement', 'sort_order', 'id']
        indexes = [
            models.Index(fields=['placement', 'is_active', 'sort_order']),
            models.Index(fields=['starts_at', 'ends_at']),
        ]

    def __str__(self):
        return f'{self.title} ({self.placement})'

    @property
    def is_current(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and self.starts_at > now:
            return False
        if self.ends_at and self.ends_at <= now:
            return False
        return True


class MarketingMediaAsset(models.Model):
    CATEGORY_MARKETING_BLOCK = 'marketing_block'

    CATEGORY_CHOICES = [
        (CATEGORY_MARKETING_BLOCK, 'Marketing block'),
    ]

    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default=CATEGORY_MARKETING_BLOCK, db_index=True)
    title = models.CharField(max_length=160, blank=True)
    image = models.ImageField(upload_to='marketing-blocks/%Y/%m/')
    alt_text = models.CharField(max_length=160, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='marketing_media_assets',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['category', '-created_at']),
        ]

    def __str__(self):
        return self.title or self.image.name
