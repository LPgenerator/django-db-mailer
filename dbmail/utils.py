# -*- encoding: utf-8 -*-


def premailer_transform(text):
    try:
        from premailer import transform

        return transform(text)
    except Exception, msg:
        print msg.__str__()
        return text


def get_ip(request):
    try:
        from ipware.ip import get_real_ip

        ip = get_real_ip(request)
        if ip is not None:
            return ip.strip()
    except ImportError:
        pass

    return request.META['REMOTE_ADDR'].split(',')[-1].strip()
