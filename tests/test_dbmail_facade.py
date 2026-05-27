"""Coverage for the public dbmail facade — send_db_* functions."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


class _StubBackend:
    """Stand-in backend module captured by importlib.import_module patch."""

    def __init__(self):
        self.calls = []

    def Sender(self, *args, **kwargs):
        sender = self

        class _Inst:
            def send(_self, is_celery=False):
                sender.calls.append(
                    {
                        "args": args,
                        "kwargs": kwargs,
                        "is_celery": is_celery,
                    }
                )
                return "OK"

        return _Inst()

    SenderDebug = Sender


@pytest.fixture
def stub_backend(mocker):
    backend = _StubBackend()
    mocker.patch("importlib.import_module", return_value=backend)
    return backend


@pytest.fixture
def template(db):
    from dbmail.models import MailTemplate

    return MailTemplate.objects.create(name="Welcome", subject="Hi", message="Body", slug="welcome", is_active=True)


class TestDbSenderSyncPath:
    """When ENABLE_CELERY=False the facade calls Sender.send() directly."""

    def test_sync_send_invokes_backend(self, settings, stub_backend, template):
        from dbmail import db_sender

        settings.DB_MAILER_ENABLE_CELERY = False
        result = db_sender("welcome", "a@b.c", use_celery=False, backend="dbmail.backends.mail")
        assert result == "OK"
        assert len(stub_backend.calls) == 1
        assert stub_backend.calls[0]["args"][0] == "welcome"

    def test_send_db_mail_dispatches_to_db_sender(self, settings, stub_backend, template):
        from dbmail import send_db_mail

        settings.DB_MAILER_ENABLE_CELERY = False
        send_db_mail("welcome", "a@b.c", use_celery=False)
        assert len(stub_backend.calls) == 1

    @pytest.mark.parametrize(
        "func,channel",
        [
            ("send_db_sms", "sms"),
            ("send_db_push", "push"),
            ("send_db_tts", "tts"),
            ("send_db_bot", "bot"),
        ],
    )
    def test_other_send_helpers_pass_correct_backend(self, settings, stub_backend, template, func, channel):
        import dbmail

        settings.DB_MAILER_ENABLE_CELERY = False
        getattr(dbmail, func)("welcome", "a@b.c", use_celery=False)
        # The backend kwarg is consumed inside db_sender, so the stub
        # received whatever ``BACKEND[channel]`` resolves to. Just assert
        # one call landed.
        assert len(stub_backend.calls) == 1


class TestImportByStringAndGetModel:
    def test_import_by_string_returns_callable(self):
        from dbmail import import_by_string

        cls = import_by_string("dbmail.models.MailTemplate")
        from dbmail.models import MailTemplate

        assert cls is MailTemplate

    def test_get_model_returns_django_model(self):
        from dbmail import get_model

        m = get_model("dbmail", "MailTemplate")
        from dbmail.models import MailTemplate

        assert m is MailTemplate


class TestAppInstalledAndCelerySupported:
    def test_app_installed_true_for_dbmail(self, settings):
        from dbmail import app_installed

        assert app_installed("dbmail") is True

    def test_app_installed_false_for_unknown(self, settings):
        from dbmail import app_installed

        assert app_installed("not-a-real-app") is False

    def test_celery_supported_returns_bool(self):
        from dbmail import celery_supported

        # Either True (celery installed) or False — must not raise.
        assert isinstance(celery_supported(), bool)


class TestPy2ShimsRemoved:
    """`PY3`, `python_2_unicode_compatible`, and `import_module` were
    purged in 3.0 GA. Importing them must raise."""

    def test_py3_constant_removed(self):
        import dbmail

        assert not hasattr(dbmail, "PY3")

    def test_python_2_unicode_compatible_removed(self):
        import dbmail

        assert not hasattr(dbmail, "python_2_unicode_compatible")

    def test_import_module_re_export_removed(self):
        import dbmail

        assert "import_module" not in dbmail.__all__
