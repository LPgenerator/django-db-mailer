import os
import sys
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings

import demo.views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # url(r'^rosetta/', include('rosetta.urls')),
    url(r'^dbmail/', include('dbmail.urls')),
]

if 'test' not in sys.argv:
    urlpatterns += [
        url(r'^grappelli/', include('grappelli.urls')),
        url('^browser_notification/$', demo.views.browser_notification),
        url('^web-push/$', demo.views.web_push_notification),
        url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    ]


# For security reason
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

