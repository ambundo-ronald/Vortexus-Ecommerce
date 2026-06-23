from __future__ import annotations

from vortexus_ecommerce_integration.constants import CUSTOM_SOURCE_FIELD, SOURCE_VALUE


def on_submit(doc, method=None) -> None:
    if doc.get(CUSTOM_SOURCE_FIELD) == SOURCE_VALUE:
        doc.add_comment("Info", "Submitted from Vortexus ecommerce channel.")

