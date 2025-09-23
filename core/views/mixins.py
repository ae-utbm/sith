import copy
import inspect
from typing import Any, ClassVar, LiteralString, Protocol, Unpack

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.utils.safestring import SafeString
from django.views import View
from django.views.generic.base import ContextMixin, TemplateResponseMixin


class TabedViewMixin(View):
    """Basic functions for displaying tabs in the template."""

    current_tab: ClassVar[str | None] = None
    list_of_tabs: ClassVar[list | None] = None
    tabs_title: ClassVar[str | None] = None

    def get_tabs_title(self):
        if not self.tabs_title:
            raise ImproperlyConfigured("tabs_title is required")
        return self.tabs_title

    def get_current_tab(self):
        if not self.current_tab:
            raise ImproperlyConfigured("current_tab is required")
        return self.current_tab

    def get_list_of_tabs(self):
        if not self.list_of_tabs:
            raise ImproperlyConfigured("list_of_tabs is required")
        return self.list_of_tabs

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["tabs_title"] = self.get_tabs_title()
        kwargs["current_tab"] = self.get_current_tab()
        kwargs["list_of_tabs"] = self.get_list_of_tabs()
        return kwargs


class AllowFragment:
    """Add `is_fragment` to templates. It's only True if the request is emitted by htmx"""

    def get_context_data(self, **kwargs):
        kwargs["is_fragment"] = self.request.headers.get("HX-Request", False)
        return super().get_context_data(**kwargs)


class FragmentRenderer(Protocol):
    def __call__(
        self, request: HttpRequest, **kwargs: Unpack[dict[str, Any]]
    ) -> SafeString: ...


class FragmentMixin(TemplateResponseMixin, ContextMixin):
    """Make a view buildable as a fragment that can be embedded in a template.

    Most fragments are used in two different ways :
    - in the request/response cycle, like any regular view
    - in templates, where the rendering is done in another view

    This mixin aims to simplify the initial fragment rendering.
    The rendered fragment will then be able to re-render itself
    through the request/response cycle if it uses HTMX.

    !!!Example
        ```python
        class MyFragment(FragmentMixin, FormView):
            template_name = "app/fragment.jinja"
            form_class = MyForm
            success_url = reverse_lazy("foo:bar")

        # in another view :
        def some_view(request):
            fragment = MyFragment.as_fragment()
            return render(
                request,
                "app/template.jinja",
                context={"fragment": fragment(request)
            }

        # in urls.py
        urlpatterns = [
            path("foo/view", some_view),
            path("foo/fragment", MyFragment.as_view()),
        ]
        ```
    """

    reload_on_redirect: bool = False
    """If True, this fragment will trigger a full page reload on redirect."""

    @classmethod
    def as_fragment(cls, **initkwargs) -> FragmentRenderer:
        # the following code is heavily inspired from the base View.as_view method
        for key in initkwargs:
            if not hasattr(cls, key):
                raise TypeError(
                    "%s() received an invalid keyword %r. as_view "
                    "only accepts arguments that are already "
                    "attributes of the class." % (cls.__name__, key)
                )

        def fragment(request: HttpRequest, **kwargs) -> SafeString:
            self = cls(**initkwargs)
            # any POST action on the fragment will be dealt by the fragment itself.
            # So, if the view that is rendering this fragment is in a POST context,
            # let's pretend anyway it's a GET, in order to be sure the fragment
            # won't try to do any POST action (like form validation) on initial render.
            self.request = copy.copy(request)
            self.request.method = "GET"
            self.kwargs = kwargs
            return self.render_fragment(request, **kwargs)

        fragment.__doc__ = cls.__doc__
        fragment.__module__ = cls.__module__
        return fragment

    def render_fragment(self, request, **kwargs) -> SafeString:
        return render_to_string(
            self.get_template_names(),
            context=self.get_context_data(**kwargs),
            request=request,
        )

    def dispatch(self, *args, **kwargs):
        res: HttpResponse = super().dispatch(*args, **kwargs)
        if 300 <= res.status_code < 400 and self.reload_on_redirect:
            # HTMX doesn't care about redirection codes (because why not),
            # so we must transform the redirection code into a 200.
            res.status_code = 200
            res.headers["HX-Redirect"] = res["Location"]
        return res


class UseFragmentsMixin(ContextMixin):
    """Mark a view as using fragments.

    This mixin is not mandatory
    (you may as well render manually your fragments in the `get_context_data` method).
    However, the interface of this class bring some distinction
    between fragments and other context data, which may
    reduce boilerplate.

    !!!Example
        ```python
        class FooFragment(FragmentMixin, FormView): ...

        class BarFragment(FragmentMixin, FormView): ...

        class AdminFragment(FragmentMixin, FormView): ...

        class MyView(UseFragmentsMixin, TemplateView)
            template_name = "app/view.jinja"
            fragments = {
                "foo": FooFragment
                "bar": BarFragment(template_name="some_template.jinja")
            }
            fragments_data = {
                "foo": {"some": "data"}  # this will be passed to the FooFragment renderer
            }

            def get_fragments(self):
                res = super().get_fragments()
                if self.request.user.is_superuser:
                    res["admin_fragment"] = AdminFragment
                return res
        ```
    """

    fragments: dict[LiteralString, type[FragmentMixin] | FragmentRenderer] | None = None
    fragment_data: dict[LiteralString, dict[LiteralString, Any]] | None = None

    def get_fragments(self) -> dict[str, type[FragmentMixin] | FragmentRenderer]:
        return self.fragments if self.fragments is not None else {}

    def get_fragment_data(self) -> dict[str, dict[str, Any]]:
        """Return eventual data used to initialize the fragments."""
        return self.fragment_data if self.fragment_data is not None else {}

    def get_fragment_context_data(self) -> dict[str, SafeString]:
        """Return the rendered fragments as context data."""
        res = {}
        data = self.get_fragment_data()
        for name, fragment in self.get_fragments().items():
            is_cls = inspect.isclass(fragment) and issubclass(fragment, FragmentMixin)
            _fragment = fragment.as_fragment() if is_cls else fragment
            fragment_data = data.get(name, {})
            res[name] = _fragment(self.request, **fragment_data)
        return res

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs.update(self.get_fragment_context_data())
        return kwargs
