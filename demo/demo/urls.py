from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rosetta/', include('rosetta.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^dbmail/', include('dbmail.urls')),

    url('^browser_notification/$', "demo.views.browser_notification"),
    url(r'^ckeditor/', include('ckeditor.urls')),
) + staticfiles_urlpatterns()

'''
from django import VERSION

if VERSION < (1, 7):
    urlpatterns += patterns(
        '', url(r'^tinymce/', include('tinymce.urls')),
    )
'''
