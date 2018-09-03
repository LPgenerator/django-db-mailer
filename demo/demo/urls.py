import os
import sys
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings

import demo.views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # url(r'^rosetta/', include('rosetta.urls')),
    url(r'^dbmail/', include('dbmail.urls')),
] + staticfiles_urlpatterns()

if 'test' not in sys.argv:
    urlpatterns += [
        url(r'^grappelli/', include('grappelli.urls')),
        url('^browser_notification/$', demo.views.browser_notification),
        url('^web-push/$', demo.views.web_push_notification),
        url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    ]

'''
from django import VERSION

if VERSION < (1, 7):
    urlpatterns += patterns(
        '', url(r'^tinymce/', include('tinymce.urls')),
    )
'''

# For security reason
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static

    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        '/', document_root=os.path.join(settings.PROJECT_ROOT, 'static', 'js'))

