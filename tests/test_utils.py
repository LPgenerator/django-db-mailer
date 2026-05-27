"""Coverage for dbmail.utils."""

from __future__ import annotations


class TestPremailerTransform:
    def test_returns_input_when_premailer_missing(self, mocker):
        # Simulate premailer-not-installed.
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "premailer":
                raise ImportError("simulated")
            return real_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=fake_import)
        from dbmail.utils import premailer_transform

        assert premailer_transform("<p>hi</p>") == "<p>hi</p>"

    def test_recovers_from_premailer_runtime_error(self, mocker):
        # premailer raises during transform; helper logs + returns original.
        import dbmail.utils as utils_mod

        class FakePremailer:
            def transform(self, *_a, **_kw):
                raise RuntimeError("boom")

        mocker.patch.dict("sys.modules", {"premailer": type("M", (), {"transform": FakePremailer().transform})})
        assert utils_mod.premailer_transform("<p>hi</p>") in ("<p>hi</p>",)


class TestGetIp:
    def test_falls_back_to_remote_addr_split(self, mocker):
        from django.test import RequestFactory

        from dbmail.utils import get_ip

        req = RequestFactory().get("/")
        req.META["REMOTE_ADDR"] = "1.2.3.4, 10.0.0.1"
        # Strip trailing comma form.
        ip = get_ip(req)
        assert ip in ("1.2.3.4", "10.0.0.1")


class TestHtml2textAndCleanHtml:
    def test_html2text_falls_back_to_strip_tags_when_module_missing(self, mocker):
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "html2text":
                raise ImportError
            return real_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=fake_import)
        from dbmail.utils import html2text

        result = html2text("<p>hello <b>world</b></p>")
        assert "hello" in result
        assert "<" not in result

    def test_clean_html_uses_configured_module(self, mocker):
        from dbmail import utils as utils_mod

        # Make import_module return a stub providing html2text().
        stub = type("M", (), {"html2text": staticmethod(lambda x: "STRIPPED")})
        mocker.patch.object(utils_mod, "import_module", return_value=stub)
        assert utils_mod.clean_html("<p>hi</p>") == "STRIPPED"
