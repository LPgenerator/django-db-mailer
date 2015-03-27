# -*- encoding: utf-8 -*-

from django.shortcuts import render


def browser_notification(request):
    return render(request, "browser_noitification.html")