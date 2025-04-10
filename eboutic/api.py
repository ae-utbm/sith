from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.exceptions import NotFound
from ninja_extra.permissions import IsAuthenticated

from counter.models import BillingInfo
from eboutic.models import Basket


@api_controller("/etransaction", permissions=[IsAuthenticated])
class EtransactionInfoController(ControllerBase):
    @route.get("/data", url_name="etransaction_data")
    def fetch_etransaction_data(self):
        """Generate the data to pay an eboutic command with paybox.

        The data is generated with the basket that is used by the current session.
        """
        basket = Basket.from_session(self.context.request.session)
        if basket is None:
            raise NotFound
        try:
            return dict(basket.get_e_transaction_data())
        except BillingInfo.DoesNotExist as e:
            raise NotFound from e
