from model_bakery.recipe import Recipe, foreign_key

from club.models import Club
from core.models import User
from counter.models import Counter, Price, Product, Refilling, Selling

counter_recipe = Recipe(Counter)
product_recipe = Recipe(Product, club=foreign_key(Recipe(Club)))
price_recipe = Recipe(Price, product=foreign_key(product_recipe))
sale_recipe = Recipe(
    Selling,
    product=foreign_key(product_recipe),
    counter=foreign_key(counter_recipe),
    seller=foreign_key(Recipe(User)),
    club=foreign_key(Recipe(Club)),
)
refill_recipe = Recipe(
    Refilling, counter=foreign_key(counter_recipe), operator=foreign_key(Recipe(User))
)
