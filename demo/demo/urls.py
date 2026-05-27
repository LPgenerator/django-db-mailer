from __future__ import annotations

import sys

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

import demo.views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dbmail/", include("dbmail.urls")),
]

if "test" not in sys.argv:
    extras = []

    try:
        import grappelli  # noqa: F401

        extras.append(path("grappelli/", include("grappelli.urls")))
    except ImportError:
        pass

    try:
        import ckeditor_uploader  # noqa: F401

        extras.append(path("ckeditor/", include("ckeditor_uploader.urls")))
    except ImportError:
        pass

    try:
        import rosetta  # noqa: F401

        extras.append(path("rosetta/", include("rosetta.urls")))
    except ImportError:
        pass

    extras += [
        re_path(r"^browser_notification/$", demo.views.browser_notification),
        re_path(r"^web-push/$", demo.views.web_push_notification),
    ]
    urlpatterns += extras


if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    try:
        import debug_toolbar  # noqa: F401

        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    except ImportError:
        pass
