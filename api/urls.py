from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI(
    title="PICON",
    description="Portail Interactif de Communication avec les Outils Numériques",
    version="0.2.0",
    urls_namespace="api",
    csrf=True,
)
api.auto_discover_controllers()
