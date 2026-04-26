from ninja_extra import ControllerBase, api_controller, route

from api.auth import ApiKeyAuth
from api.schemas import ApiClientSchema


@api_controller("/client")
class ApiClientController(ControllerBase):
    @route.get(
        "/me",
        auth=[ApiKeyAuth()],
        response=ApiClientSchema,
        url_name="api-client-infos",
    )
    def get_client_info(self):
        return self.context.request.auth
