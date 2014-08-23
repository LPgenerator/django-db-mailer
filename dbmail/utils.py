# -*- encoding: utf-8 -*-


def clean_cache_key(key):
    return key.replace('>', '').replace('<', '').replace(' ', '')
