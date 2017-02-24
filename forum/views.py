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

class ForumMainView(ListView):
    queryset = Forum.objects.filter(parent=None)
    template_name = "forum/main.jinja"

class ForumMarkAllAsRead(RedirectView):
    permanent = False
    url = reverse_lazy('forum:last_unread')

    def get(self, request, *args, **kwargs):
        try:
            fi = request.user.forum_infos
            fi.last_read_date = timezone.now()
            fi.save()
        except: pass
        return super(ForumMarkAllAsRead, self).get(request, *args, **kwargs)

class ForumLastUnread(ListView):
    model = ForumTopic
    template_name = "forum/last_unread.jinja"

    def get_queryset(self):
        l = ForumMessage.objects.exclude(readers=self.request.user).filter(
                date__gt=self.request.user.forum_infos.last_read_date).values_list('topic') # TODO try to do better
        return self.model.objects.filter(id__in=l).annotate(models.Max('messages__date')).order_by('-messages__date__max')
        # return self.model.objects.exclude(messages__readers=self.request.user).distinct().annotate(
                # models.Max('messages__date')).order_by('-messages__date__max')

class ForumCreateView(CanCreateMixin, CreateView):
    model = Forum
    fields = ['name', 'parent', 'owner_club', 'is_category', 'edit_groups', 'view_groups']
    template_name = "core/create.jinja"

    def get_initial(self):
        init = super(ForumCreateView, self).get_initial()
        try:
            parent = Forum.objects.filter(id=self.request.GET['parent']).first()
            init['parent'] = parent
            init['owner_club'] = parent.owner_club
        except: pass
        return init

class ForumEditForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['name', 'parent', 'owner_club', 'is_category', 'edit_groups', 'view_groups']
    recursive = forms.BooleanField(label=_("Apply rights and club owner recursively"), required=False)

class ForumEditView(CanEditPropMixin, UpdateView):
    model = Forum
    pk_url_kwarg = "forum_id"
    form_class = ForumEditForm
    template_name = "core/edit.jinja"
    success_url = reverse_lazy('forum:main')

    def form_valid(self, form):
        ret = super(ForumEditView, self).form_valid(form)
        if form.cleaned_data['recursive']:
            self.object.apply_rights_recursively()
        return ret

class ForumDeleteView(CanEditPropMixin, DeleteView):
    model = Forum
    pk_url_kwarg = "forum_id"
    template_name = "core/delete_confirm.jinja"
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

class ForumTopicEditView(CanEditMixin, UpdateView):
    model = ForumTopic
    fields = ['forum']
    pk_url_kwarg = "topic_id"
    template_name = "core/edit.jinja"

class ForumTopicDetailView(CanViewMixin, DetailView):
    model = ForumTopic
    pk_url_kwarg = "topic_id"
    template_name = "forum/topic.jinja"
    context_object_name = "topic"

    def get_context_data(self, **kwargs):
        kwargs = super(ForumTopicDetailView, self).get_context_data(**kwargs)
        msg = self.object.messages.exclude(readers=self.request.user).order_by('id').first()
        try:
            kwargs['first_unread_message_id'] = msg.id
        except:
            kwargs['first_unread_message_id'] = -1
        return kwargs

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
                "> " + line for line in ForumMessage.objects.filter(id=self.request.GET['quote_id']).first().message.split('\n')
                ])
        except: pass
        return init

    def form_valid(self, form):
        form.instance.topic = self.topic
        form.instance.author = self.request.user
        return super(ForumMessageCreateView, self).form_valid(form)

