from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils import timezone
from django.conf import settings
from django import forms
from django.db import models
from django.core.exceptions import PermissionDenied

from ajax_select import make_ajax_form, make_ajax_field

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, CanCreateMixin, TabedViewMixin
from forum.models import Forum, ForumMessage, ForumTopic, ForumMessageMeta

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
        return self.model.objects.filter(id__in=l).annotate(models.Max('messages__date')).order_by('-messages__date__max').select_related('author')

class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['name', 'parent', 'owner_club', 'is_category', 'edit_groups', 'view_groups']
    edit_groups = make_ajax_field(Forum, 'edit_groups', 'groups', help_text="")
    view_groups = make_ajax_field(Forum, 'view_groups', 'groups', help_text="")

class ForumCreateView(CanCreateMixin, CreateView):
    model = Forum
    form_class = ForumForm
    template_name = "core/create.jinja"

    def get_initial(self):
        init = super(ForumCreateView, self).get_initial()
        try:
            parent = Forum.objects.filter(id=self.request.GET['parent']).first()
            init['parent'] = parent
            init['owner_club'] = parent.owner_club
            init['edit_groups'] = parent.edit_groups.all()
            init['view_groups'] = parent.view_groups.all()
        except: pass
        return init

class ForumEditForm(ForumForm):
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

class TopicForm(forms.ModelForm):
    class Meta:
        model = ForumMessage
        fields = ['title', 'message']
    title = forms.CharField(required=True)

class ForumTopicCreateView(CanCreateMixin, CreateView):
    model = ForumMessage
    form_class = TopicForm
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
    queryset = ForumTopic.objects.select_related('forum__parent')

    def get_context_data(self, **kwargs):
        kwargs = super(ForumTopicDetailView, self).get_context_data(**kwargs)
        msg = self.object.messages.exclude(readers=self.request.user).filter(date__gte=self.request.user.forum_infos.last_read_date).order_by('id').first()
        try:
            kwargs['first_unread_message_id'] = msg.id
        except:
            kwargs['first_unread_message_id'] = float("inf")
        return kwargs

class ForumMessageEditView(CanEditMixin, UpdateView):
    model = ForumMessage
    fields = ['title', 'message']
    template_name = "core/edit.jinja"
    pk_url_kwarg = "message_id"

    def form_valid(self, form):
        ForumMessageMeta(message=self.object, user=self.request.user, action="EDIT").save()
        return super(ForumMessageEditView, self).form_valid(form)

class ForumMessageDeleteView(SingleObjectMixin, RedirectView):
    model = ForumMessage
    pk_url_kwarg = "message_id"
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        self.object = self.get_object()
        if self.object.can_be_moderated_by(self.request.user):
            ForumMessageMeta(message=self.object, user=self.request.user, action="DELETE").save()
        return self.object.get_absolute_url()

class ForumMessageUndeleteView(SingleObjectMixin, RedirectView):
    model = ForumMessage
    pk_url_kwarg = "message_id"
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        self.object = self.get_object()
        if self.object.can_be_moderated_by(self.request.user):
            ForumMessageMeta(message=self.object, user=self.request.user, action="UNDELETE").save()
        return self.object.get_absolute_url()

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
            message = ForumMessage.objects.select_related('author').filter(id=self.request.GET['quote_id']).first()
            init['message'] = "> ##### %s\n" % (_("%(author)s said") % {'author': message.author.get_short_name()})
            init['message'] += "\n".join([
                "> " + line for line in message.message.split('\n')
                ])
            init['message'] += "\n\n"
        except Exception as e:
            print(repr(e))
        return init

    def form_valid(self, form):
        form.instance.topic = self.topic
        form.instance.author = self.request.user
        return super(ForumMessageCreateView, self).form_valid(form)


