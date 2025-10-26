import hmac
from urllib.parse import unquote

import pydantic
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import FormView, TemplateView
from ninja import Schema
from ninja_extra.shortcuts import get_object_or_none
from pydantic import HttpUrl

from api.forms import ThirdPartyAuthForm
from api.models import ApiClient
from core.models import SithFile
from core.schemas import UserProfileSchema
from core.utils import hmac_hexdigest


class ThirdPartyAuthParamsSchema(Schema):
    client_id: int
    third_party_app: str
    cgu_link: HttpUrl
    username: str
    callback_url: HttpUrl
    signature: str


class ThirdPartyAuthView(LoginRequiredMixin, FormView):
    form_class = ThirdPartyAuthForm
    template_name = "api/third_party/auth.jinja"
    success_url = reverse_lazy("core:index")

    def parse_params(self) -> ThirdPartyAuthParamsSchema:
        """Parse and check the authentication parameters.

        Raises:
            PermissionDenied: if the verification failed.
        """
        # This is here rather than in ThirdPartyAuthForm because
        # the given parameters and their signature are checked during both
        # POST (for obvious reasons) and GET (in order not to make
        # the user fill a form just to get an error he won't understand)
        params = self.request.GET or self.request.POST
        params = {key: unquote(val) for key, val in params.items()}
        try:
            params = ThirdPartyAuthParamsSchema(**params)
        except pydantic.ValidationError as e:
            raise PermissionDenied("Wrong data format") from e
        client: ApiClient = get_object_or_none(ApiClient, id=params.client_id)
        if not client:
            raise PermissionDenied
        if not hmac.compare_digest(
            hmac_hexdigest(client.hmac_key, params.model_dump(exclude={"signature"})),
            params.signature,
        ):
            raise PermissionDenied("Bad signature")
        return params

    def dispatch(self, request, *args, **kwargs):
        self.params = self.parse_params()
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        messages.warning(
            self.request,
            _(
                "You are going to link your AE account and your %(app)s account. "
                "Continue only if this page was opened from %(app)s."
            )
            % {"app": self.params.third_party_app},
        )
        return super().get(*args, **kwargs)

    def get_initial(self):
        return self.params.model_dump()

    def form_valid(self, form):
        client = ApiClient.objects.get(id=form.cleaned_data["client_id"])
        user = UserProfileSchema.from_orm(self.request.user).model_dump()
        data = {"user": user, "signature": hmac_hexdigest(client.hmac_key, user)}
        response = requests.post(form.cleaned_data["callback_url"], data=data)
        self.success_url = reverse(
            "api-link:third-party-auth-result",
            kwargs={"result": "success" if response.ok else "failure"},
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "third_party_app": self.params.third_party_app,
            "third_party_cgu": self.params.cgu_link,
            "sith_cgu": SithFile.objects.get(id=settings.SITH_CGU_FILE_ID),
        }


class ThirdPartyAuthResultView(LoginRequiredMixin, TemplateView):
    """View that the user will see if its authentication on sith was successful.

    This can show either a success or a failure message :
    - success : everything is good, the user is successfully authenticated
      and can close the page
    - failure : the authentication has been processed on the sith side,
      but the request to the callback url received an error.
      In such a case, there is nothing much we can do but to advice
      the user to contact the developers of the third-party app.
    """

    template_name = "core/base.jinja"
    success_message = _(
        "You have been successfully authenticated. You can now close this page."
    )
    error_message = _(
        "Your authentication on the AE website was successful, "
        "but an error happened during the interaction "
        "with the third-party application. "
        "Please contact the managers of the latter."
    )

    def get(self, request, *args, **kwargs):
        if self.kwargs.get("result") == "success":
            messages.success(request, self.success_message)
        else:
            messages.error(request, self.error_message)
        return super().get(request, *args, **kwargs)
