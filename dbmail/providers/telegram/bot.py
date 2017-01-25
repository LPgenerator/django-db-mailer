# -*- encoding: utf-8 -*-

import telepot
from django.conf import settings


def send(to, message, **kwargs):
    """
       SITE: https://github.com/nickoala/telepot
       TELEGRAM API: https://core.telegram.org/bots/api

       Installation:
       pip install 'telepot>=10.4'
   """

    available_kwargs_keys = [
        'parse_mode',
        'disable_web_page_preview',
        'disable_notification',
        'reply_to_message_id',
        'reply_markup'
    ]

    available_kwargs = {
        k: v for k, v in kwargs.iteritems() if k in available_kwargs_keys
    }

    bot = telepot.Bot(settings.TELEGRAM_BOT_TOKEN)
    return bot.sendMessage(to, message, **available_kwargs)
