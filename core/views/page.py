# This file contains all the views that concern the page model
from django.shortcuts import render, redirect, get_object_or_404

from core.models import Page
from core.views.forms import PageEditForm, PagePropForm

def page(request, page_name=None):
    """
    This view displays a page or the link to create it if 404
    """
    context = {'title': 'View a Page'}
    if page_name == None:
        context['page_list'] = Page.objects.all
        return render(request, "core/page.html", context)
    context['page'] = Page.get_page_by_full_name(page_name)
    if context['page'] is not None:
        context['view_page'] = True
        context['title'] = context['page'].title
        context['tests'] = "PAGE_FOUND : "+context['page'].title
    else:
        context['title'] = "This page does not exist"
        context['new_page'] = page_name
        context['tests'] = "PAGE_NOT_FOUND"
    return render(request, "core/page.html", context)

def page_edit(request, page_name=None):
    """
    page_edit view, able to create a page, save modifications, and display the page ModelForm
    """
    context = {'title': 'Edit a page',
               'page_name': page_name}
    p = Page.get_page_by_full_name(page_name)
    # New page
    if p == None:
        parent_name = '/'.join(page_name.split('/')[:-1])
        name = page_name.split('/')[-1]
        if parent_name == "":
            p = Page(name=name)
        else:
            parent = Page.get_page_by_full_name(parent_name)
            p = Page(name=name, parent=parent)
    # Saving page
    if request.method == 'POST':
        f = PageEditForm(request.POST, instance=p)
        if f.is_valid():
            f.save()
            context['tests'] = "PAGE_SAVED"
        else:
            context['tests'] = "PAGE_NOT_SAVED"
    # Default: display the edit form without change
    else:
        context['tests'] = "POST_NOT_RECEIVED"
        f = PageEditForm(instance=p)
    context['page'] = p
    context['page_edit'] = f.as_p()
    return render(request, 'core/page.html', context)

def page_prop(request, page_name=None):
    """
    page_prop view, able to change a page's properties
    """
    context = {'title': 'Page properties',
               'page_name': page_name}
    p = Page.get_page_by_full_name(page_name)
    # New page
    if p == None:
        parent_name = '/'.join(page_name.split('/')[:-1])
        name = page_name.split('/')[-1]
        if parent_name == "":
            p = Page(name=name)
        else:
            parent = Page.get_page_by_full_name(parent_name)
            p = Page(name=name, parent=parent)
    # Saving page
    if request.method == 'POST':
        f = PagePropForm(request.POST, instance=p)
        if f.is_valid():
            f.save()
            context['tests'] = "PAGE_SAVED"
        else:
            context['tests'] = "PAGE_NOT_SAVED"
    # Default: display the edit form without change
    else:
        context['tests'] = "POST_NOT_RECEIVED"
        f = PagePropForm(instance=p)
    context['page'] = p
    context['page_prop'] = f.as_p()
    return render(request, 'core/page.html', context)
