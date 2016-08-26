from django.conf.urls import url, include

from counter.views import *

urlpatterns = [
    url(r'^(?P<counter_id>[0-9]+)$', CounterMain.as_view(), name='details'),
    url(r'^(?P<counter_id>[0-9]+)/click/(?P<user_id>[0-9]+)$', CounterClick.as_view(), name='click'),
    url(r'^(?P<counter_id>[0-9]+)/cash_summary$', CounterCashSummaryView.as_view(), name='cash_summary'),
    url(r'^(?P<counter_id>[0-9]+)/login$', CounterLogin.as_view(), name='login'),
    url(r'^(?P<counter_id>[0-9]+)/logout$', CounterLogout.as_view(), name='logout'),
    url(r'^admin/(?P<counter_id>[0-9]+)$', CounterEditView.as_view(), name='admin'),
    url(r'^admin/(?P<counter_id>[0-9]+)/prop$', CounterEditPropView.as_view(), name='prop_admin'),
    url(r'^admin$', CounterListView.as_view(), name='admin_list'),
    url(r'^admin/new$', CounterCreateView.as_view(), name='new'),
    url(r'^admin/delete/(?P<counter_id>[0-9]+)$', CounterDeleteView.as_view(), name='delete'),
    url(r'^admin/product/list$', ProductListView.as_view(), name='product_list'),
    url(r'^admin/product/create$', ProductCreateView.as_view(), name='new_product'),
    url(r'^admin/product/(?P<product_id>[0-9]+)$', ProductEditView.as_view(), name='product_edit'),
    url(r'^admin/producttype/list$', ProductTypeListView.as_view(), name='producttype_list'),
    url(r'^admin/producttype/create$', ProductTypeCreateView.as_view(), name='new_producttype'),
    url(r'^admin/producttype/(?P<type_id>[0-9]+)$', ProductTypeEditView.as_view(), name='producttype_edit'),
    url(r'^admin/selling/(?P<selling_id>[0-9]+)/delete$', SellingDeleteView.as_view(), name='selling_delete'),
    url(r'^admin/refilling/(?P<refilling_id>[0-9]+)/delete$', RefillingDeleteView.as_view(), name='refilling_delete'),
]


