from django.test import TestCase

from counter.baker_recipes import product_recipe
from counter.forms import ProductFormulaForm


class TestFormulaForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.products = product_recipe.make(
            selling_price=iter([1.5, 1, 1]),
            special_selling_price=iter([1.4, 0.9, 0.9]),
            _quantity=3,
            _bulk_create=True,
        )

    def test_ok(self):
        form = ProductFormulaForm(
            data={
                "result": self.products[0].id,
                "products": [self.products[1].id, self.products[2].id],
            }
        )
        assert form.is_valid()
        formula = form.save()
        assert formula.result == self.products[0]
        assert set(formula.products.all()) == set(self.products[1:])

    def test_price_invalid(self):
        self.products[0].selling_price = 2.1
        self.products[0].save()
        form = ProductFormulaForm(
            data={
                "result": self.products[0].id,
                "products": [self.products[1].id, self.products[2].id],
            }
        )
        assert not form.is_valid()
        assert form.errors == {
            "result": [
                "Le résultat ne peut pas être plus cher "
                "que le total des autres produits."
            ]
        }

    def test_product_both_in_result_and_products(self):
        form = ProductFormulaForm(
            data={
                "result": self.products[0].id,
                "products": [self.products[0].id, self.products[1].id],
            }
        )
        assert not form.is_valid()
        assert form.errors == {
            "__all__": [
                "Un même produit ne peut pas être à la fois "
                "le résultat et un élément de la formule."
            ]
        }
