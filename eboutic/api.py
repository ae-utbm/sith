from django.shortcuts import get_object_or_404
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.exceptions import NotFound, PermissionDenied
from ninja_extra.permissions import IsAuthenticated
from pydantic import NonNegativeInt

from core.models import User
from counter.models import BillingInfo, Customer
from eboutic.models import Basket
from eboutic.schemas import BillingInfoSchema


@api_controller("/etransaction", permissions=[IsAuthenticated])
class EtransactionInfoController(ControllerBase):
    @route.put("/billing-info/{user_id}", url_name="put_billing_info")
    def put_user_billing_info(self, user_id: NonNegativeInt, info: BillingInfoSchema):
        """Update or create the billing info of this user."""
        if user_id == self.context.request.user.id:
            user = self.context.request.user
        elif self.context.request.user.is_root:
            user = get_object_or_404(User, pk=user_id)
        else:
            raise PermissionDenied
        customer, _ = Customer.get_or_create(user)
        BillingInfo.objects.update_or_create(
            customer=customer, defaults=info.model_dump(exclude_none=True)
        )

    @route.get("/data", url_name="etransaction_data")
    def fetch_etransaction_data(self):
        """Generate the data to pay an eboutic command with paybox.

        The data is generated with the basket that is used by the current session.
        """
        basket = Basket.from_session(self.context.request.session)
        if basket is None:
            raise NotFound
        return dict(basket.get_e_transaction_data())
