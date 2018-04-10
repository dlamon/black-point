# -*- coding: utf-8 -*-
__author__ = 'liaowei'
import hashlib, re

def get_md5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    md5 = hashlib.md5()
    md5.update(url)
    return md5.hexdigest()

def extract_numbers(text):
    match_re = re.match(".*?(\\d+).*", text)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums