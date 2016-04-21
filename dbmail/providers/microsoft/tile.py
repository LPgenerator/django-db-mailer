from dbmail.providers.microsoft.base import MPNSBase, ElementTree


class MPNSTile(MPNSBase):
    NOTIFICATION_CLS = 1
    TARGET = 'token'

    @staticmethod
    def clear(parent, element, payload_param, payload):
        if payload_param in payload:
            el = ElementTree.SubElement(parent, element)
            if payload[payload_param] is None:
                el.attrib['Action'] = 'Clear'
            else:
                el.text = payload[payload_param]
            return el

    def payload(self, payload):
        root = ElementTree.Element("{WPNotification}Notification")
        tile = ElementTree.SubElement(root, '{WPNotification}Tile')
        self.attr(tile, 'id', payload)
        self.attr(tile, 'template', payload)
        self.sub(
            tile, '{WPNotification}BackgroundImage',
            'background_image', payload)
        self.clear(tile, '{WPNotification}Count', 'count', payload)
        self.clear(tile, '{WPNotification}Title', 'title', payload)
        self.clear(
            tile, '{WPNotification}BackBackgroundImage',
            'back_background_image', payload)
        self.clear(tile, '{WPNotification}BackTitle', 'back_title', payload)
        self.clear(
            tile, '{WPNotification}BackContent', 'back_content', payload)
        return self.serialize_tree(ElementTree.ElementTree(root))


def send(uri, message, **kwargs):
    kwargs['title'] = kwargs.pop("event", 'App')
    kwargs['text1'] = message
    return MPNSTile().send(uri, kwargs)
