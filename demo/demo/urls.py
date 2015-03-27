from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django import VERSION

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rosetta/', include('rosetta.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^dbmail/', include('dbmail.urls')),

    url('^browser_notification/$', "demo.views.browser_notification"),
) + staticfiles_urlpatterns()

if VERSION < (1, 7):
    urlpatterns += patterns(
        '', url(r'^tinymce/', include('tinymce.urls')),
    )
