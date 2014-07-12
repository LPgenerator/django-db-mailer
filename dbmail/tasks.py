# -*- coding: utf-8 -*-

from dbmail.send_mail import SendMail
from celery import task


@task(name='dbmail.send_db_mail')
def send_db_mail(*args, **kwargs):
    return SendMail(*args, **kwargs).send()
