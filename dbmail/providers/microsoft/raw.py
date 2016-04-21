from dbmail.providers.microsoft.base import MPNSBase


class MPNSRaw(MPNSBase):
    NOTIFICATION_CLS = 3
    TARGET = 'raw'

    def payload(self, payload):
        return payload


def send(uri, *_, **kwargs):
    return MPNSRaw().send(uri, kwargs)
