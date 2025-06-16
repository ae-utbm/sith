from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI(
    title="PICON",
    description="Portail Interaction de Communication avec les Services Étudiants",
    version="0.2.0",
    urls_namespace="api",
    csrf=True,
)
api.auto_discover_controllers()
