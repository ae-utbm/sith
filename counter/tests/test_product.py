from io import BytesIO
from uuid import uuid4

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker
from PIL import Image

from counter.models import Product, ProductType


@pytest.mark.django_db
@pytest.mark.parametrize("model", [Product, ProductType])
def test_resize_product_icon(model):
    """Test that the product icon is resized when saved."""
    # Product and ProductType icons have a height of 70px
    # so this image should be resized to 50x70
    img = Image.new("RGB", (100, 140))
    content = BytesIO()
    img.save(content, format="JPEG")
    name = str(uuid4())

    product = baker.make(
        model,
        icon=SimpleUploadedFile(
            f"{name}.jpg", content.getvalue(), content_type="image/jpeg"
        ),
    )

    assert product.icon.width == 50
    assert product.icon.height == 70
    assert product.icon.name == f"products/{name}.webp"
    assert Image.open(product.icon).format == "WEBP"
