from io import BytesIO
from xml.etree import ElementTree

from django.conf import settings
from requests import post


class WPError(Exception):
    pass


class MPNSBase(object):
    NOTIFICATION_CLS = None
    TARGET = None

    def __init__(self):
        self.headers = {
            'Content-Type': 'text/xml',
            'Accept': 'application/*',
            'X-NotificationClass': self.NOTIFICATION_CLS,
            'X-WindowsPhone-Target': self.TARGET,
        }
        ElementTree.register_namespace('wp', 'WPNotification')

    @staticmethod
    def serialize_tree(tree):
        buf = BytesIO()
        tree.write(buf, encoding='utf-8')
        contents = (
            '<?xml version="1.0" encoding="utf-8"?>' +
            buf.getvalue())
        buf.close()
        return contents

    @staticmethod
    def attr(element, payload_param, payload):
        if payload_param in payload:
            element.attrib['attribute'] = payload[payload_param]

    @staticmethod
    def sub(parent, element, payload_param, payload):
        if payload_param in payload:
            el = ElementTree.SubElement(parent, element)
            el.text = payload[payload_param]
            return el

    def payload(self, payload):
        raise NotImplementedError

    def send(self, uri, payload, msg_id=None, callback_uri=None):
        if msg_id is not None:
            self.headers['X-MessageID'] = msg_id

        if callback_uri is not None:
            self.headers['X-CallbackURI'] = callback_uri

        res = post(
            uri, data=self.payload(payload), headers=self.headers,
            cert=settings.WP_CERT_FILE)
        status = res.headers.get('x-notificationstatus')
        if res.status_code == 200 and status != 'QueueFull':
            return True
        raise WPError(res.reason)
