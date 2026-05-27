from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from dbmail import celery_supported, db_sender, defaults, signals
from dbmail.models import ApiKey, MailLogTrack
from dbmail.utils import get_ip

logger = logging.getLogger(__name__)

# Backwards-compatible alias; delegates to utils.get_ip which also
# handles the REMOTE_ADDR fallback.
_client_ip = get_ip


def _audit(
    request: HttpRequest,
    api_key_obj: ApiKey | None,
    action: str,
    success: bool,
    detail: str | None = None,
) -> None:
    """Persist a row in :class:`ApiKeyUsageAudit` for the current request.

    Best-effort: a failure here MUST NOT break the API response. The
    operational signal (audit gap) is logged via ``logger.exception``
    so alerting can pick it up.
    """
    from dbmail.models import ApiKeyUsageAudit

    try:
        ua = request.headers.get("User-Agent") or ""
        ApiKeyUsageAudit.objects.create(
            api_key=api_key_obj,
            api_key_name=api_key_obj.name if api_key_obj else None,
            ip=_client_ip(request),
            ua=ua[:512],
            action=action,
            success=success,
            detail=detail,
        )
    except Exception:  # pragma: no cover - exercised only on storage failure
        logger.exception("Failed to write API audit log")


_BASE_ALLOWED_API_FIELDS: tuple[str, ...] = (
    "api_key",
    "slug",
    "recipient",
    "from_email",
    "cc",
    "bcc",
    "queue",
    "retry_delay",
    "max_retries",
    "retry",
    "language",
    "time_limit",
    "send_after",
    "backend",
)


def _allowed_api_fields() -> tuple[str, ...]:
    """Return the field whitelist for the public ``send_by_dbmail`` API.

    ``provider`` is excluded by default — accepting attacker-controlled
    dotted-path module names from the wire is a CWE-470 / CWE-94 vector
    that escalates a stolen API key into post-auth RCE through
    ``import_module(provider)`` inside the backend Sender. Operators
    that genuinely need provider routing per request can opt in with
    ``DB_MAILER_API_ALLOW_PROVIDER_OVERRIDE = True`` and constrain the
    accepted values via ``DB_MAILER_API_PROVIDER_ALLOWLIST``.
    See ADR-0006 and SECURITY.md.
    """
    if getattr(settings, "DB_MAILER_API_ALLOW_PROVIDER_OVERRIDE", False):
        return (*_BASE_ALLOWED_API_FIELDS, "provider")
    return _BASE_ALLOWED_API_FIELDS


# Public alias kept for backwards compatibility with anyone who imported
# ``ALLOWED_API_FIELDS`` directly. New code should call
# ``_allowed_api_fields()`` so the operator-controlled toggle is
# evaluated at request time.
ALLOWED_API_FIELDS = _BASE_ALLOWED_API_FIELDS


def _ratelimit_exceeded(api_key: str) -> bool:
    """Cache-based per-key rate limit (ADR-0006).

    Configurable via ``settings.DB_MAILER_API_RATE_LIMIT = (count, seconds)``.
    Default ``(60, 60)``. ``count == 0`` disables.
    """
    count, window = getattr(settings, "DB_MAILER_API_RATE_LIMIT", (60, 60))
    if count <= 0:
        return False

    key = "dbmail:rate:" + hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    # ``cache.add`` is atomic: returns False if the key already exists,
    # so concurrent first-callers do not double-initialise to 1 and bypass
    # one count.
    if cache.add(key, 0, timeout=window):
        # Counter freshly initialised; current call is the first of the window.
        cache.incr(key)
        return False
    try:
        current = cache.incr(key)
    except ValueError:
        # Race: another worker just expired and re-added the key.
        cache.add(key, 1, timeout=window)
        return False
    return current > count


def _hmac_check(request: HttpRequest) -> bool:
    """Optional HMAC-SHA-256 body signature (ADR-0006).

    Disabled when ``settings.DB_MAILER_API_HMAC_SECRET`` is empty.
    """
    secret = getattr(settings, "DB_MAILER_API_HMAC_SECRET", "")
    if not secret:
        return True
    received = request.META.get("HTTP_X_DBMAIL_SIGNATURE", "")
    if not received.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), request.body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received[len("sha256=") :], expected)


@csrf_exempt
def send_by_dbmail(request: HttpRequest) -> HttpResponse:
    """Public POST endpoint that triggers a dbmail send by template slug.

    Security model (ADR-0006):

    - Plain-text ``api_key`` is accepted only for legacy rows; new rows
      authenticate via ``password_hash`` (Django hashers).
      ``ApiKey.is_valid_key()`` rehashes legacy rows on first successful
      auth.
    - Cache-based rate limit, configurable via
      ``DB_MAILER_API_RATE_LIMIT``.
    - Optional HMAC body signature, enabled by setting
      ``DB_MAILER_API_HMAC_SECRET``.
    """
    if request.method != "POST":
        raise Http404

    # Force-read the raw body now so any subsequent ``request.POST``
    # access does not consume the stream and ``_hmac_check`` can still
    # see the bytes. Reading ``request.body`` is idempotent — Django
    # caches the result.
    _ = request.body

    if getattr(settings, "DB_MAILER_API_DISABLE", False):
        # Operator-side kill switch (e.g. while patching providers).
        _audit(request, None, "kill_switch", success=False, detail="DB_MAILER_API_DISABLE")
        return HttpResponseForbidden()

    allowed_fields = _allowed_api_fields()
    kwargs: dict[str, Any] = {f: request.POST.get(f) for f in allowed_fields if request.POST.get(f)}

    backend = defaults.BACKEND.get(kwargs.pop("backend", "mail"))
    api_key = kwargs.pop("api_key", None)
    if not api_key:
        _audit(request, None, "missing_api_key", success=False)
        raise Http404

    # If the operator opted in to provider override, enforce the
    # allowlist before the value reaches Sender._provider where it is
    # passed to importlib.import_module (CWE-94).
    if "provider" in kwargs:
        allowlist = tuple(getattr(settings, "DB_MAILER_API_PROVIDER_ALLOWLIST", ()))
        if not allowlist or kwargs["provider"] not in allowlist:
            logger.warning(
                "dbmail API rejected provider override %r (not in DB_MAILER_API_PROVIDER_ALLOWLIST)",
                kwargs["provider"],
            )
            _audit(
                request,
                None,
                "provider_blocked",
                success=False,
                detail=str(kwargs.get("provider"))[:255],
            )
            return HttpResponseForbidden()

    if _ratelimit_exceeded(api_key):
        logger.warning("dbmail API rate limit exceeded for key prefix %r", api_key[:4])
        _audit(request, None, "rate_limit", success=False, detail=api_key[:4])
        return HttpResponse(status=429)

    if not _hmac_check(request):
        logger.warning("dbmail API HMAC signature invalid for key prefix %r", api_key[:4])
        _audit(request, None, "hmac_invalid", success=False, detail=api_key[:4])
        return HttpResponseForbidden()

    cache_key = "dbmail:apikey:" + hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    if cache.get(cache_key) is None:
        try:
            api_obj = ApiKey.objects.get(api_key=api_key, is_active=True)
        except ApiKey.DoesNotExist:
            _audit(request, None, "invalid_key", success=False, detail=api_key[:4])
            raise Http404 from None
        if not api_obj.is_valid_key(api_key):
            _audit(request, api_obj, "invalid_key", success=False)
            raise Http404
        api_obj.mark_used(get_ip(request))
        cache.set(cache_key, 1, timeout=defaults.CACHE_TTL)
    else:
        # Cache hit — re-fetch FK for the audit row. Best-effort; the
        # audit table is informational, not load-bearing.
        api_obj = ApiKey.objects.filter(api_key=api_key, is_active=True).first()

    args: list[Any] = []
    if request.POST.get("data"):
        args = [json.loads(request.POST["data"])]

    if not (kwargs.get("slug") and kwargs.get("recipient")):
        _audit(request, api_obj, "bad_request", success=False, detail="missing slug/recipient")
        raise Http404

    if backend is not None:
        kwargs["backend"] = backend

    slug = kwargs.pop("slug")
    db_sender(slug, kwargs.pop("recipient"), *args, **kwargs)
    _audit(request, api_obj, "send", success=True, detail=slug)
    return HttpResponse("OK")


def mail_read_tracker(request: HttpRequest, encrypted: str) -> HttpResponse:
    if defaults.TRACK_ENABLE and defaults.ENABLE_LOGGING:
        req = {k: v for k, v in request.META.items() if k.startswith("HTTP_") or k.startswith("REMOTE")}
        if celery_supported() and defaults.ENABLE_CELERY:
            from dbmail.tasks import mail_track

            mail_track.apply_async(
                args=[req, encrypted],
                queue=defaults.TRACKING_QUEUE,
                retry=1,
                retry_policy={"max_retries": 3},
            )
        else:
            MailLogTrack.track(req, encrypted)

    return HttpResponse(
        content=defaults.TRACK_PIXEL[1],
        content_type=defaults.TRACK_PIXEL[0],
    )


class PostCSRFMixin(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)


def _safe_safari_push_path(site_pid: str) -> str | None:
    """Resolve and validate path to a Safari pushPackage zip.

    Defends against path traversal: ``site_pid`` from the URL must end up
    pointing inside ``defaults.SAFARI_PUSH_PATH``.
    Returns the absolute path or ``None`` if the resolved location escapes
    the configured directory.
    """
    base = os.path.realpath(defaults.SAFARI_PUSH_PATH)
    candidate = os.path.realpath(os.path.join(base, f"{site_pid}.zip"))
    if not candidate.startswith(base + os.sep):
        return None
    return candidate


class SafariPushPackagesView(PostCSRFMixin):
    def post(
        self,
        _: HttpRequest,
        version: str,
        site_pid: str,
    ) -> HttpResponse:
        signals.safari_push_package.send(
            self.__class__,
            instance=self,
            version=version,
            site_pid=site_pid,
        )

        path = _safe_safari_push_path(site_pid)
        if path is None or not os.path.isfile(path):
            logger.warning("Safari pushPackage rejected: %r", site_pid)
            return HttpResponseNotFound()

        with open(path, "rb") as fh:
            data = fh.read()
        return HttpResponse(data, content_type="application/zip")


class SafariSubscriptionView(PostCSRFMixin):
    http_method_names = ["post", "delete"]

    def post(self, _: HttpRequest, **kwargs: Any) -> HttpResponse:
        signals.safari_subscribe.send(self.__class__, instance=self, **kwargs)
        return HttpResponse()

    def delete(self, _: HttpRequest, **kwargs: Any) -> HttpResponse:
        signals.safari_unsubscribe.send(self.__class__, instance=self, **kwargs)
        return HttpResponse()


class SafariLogView(PostCSRFMixin):
    def post(self, request: HttpRequest, version: str) -> HttpResponse:
        err = json.loads(request.body)
        signals.safari_error_log.send(self.__class__, instance=self, err=err)
        return HttpResponse()


class PushSubscriptionView(View):
    http_method_names = ["post", "delete"]

    def _process(
        self,
        request: HttpRequest,
        signal: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        try:
            kwargs.update(json.loads(request.body))
            signal.send(self.__class__, instance=self, **kwargs)
            return HttpResponse()
        except ValueError:
            return HttpResponseBadRequest()

    def post(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        return self._process(request, signals.push_subscribe, **kwargs)

    def delete(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        return self._process(request, signals.push_unsubscribe, **kwargs)
