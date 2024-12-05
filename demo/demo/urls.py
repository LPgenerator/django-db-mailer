import sys
from django.urls import include, re_path
from django.contrib import admin
from django.conf import settings

import demo.views


urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    # re_path(r'^rosetta/', include('rosetta.urls')),
    re_path(r"^dbmail/", include("dbmail.urls")),
]

if "test" not in sys.argv:
    urlpatterns += [
        re_path(r"^grappelli/", include("grappelli.urls")),
        re_path("^browser_notification/$", demo.views.browser_notification),
        re_path("^web-push/$", demo.views.web_push_notification),
        re_path(r"^ckeditor/", include("ckeditor_uploader.urls")),
    ]


# For security reason
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
