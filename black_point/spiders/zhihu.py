# -*- coding: utf-8 -*-
from hashlib import sha1
import scrapy
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json
import time
import hmac
import re


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    headers = {
        'origin': 'https://www.zhihu.com',
        'referer': 'https://www.zhihu.com/signup',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
    }

    def parse(self, response):
        with open("index_page.html", "wb") as f:
            f.write(response.text.encode("utf-8"))
        pass
    
    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/signup', headers=self.headers, callback=self.get_capsion_ticket)]

    def get_capsion_ticket(self, response):
        cookies = response.headers.getlist('Set-Cookie')
        cookie_dict = {}
        cookie_dict["_zap"] = '6fcd1339-a0d4-4359-8e96-05b1044b9de8'
        cookie_dict["l_cap_id"] = '"NGM0MmJjNmNlZmM1NGYyYjgwMzg5NjMwMzMwYzlkMjE=|1522600732|30163cf83044a403676d61f27f2af0567fadba5f"'
        cookie_dict["r_cap_id"] = '"YWZjMDhiYzFhNjRiNDEwMWI2NzZmNDE4ZTE1NGZlNjE=|1522600732|6dd56ecae06caf9a73e167787b7e18dcf23cd39b"'
        cookie_dict["cap_id"] = '"YzNhYTk5MzY0MmZhNGYwMWE2OTMzOTZlOGQ1YWM2YTU=|1522600732|b1b4bb925b6d7e417e6d83d873204a615c4a080d"'
        for cookie in cookies:
            cookie = cookie.decode("utf-8")
            match_re = re.match('(.*?)=(.*?);.*', cookie)
            if match_re:
                key = match_re.group(1)
                value = match_re.group(2)
                cookie_dict[key] = value
        return [scrapy.Request('https://www.zhihu.com/api/v3/oauth/captcha?lang=cn', 
            headers=self.headers, 
            cookies = cookie_dict, 
            callback=self.login, 
            errback=self.get_capsion_ticket_errorback, 
            dont_filter=True)]

    def get_capsion_ticket_errorback(self, response):
        print("#########################################################")
        print(response.value.response.body)
        print("get_capsion_ticket_errorback")
    

    def login(self, response):
        post_url = "https://www.zhihu.com/api/v3/oauth/sign_in"
        cookies = response.headers.getlist('Set-Cookie')
        cookie_dict = {}
        for cookie in cookies:
            cookie = cookie.decode("utf-8")
            match_re = re.match('(.*?)=(.*?);.*', cookie)
            if match_re:
                key = match_re.group(1)
                value = match_re.group(2)
                cookie_dict[key] = value

        grant_type = "password"
        client_id = "c3cef7c66a1843f8b3a9e6a1e3160e20"
        source = "com.zhihu.web"
        timestamp = str((int(round(time.time() * 1000))))

        h = hmac.new(b"d1b964811afb40118a12068ff74a12f4", digestmod=sha1)
        h.update(grant_type.encode("utf-8"))
        h.update(client_id.encode("utf-8"))
        h.update(source.encode("utf-8"))
        h.update(timestamp.encode("utf-8"))
        signature = h.hexdigest()

        post_data = {
            "username": "+86xxx",
            "password": "xxx",
            "grant_type": grant_type,
            "client_id": client_id,
            "source": source,
            "timestamp": timestamp,
            "signature": signature
        }
        me = MultipartEncoder(fields=post_data)
        me_boundary = me.boundary[2:]  #need this in headers
        me_body = me.to_string()       #contains the request body
        self.headers['Content-Type'] = 'multipart/form-data; boundary=' + me_boundary
        yield  scrapy.Request(
            url = post_url,
            method = 'post',
            #cookies = cookie_dict,
            body = me_body,
            headers = self.headers,
            callback = self.login_callback,
            errback = self.login_errorback,
            dont_filter=True
        )

    def login_callback(self, response):
        print("#########################################################")
        print(response)
        print("login_callback")
        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True, headers=self.headers)



    def login_errorback(self, response):
        print("#########################################################")
        print(response.value.response.body)
        print("login_errorback")