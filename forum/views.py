from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils import timezone
from django.conf import settings
from django import forms
from django.db import models
from django.core.exceptions import PermissionDenied

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin, TabedViewMixin
from forum.models import Forum, ForumMessage, ForumTopic

class ForumMainView(CanViewMixin, ListView):
    queryset = Forum.objects.filter(parent=None)
    template_name = "forum/main.jinja"

class ForumCreateView(CanCreateMixin, CreateView):
    model = Forum
    fields = ['name', 'parent', 'is_category', 'edit_groups', 'view_groups']
    template_name = "core/create.jinja"

    def get_initial(self):
        init = super(ForumCreateView, self).get_initial()
        parent = Forum.objects.filter(id=self.request.GET['parent']).first()
        init['parent'] = parent
        return init

class ForumEditView(CanEditPropMixin, UpdateView):
    model = Forum
    pk_url_kwarg = "forum_id"
    fields = ['name', 'parent', 'is_category', 'edit_groups', 'view_groups']
    template_name = "core/edit.jinja"
    success_url = reverse_lazy('forum:main')

class ForumDetailView(CanViewMixin, DetailView):
    model = Forum
    template_name = "forum/forum.jinja"
    pk_url_kwarg = "forum_id"

    def get_context_data(self, **kwargs):
        kwargs = super(ForumDetailView, self).get_context_data(**kwargs)
        kwargs['topics'] = self.object.topics.annotate(models.Max('messages__date')).order_by('-messages__date__max')
        return kwargs

class ForumTopicCreateView(CanCreateMixin, CreateView):
    model = ForumMessage
    fields = ['title', 'message']
    template_name = "core/create.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.forum = get_object_or_404(Forum, id=self.kwargs['forum_id'], is_category=False)
        if not request.user.can_view(self.forum):
            raise PermissionDenied
        return super(ForumTopicCreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        topic = ForumTopic(title=form.instance.title, author=self.request.user, forum=self.forum)
        topic.save()
        form.instance.topic = topic
        form.instance.author = self.request.user
        return super(ForumTopicCreateView, self).form_valid(form)

class ForumTopicEditView(CanEditPropMixin, UpdateView):
    model = ForumTopic
    fields = ['title', 'forum']
    pk_url_kwarg = "topic_id"
    template_name = "core/edit.jinja"

class ForumTopicDetailView(CanViewMixin, DetailView):
    model = ForumTopic
    pk_url_kwarg = "topic_id"
    template_name = "forum/topic.jinja"
    context_object_name = "topic"

class ForumMessageEditView(CanEditMixin, UpdateView):
    model = ForumMessage
    fields = ['title', 'message']
    template_name = "core/edit.jinja"
    pk_url_kwarg = "message_id"

class ForumMessageCreateView(CanCreateMixin, CreateView):
    model = ForumMessage
    fields = ['title', 'message']
    template_name = "core/create.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.topic = get_object_or_404(ForumTopic, id=self.kwargs['topic_id'])
        if not request.user.can_view(self.topic):
            raise PermissionDenied
        return super(ForumMessageCreateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        init = super(ForumMessageCreateView, self).get_initial()
        try:
            init['message'] = "\n".join([
                " > " + line for line in ForumMessage.objects.filter(id=self.request.GET['quote_id']).first().message.split('\n')
                ])
        except: pass
        return init

    def form_valid(self, form):
        form.instance.topic = self.topic
        form.instance.author = self.request.user
        return super(ForumMessageCreateView, self).form_valid(form)

