# -*- encoding: utf-8 -*-

from itertools import chain

from push_notifications.models import APNSDevice, GCMDevice


def send(users, message, *args, **kwargs):
    """
    Site: https://github.com/jleclanche/django-push-notifications
    Desc: Handles models for storing and sending notification through
          appropriate service
    Takes in user ids and gets devices
    """
    apns = APNSDevice.objects.filter(user__in=users)
    gcm = GCMDevice.objects.filter(user__in=users)

    devices = list(chain(apns, gcm))

    for device in devices:
        device.send_message(message, *args, **kwargs)
    return True
