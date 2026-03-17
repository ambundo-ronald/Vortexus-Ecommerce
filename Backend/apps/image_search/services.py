import hashlib
import logging
from functools import lru_cache
from io import BytesIO
from typing import Any

from django.apps import apps
from django.conf import settings
from opensearchpy.exceptions import OpenSearchException
from PIL import Image, UnidentifiedImageError

from apps.common.clients import get_opensearch_client
from apps.common.currency import convert_product_payload
from apps.common.products import serialize_product_card

logger = logging.getLogger(__name__)


class HashImageEmbeddingBackend:
    def embed_bytes(self, image_bytes: bytes) -> list[float]:
        digest = hashlib.sha256(image_bytes).digest()
        return [digest[idx % len(digest)] / 255 for idx in range(settings.EMBEDDING_DIMENSION)]


class ClipImageEmbeddingBackend:
    def __init__(self, model_name: str, device: str) -> None:
        from transformers import CLIPModel, CLIPProcessor

        import torch

        self._torch = torch
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.device = self._resolve_device(device)
        self.model.to(self.device)
        self.model.eval()

    def _resolve_device(self, preferred_device: str) -> str:
        if preferred_device == 'auto':
            if self._torch.cuda.is_available():
                return 'cuda'
            if hasattr(self._torch.backends, 'mps') and self._torch.backends.mps.is_available():
                return 'mps'
            return 'cpu'

        if preferred_device == 'cuda' and not self._torch.cuda.is_available():
            logger.warning('CLIP_DEVICE=cuda requested but CUDA unavailable. Falling back to cpu.')
            return 'cpu'

        if preferred_device == 'mps':
            if not hasattr(self._torch.backends, 'mps') or not self._torch.backends.mps.is_available():
                logger.warning('CLIP_DEVICE=mps requested but MPS unavailable. Falling back to cpu.')
                return 'cpu'

        return preferred_device

    def embed_bytes(self, image_bytes: bytes) -> list[float]:
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        inputs = self.processor(images=image, return_tensors='pt')
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with self._torch.inference_mode():
            features = self.model.get_image_features(**inputs)
            features = self._torch.nn.functional.normalize(features, p=2, dim=-1)

        vector = features[0].detach().cpu().tolist()
        if len(vector) != settings.EMBEDDING_DIMENSION:
            raise ValueError(
                f'Embedding dimension mismatch: expected {settings.EMBEDDING_DIMENSION}, got {len(vector)}'
            )

        return vector


@lru_cache(maxsize=1)
def get_embedding_backend() -> Any:
    backend_name = settings.IMAGE_EMBEDDING.get('BACKEND', 'clip').lower()
    if backend_name == 'hash':
        return HashImageEmbeddingBackend()

    try:
        model_name = settings.IMAGE_EMBEDDING.get('CLIP_MODEL_NAME', 'openai/clip-vit-base-patch32')
        device = settings.IMAGE_EMBEDDING.get('CLIP_DEVICE', 'cpu')
        return ClipImageEmbeddingBackend(model_name=model_name, device=device)
    except Exception as exc:
        logger.exception('CLIP backend unavailable, falling back to hash embeddings: %s', exc)
        return HashImageEmbeddingBackend()


class ImageEmbeddingService:
    def embed_image(self, image_file) -> list[float]:
        image_bytes = image_file.read()
        if hasattr(image_file, 'seek'):
            image_file.seek(0)

        if not image_bytes:
            raise ValueError('Cannot embed an empty image')

        try:
            return get_embedding_backend().embed_bytes(image_bytes)
        except UnidentifiedImageError as exc:
            raise ValueError('Unsupported image content') from exc


class ImageSearchService:
    def __init__(self) -> None:
        self.embedding_service = ImageEmbeddingService()

    def search_similar(
        self,
        image_file,
        top_k: int,
        category: str | None = None,
        display_currency: str | None = None,
    ) -> dict[str, Any]:
        query_vector = self.embedding_service.embed_image(image_file)

        try:
            return self._search_opensearch(
                query_vector=query_vector,
                top_k=top_k,
                category=category,
                display_currency=display_currency,
            )
        except (OpenSearchException, KeyError):
            return self._search_database_fallback(
                top_k=top_k,
                category=category,
                display_currency=display_currency,
            )

    def _search_opensearch(
        self,
        query_vector: list[float],
        top_k: int,
        category: str | None = None,
        display_currency: str | None = None,
    ) -> dict[str, Any]:
        client = get_opensearch_client()

        knn_clause = {
            'knn': {
                'embedding': {
                    'vector': query_vector,
                    'k': top_k,
                }
            }
        }

        if category:
            query: dict[str, Any] = {
                'bool': {
                    'must': [knn_clause],
                    'filter': [{'term': {'category_slug': category}}],
                }
            }
        else:
            query = knn_clause

        body = {
            'size': top_k,
            'query': query,
        }

        response = client.search(index=settings.SEARCH_INDEX_IMAGE_EMBEDDINGS, body=body)
        results = []

        for hit in response['hits']['hits']:
            source = hit.get('_source', {})
            results.append(
                convert_product_payload(
                {
                    'id': source.get('product_id'),
                    'title': source.get('title'),
                    'sku': source.get('sku'),
                    'price': source.get('price'),
                    'base_price': source.get('price'),
                    'currency': source.get('currency', 'USD'),
                    'base_currency': source.get('currency', 'USD'),
                    'thumbnail': source.get('thumbnail', ''),
                    'in_stock': source.get('in_stock', False),
                    'score': hit.get('_score'),
                },
                display_currency,
                )
            )

        return {
            'results': results,
            'meta': {'top_k': top_k},
            'source': 'opensearch',
        }

    def _search_database_fallback(
        self,
        top_k: int,
        category: str | None = None,
        display_currency: str | None = None,
    ) -> dict[str, Any]:
        Product = apps.get_model('catalogue', 'Product')

        queryset = Product.objects.filter(is_public=True).prefetch_related('stockrecords').order_by('-date_updated')
        if category:
            queryset = queryset.filter(categories__slug=category)

        products = queryset.distinct()[:top_k]
        results = [serialize_product_card(product=product, display_currency=display_currency) for product in products]

        return {
            'results': results,
            'meta': {'top_k': top_k},
            'source': 'database',
        }
