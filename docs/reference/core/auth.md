## Backend

::: core.auth.backends
    handler: python
    options:
        heading_level: 3
        members:
            - SithModelBackend

## Mixins

::: core.auth.mixins
    handler: python
    options:
        heading_level: 3
        members:
            - can_edit_prop
            - can_edit
            - can_view
            - CanEditMixin
            - CanViewMixin
            - CanEditPropMixin
            - FormerSubscriberMixin
            - PermissionOrAuthorRequiredMixin
