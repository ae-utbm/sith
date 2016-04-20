from django.conf.urls import url, include

from accounting.views import *

urlpatterns = [
    # Bank accounts
    url(r'^$', BankAccountListView.as_view(), name='bank_list'),
    url(r'^bank/create$', BankAccountCreateView.as_view(), name='bank_new'),
    url(r'^bank/(?P<b_account_id>[0-9]+)$', BankAccountDetailView.as_view(), name='bank_details'),
    url(r'^bank/(?P<b_account_id>[0-9]+)/edit$', BankAccountEditView.as_view(), name='bank_edit'),
    url(r'^bank/(?P<b_account_id>[0-9]+)/delete$', BankAccountDeleteView.as_view(), name='bank_delete'),
    # Club accounts
    url(r'^club/create$', ClubAccountCreateView.as_view(), name='club_new'),
    url(r'^club/(?P<c_account_id>[0-9]+)$', ClubAccountDetailView.as_view(), name='club_details'),
    url(r'^club/(?P<c_account_id>[0-9]+)/edit$', ClubAccountEditView.as_view(), name='club_edit'),
    url(r'^club/(?P<c_account_id>[0-9]+)/delete$', ClubAccountDeleteView.as_view(), name='club_delete'),
    # Journals
    url(r'^journal/create$', JournalCreateView.as_view(), name='journal_new'),
]


