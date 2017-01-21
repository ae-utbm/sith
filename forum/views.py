from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils import timezone
from django.conf import settings
from django import forms
from django.core.exceptions import PermissionDenied

from forum.models import Forum, ForumMessage, ForumTopic

class ForumMainView(ListView):
    queryset = Forum.objects.filter(parent=None)
    template_name = "forum/main.jinja"

class ForumCreateView(CreateView):
    model = Forum
    fields = ['name', 'parent', 'is_category', 'owner_group', 'edit_groups', 'view_groups']
    template_name = "core/create.jinja"

    def get_initial(self):
        init = super(ForumCreateView, self).get_initial()
        parent = Forum.objects.filter(id=self.request.GET['parent']).first()
        init['parent'] = parent
        return init

class ForumEditView(UpdateView):
    model = Forum
    pk_url_kwarg = "forum_id"
    fields = ['name', 'parent', 'is_category', 'owner_group', 'edit_groups', 'view_groups']
    template_name = "core/edit.jinja"
    success_url = reverse_lazy('forum:main')

class ForumDetailView(DetailView):
    model = Forum
    template_name = "forum/forum.jinja"
    pk_url_kwarg = "forum_id"

class ForumTopicCreateView(CreateView):
    model = ForumTopic
    fields = ['title']
    template_name = "core/create.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.forum = get_object_or_404(Forum, id=self.kwargs['forum_id'], is_category=False)
        if not request.user.can_view(self.forum):
            raise PermissionDenied
        return super(ForumTopicCreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.forum = self.forum
        form.instance.author = self.request.user
        return super(ForumTopicCreateView, self).form_valid(form)

class ForumTopicEditView(UpdateView):
    model = ForumTopic
    fields = ['title']
    pk_url_kwarg = "topic_id"
    template_name = "core/edit.jinja"

class ForumTopicDetailView(DetailView):
    model = ForumTopic
    pk_url_kwarg = "topic_id"
    template_name = "forum/topic.jinja"
    context_object_name = "topic"

class ForumMessageCreateView(CreateView):
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

