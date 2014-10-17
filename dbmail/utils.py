# -*- encoding: utf-8 -*-


def clean_cache_key(key):
    return key.replace('>', '').replace('<', '').replace(' ', '')


def premailer_transform(text):
    try:
        from premailer import transform

        return transform(text)
    except Exception, msg:
        print msg.__str__()
        return text
