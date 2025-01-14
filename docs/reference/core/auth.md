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
            - CanCreateMixin
            - CanEditMixin
            - CanViewMixin
            - FormerSubscriberMixin
            - PermissionOrAuthorRequiredMixin


## API Permissions

::: core.auth.api_permissions
    handler: python
    options:
        heading_level: 3