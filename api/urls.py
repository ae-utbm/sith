from django.urls import path, register_converter
from ninja.security import SessionAuth
from ninja_extra import NinjaExtraAPI

from api.views import ThirdPartyAuthResultView, ThirdPartyAuthView
from core.converters import ResultConverter

api = NinjaExtraAPI(
    title="PICON",
    description="Portail Interactif de Communication avec les Outils Numériques",
    version="0.2.0",
    urls_namespace="api",
    auth=[SessionAuth()],
)
api.auto_discover_controllers()

register_converter(ResultConverter, "res")

urlpatterns = [
    path("auth/", ThirdPartyAuthView.as_view(), name="third-party-auth"),
    path(
        "auth/<res:result>/",
        ThirdPartyAuthResultView.as_view(),
        name="third-party-auth-result",
    ),
]
