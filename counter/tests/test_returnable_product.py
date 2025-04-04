import pytest
from model_bakery import baker

from counter.baker_recipes import refill_recipe, sale_recipe
from counter.models import Customer, ReturnableProduct


@pytest.mark.django_db
def test_update_returnable_product_balance():
    Customer.objects.all().delete()
    ReturnableProduct.objects.all().delete()
    customers = baker.make(Customer, _quantity=2, _bulk_create=True)
    refill_recipe.make(customer=iter(customers), _quantity=2, amount=100)
    returnable = baker.make(ReturnableProduct)
    sale_recipe.make(
        unit_price=0, quantity=3, product=returnable.product, customer=customers[0]
    )
    sale_recipe.make(
        unit_price=0, quantity=1, product=returnable.product, customer=customers[0]
    )
    sale_recipe.make(
        unit_price=0,
        quantity=2,
        product=returnable.returned_product,
        customer=customers[0],
    )
    sale_recipe.make(
        unit_price=0, quantity=4, product=returnable.product, customer=customers[1]
    )

    returnable.update_balances()
    assert list(
        returnable.balances.order_by("customer_id").values("customer_id", "balance")
    ) == [
        {"customer_id": customers[0].pk, "balance": 2},
        {"customer_id": customers[1].pk, "balance": 4},
    ]
