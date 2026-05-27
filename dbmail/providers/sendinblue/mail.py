"""SendInBlue (Brevo) mail provider.

Note: Sendinblue rebranded to Brevo in 2023; the legacy ``mailin`` SDK
has not been maintained since ~2018. This provider keeps the legacy
SDK call shape for backwards compatibility and is scheduled for
replacement in a future release with ``getbrevo-brevo-python``.

Install via the ``[sendinblue]`` extra:
``pip install "django-db-mailer[sendinblue]"``.
"""

from __future__ import annotations

import base64
import email
import warnings


class SendInBlueError(Exception):
    pass


def email_list_to_email_dict(email_list):
    if email_list is None:
        return {}
    result = {}
    for value in email_list:
        realname, address = email.utils.parseaddr(value)
        result[address] = realname if realname and address else address
    return result


def email_address_to_list(email_address):
    realname, address = email.utils.parseaddr(email_address)
    return [address, realname] if realname and address else [email_address, email_address]


def send(sender_instance):
    """Send a transactional email using SendInBlue API.

    Site: https://www.sendinblue.com
    API: https://apidocs.sendinblue.com/
    """
    warnings.warn(
        "dbmail.providers.sendinblue uses the unmaintained 'mailin' SDK; "
        "Sendinblue rebranded to Brevo in 2023. The provider will be "
        "rewritten against 'getbrevo-brevo-python' in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    from mailin import Mailin

    m = Mailin("https://api.sendinblue.com/v2.0", sender_instance._kwargs.get("api_key"))
    data = {
        "to": email_list_to_email_dict(sender_instance._recipient_list),
        "cc": email_list_to_email_dict(sender_instance._cc),
        "bcc": email_list_to_email_dict(sender_instance._bcc),
        "from": email_address_to_list(sender_instance._from_email),
        "subject": sender_instance._subject,
    }
    if sender_instance._template.is_html:
        data.update({"html": sender_instance._message, "headers": {"Content-Type": "text/html; charset=utf-8"}})
    else:
        data.update({"text": sender_instance._message})
    if "attachments" in sender_instance._kwargs:
        data["attachment"] = {}
        for attachment in sender_instance._kwargs["attachments"]:
            data["attachment"][attachment[0]] = base64.b64encode(attachment[1]).decode("ascii")
    result = m.send_email(data)
    if result["code"] != "success":
        raise SendInBlueError(result["message"])
