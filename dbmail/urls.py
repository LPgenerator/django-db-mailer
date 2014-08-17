# -*- encoding: utf-8 -*-

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'dbmail.views',
    url(r'^api/', 'send_by_dbmail', name='db-mail-api'),
)
