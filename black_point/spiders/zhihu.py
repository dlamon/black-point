# -*- coding: utf-8 -*-
import scrapy, json, time, hmac, re
from hashlib import sha1
from urllib import parse
from requests_toolbelt.multipart.encoder import MultipartEncoder
from scrapy.utils.project import get_project_settings
from scrapy.loader import ItemLoader
from black_point.items import ZhihuQuestionItem, ZhihuAnswerItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    start_urls = ['https://www.zhihu.com/question/270392402']

    start_answer_url = "http://www.zhihu.com/api/v4/questions/{}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={}&offset={}&sort_by=default"

    headers = {
        'origin': 'https://www.zhihu.com',
        'referer': 'https://www.zhihu.com/signup',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
    }

    
    def parse(self, response):
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x:True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\\d+))(/|$).*", url)
            time.sleep(1)
            if match_obj:
                url = match_obj.group(1)
                yield scrapy.Request(url=url, headers=self.headers, callback=self.parse_question)
            else:
                yield scrapy.Request(url=url, headers=self.headers, callback=self.parse)


    def parse_question(self, response):
        match_obj = re.match("(.*zhihu.com/question/(\\d+))(/|$).*", response.url)
        if match_obj:
            question_id = int(match_obj.group(2))
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        item_loader.add_value("question_id", question_id)
        item_loader.add_value("url", response.url)
        item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")
        item_loader.add_css("title", "h1.QuestionHeader-title::text")
        item_loader.add_css("content", "div.QuestionRichText span.RichText")
        item_loader.add_css("answers_num", "h4.List-headerText span::text")
        item_loader.add_css("followers_num", "button.NumberBoard-item.Button strong.NumberBoard-itemValue::text")
        item_loader.add_css("browsed_num", "div.NumberBoard-item strong.NumberBoard-itemValue::text")
        item_loader.add_css("comments_num", "div.QuestionHeader-Comment button::text")
        question_item = item_loader.load_item()
        url = self.start_answer_url.format(question_id, 20, 0)
        yield scrapy.Request(url=url, headers=self.headers, callback=self.parse_answers)
        yield question_item


    def parse_answers(self, response):
        answers_json = json.loads(response.text)
        is_end = answers_json["paging"]["is_end"]
        next_url = answers_json["paging"]["next"]
        for answer in answers_json["data"]:
            zhihuAnswerItem = ZhihuAnswerItem()
            zhihuAnswerItem["answer_id"] = answer["id"]
            zhihuAnswerItem["url"] = answer["url"]
            zhihuAnswerItem["question_id"] = answer["question"]["id"]
            zhihuAnswerItem["author_id"] = answer["author"]["id"]
            zhihuAnswerItem["author_name"] = answer["author"]["name"]
            zhihuAnswerItem["author_type"] = answer["author"]["user_type"]
            zhihuAnswerItem["author_token"] = answer["author"]["url_token"]
            zhihuAnswerItem["create_time"] = answer["created_time"]
            zhihuAnswerItem["updated_time"] = answer["updated_time"]
            zhihuAnswerItem["voteup_count"] = answer["voteup_count"]
            zhihuAnswerItem["comment_count"] = answer["comment_count"]
            zhihuAnswerItem["content"] = answer["content"]
            yield zhihuAnswerItem
        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answers)


    def start_requests(self):
        url = "https://www.zhihu.com/signup"
        return [scrapy.Request(url=url, headers=self.headers, callback=self.get_captcha)]


    def get_captcha(self, response):
        url = "https://www.zhihu.com/api/v3/oauth/captcha?lang=cn"        
        cookie_list = response.headers.getlist('Set-Cookie')
        cookies = {}
        for cookie in cookie_list:
            cookie = cookie.decode("utf-8")
            match_re = re.match("(.*?)=(.*?);.*", cookie)
            if match_re:
                key = match_re.group(1)
                value = match_re.group(2)
                cookies[key] = value
        yield scrapy.Request(
                url = url, 
                headers=self.headers, 
                cookies = cookies, 
                callback=self.login, 
                errback=self.get_captcha_errback, 
                dont_filter=True)


    def get_captcha_errback(self, response):
        self.logger.error("get_captcha_errback \r\n %s", response.value.response.body)


    def login(self, response):
        url = "https://www.zhihu.com/api/v3/oauth/sign_in"
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
        settings = get_project_settings()
        data = {
            "username": settings["ZHIHU_USERNAME"],
            "password": settings["ZHIHU_PASSWORD"],
            "grant_type": grant_type,
            "client_id": client_id,
            "source": source,
            "timestamp": timestamp,
            "signature": signature
        }
        multipartEncoder = MultipartEncoder(fields=data)
        boundary = multipartEncoder.boundary[2:]
        body = multipartEncoder.to_string()
        self.headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
        yield  scrapy.Request(
            url = url,
            method = "post",
            body = body,
            headers = self.headers,
            callback = self.login_callback,
            errback = self.login_errback,
            dont_filter=True
        )


    def login_callback(self, response):
        for url in self.start_urls:
            yield scrapy.Request(url=url, dont_filter=True, headers=self.headers)


    def login_errback(self, response):
       self.logger.error("login_errback \r\n %s", response.value.response.body)