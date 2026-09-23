from core.views.widgets.ajax_select import AutoCompleteSelect


class StockItemSelect(AutoCompleteSelect):
    def get_context(self, name, value, attrs):
        self._quantities = {
            str(item.pk): item.quantity
            for item in self.choices.queryset.only("pk", "quantity", "item__name")
        }
        return super().get_context(name, value, attrs)

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        quantity = self._quantities.get(str(value))
        if quantity is not None:
            option["attrs"]["data-quantity"] = str(quantity)
        return option
