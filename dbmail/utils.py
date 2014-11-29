# -*- encoding: utf-8 -*-


def premailer_transform(text):
    try:
        from premailer import transform

        return transform(text)
    except Exception, msg:
        print msg.__str__()
        return text
