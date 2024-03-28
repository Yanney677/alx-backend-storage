#!/usr/bin/env python3
"""Web Cache and Tracker to access the URL
"""
import redis
import requests
from functools import wraps

store_value = redis.Redis()


def count_url_access(method):
    """Counts the number of times a URL is invoke
    """
    @wraps(method)
    def wrapper(url):
        cached_key = "cached:" + url
        cached_data = store_value.get(cached_key)
        if cached_data:
            return cached_data.decode("utf-8")

        count_key = "count:" + url
        html = method(url)

        store_value.incr(count_key)
        store_value.set(cached_key, html)
        store_value.expire(cached_key, 15)
        return html
    return wrapper


@count_access_url
def get_page(url: str) -> str:
    """Returns HTML content from the url"""
    request_value = requests.get(url)
    return request_value.text
