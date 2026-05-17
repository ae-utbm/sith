from typing import Any

from ninja import Status
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.exceptions import NotFound

from api.permissions import CanView
from counter.models import BillingInfo
from eboutic.models import Basket


@api_controller("/etransaction", permissions=[CanView])
class EtransactionInfoController(ControllerBase):
    @route.get(
        "/data/{basket_id}",
        url_name="etransaction_data",
        response={200: dict[str, Any], 410: str},
    )
    def fetch_etransaction_data(self, basket_id: int):
        """Generate the data to pay an eboutic command with paybox.

        The data is generated with the basket that is used by the current session.
        """
        basket: Basket = self.get_object_or_exception(Basket, pk=basket_id)
        if basket.is_expired:
            return Status(410, "This basket is expired.")
        try:
            return dict(basket.get_e_transaction_data())
        except BillingInfo.DoesNotExist as e:
            raise NotFound from e
