from __future__ import annotations

import json

import requests
from django.conf import settings

from dbmail.providers._compat import from_unicode


class SMSBlissError(Exception):
    pass


def send(to, message, sms_from=None, **kwargs):
    sender = SMSBlissProvider(sms_from=sms_from)
    return sender.send_message(to, message, **kwargs)


class SMSBlissProvider:
    def __init__(self, **kwargs):
        # Read settings lazily so the provider module is importable
        # even when SMSBLISS_* are not configured (e.g. on CI smoke
        # imports without a project).
        self.login = settings.SMSBLISS_LOGIN
        self.password = settings.SMSBLISS_PASSWORD
        self.url = settings.SMSBLISS_API_URL
        self._from_msg = kwargs.pop("sms_from", settings.SMSBLISS_FROM)

    def send_message(self, sms_to, message, **kwargs):
        kwargs.update(
            {
                "messages": [{"clientId": 1, "phone": sms_to, "text": from_unicode(message), "sender": self._from_msg}],
                "showBillingDetails": True,
            }
        )
        return self._send_request(kwargs)

    def _send_request(self, data_to_send):
        data = self.add_credentials(data_to_send)
        response = requests.post(self.url, data=json.dumps(data), timeout=10)

        response_data = response.json()

        is_success = self.is_success_response(response, response_data)

        if not is_success:
            raise SMSBlissError(response_data)

        return response_data

    def add_credentials(self, data_to_send):
        data_to_send.update(
            {
                "login": self.login,
                "password": self.password,
            }
        )
        return data_to_send

    @staticmethod
    def is_success_response(response, response_data):
        if response.status_code != 200:
            return False

        response_messages = response_data.get("messages", [])

        for message in response_messages:
            if isinstance(message, dict):
                if message.get("status") not in ["accepted", "delivered"]:
                    return False
        return True
