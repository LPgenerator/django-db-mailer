# -*- encoding: utf-8 -*-

from django.conf.urls import url

from dbmail.views import (
    send_by_dbmail, mail_read_tracker,
    SafariPushPackagesView, SafariSubscriptionView, SafariLogView,
    PushSubscriptionView
)

urlpatterns = [
    url(r'^api/', send_by_dbmail, name='db-mail-api'),
    url(r'^mail_read_tracker/(.*?)/$',
        mail_read_tracker, name='db-mail-tracker'),

    url(r'^safari/v(?P<version>[0-9]{1})/pushPackages/(?P<site_pid>[.\w-]+)/?',
        SafariPushPackagesView.as_view()),
    url(r'^safari/v(?P<version>[0-9]{1})/devices/'
        r'(?P<device_token>[.\w-]+)/registrations/(?P<site_pid>[.\w-]+)/?',
        SafariSubscriptionView.as_view()),
    url(r'^safari/v(?P<version>[0-9]{1})/log/?', SafariLogView.as_view()),

    url(r'^(?P<reg_type>web-push|mobile)/subscribe/',
        PushSubscriptionView.as_view(), name='push-subscribe'),
    url(r'^(?P<reg_type>web-push|mobile)/unsubscribe/',
        PushSubscriptionView.as_view(), name='push-unsubscribe'),
]
