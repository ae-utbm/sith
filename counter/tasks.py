# Create your tasks here

from celery import shared_task

from counter.models import Counter, Product


@shared_task
def archive_product(*, product_id: int, **kwargs):
    product = Product.objects.get(id=product_id)
    product.archived = True
    product.save()


@shared_task
def change_counters(*, product_id: int, counters: list[int], **kwargs):
    product = Product.objects.get(id=product_id)
    counters = Counter.objects.filter(id__in=counters)
    product.counters.set(counters)
