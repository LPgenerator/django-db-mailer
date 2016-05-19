from dbmail.providers.microsoft.base import MPNSBase, ElementTree


class MPNSToast(MPNSBase):
    NOTIFICATION_CLS = 2
    TARGET = 'toast'

    def payload(self, payload):
        root = ElementTree.Element("{WPNotification}Notification")
        toast = ElementTree.SubElement(root, '{WPNotification}Toast')
        self.sub(toast, '{WPNotification}Text1', 'text1', payload)
        self.sub(toast, '{WPNotification}Text2', 'text2', payload)
        self.sub(toast, '{WPNotification}Sound', 'sound', payload)
        self.sub(toast, '{WPNotification}Param', 'param', payload)
        self.sub(toast, '{WPNotification}Path', 'path', payload)
        return self.serialize_tree(ElementTree.ElementTree(root))


def send(uri, message, **kwargs):
    kwargs['text1'] = kwargs.pop("event", 'App')
    kwargs['text2'] = message
    return MPNSToast().send(uri, kwargs)
