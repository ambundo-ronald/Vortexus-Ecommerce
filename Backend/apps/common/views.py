from django.apps import apps
from django.db.models import Q
from django.views.generic import TemplateView


class IndustrialHomeView(TemplateView):
    template_name = "oscar/home/industrial_home.html"

    CURATED_SECTIONS = (
        {
            "title": "Borehole Pumps",
            "subtitle": "Submersible, solar and surface pumping systems",
            "keywords": ["borehole", "submersible", "solar pump", "water pump", "surface pump"],
        },
        {
            "title": "Water Treatment",
            "subtitle": "Filtration, dosing and disinfection units",
            "keywords": ["filter", "ro", "uv", "chlorine", "treatment", "purifier"],
        },
        {
            "title": "Pipes and Accessories",
            "subtitle": "Pressure control, fittings and installation accessories",
            "keywords": ["pipe", "fitting", "valve", "pressure", "tank", "accessory"],
        },
    )

    def _get_public_products(self):
        Product = apps.get_model("catalogue", "Product")
        return (
            Product.objects.filter(is_public=True)
            .exclude(structure="parent")
            .select_related("product_class")
            .prefetch_related("images")
        )

    def _products_for_keywords(self, keywords, limit=8):
        query = Q()
        for keyword in keywords:
            query |= Q(title__icontains=keyword) | Q(description__icontains=keyword)
        return list(self._get_public_products().filter(query).distinct()[:limit])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Category = apps.get_model("catalogue", "Category")

        root_categories = Category.objects.filter(depth=1).order_by("name")[:10]
        featured_products = list(self._get_public_products()[:8])

        curated_sections = []
        for section in self.CURATED_SECTIONS:
            curated_sections.append(
                {
                    "title": section["title"],
                    "subtitle": section["subtitle"],
                    "products": self._products_for_keywords(section["keywords"], limit=8),
                }
            )

        context.update(
            {
                "root_categories": root_categories,
                "featured_products": featured_products,
                "curated_sections": curated_sections,
                "capabilities": [
                    {
                        "title": "Fast Text Search",
                        "description": "Search by model, SKU, brand and application with filters.",
                        "href": "/search/",
                    },
                    {
                        "title": "Image Search",
                        "description": "Upload a part photo to find similar pumps and accessories.",
                        "href": "/api/v1/search/image/",
                    },
                    {
                        "title": "Smart Recommendations",
                        "description": "Get related products and compatible accessories in real time.",
                        "href": "/api/v1/recommendations/",
                    },
                ],
            }
        )
        return context
