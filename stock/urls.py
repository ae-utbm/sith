from django.urls import path

from stock.views.core import (
    StockCreateView,
    StockHomeView,
    StockUpdateView,
)
from stock.views.items import (
    ItemActionCreateView,
    ItemCreateView,
    ItemListView,
    ItemUpdateView,
)

urlpatterns = [
    path("<int:club_id>/create/", StockCreateView.as_view(), name="create"),
    path("<int:club_id>/edit/<int:stock_id>", StockUpdateView.as_view(), name="edit"),
    path("<int:club_id>/home/", StockHomeView.as_view(), name="home"),
    path(
        "<int:club_id>/stock/<int:stock_id>/items/create/",
        ItemCreateView.as_view(),
        name="items_create",
    ),
    path(
        "<int:club_id>/stock/<int:stock_id>/items/",
        ItemListView.as_view(),
        name="items_list",
    ),
    path(
        "<int:club_id>/stock/<int:stock_id>/items/<int:item_id>/edit/",
        ItemUpdateView.as_view(),
        name="item_edit",
    ),
    path(
        "<int:club_id>/stock/<int:stock_id>/actions/create",
        ItemActionCreateView.as_view(),
        name="action_create",
    ),
]
