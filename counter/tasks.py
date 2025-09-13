# Create your tasks here

from celery import shared_task

from counter.models import Product


@shared_task
def archive_product(product_id: int):
    product = Product.objects.get(id=product_id)
    product.archived = True
    product.save()
