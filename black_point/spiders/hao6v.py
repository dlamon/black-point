# -*- coding: utf-8 -*-
import scrapy
import re
import sys
import logging
from os import path
from urllib import parse
from scrapy.http import Request
from black_point.items import Hao6vItem
from black_point.utils.sysutils import getMd5

class Hao6vSpider(scrapy.Spider):
    name = 'hao6v'
    allowed_domains = ['www.hao6v.com']
    start_urls = ['http://www.hao6v.com/dy/index.html']
    #start_urls = ['http://www.hao6v.com/dy/2017-12-25/MaFanDaLe.html']

    def parse(self, response):
        list_urls = response.css(".list a::attr(href)").extract()
        for url in list_urls:
            yield Request(url=parse.urljoin(response.url, url), callback=self.parse_detail)
        nav_urls = response.xpath('//*[@id="main"]/div[1]/div/div[2]').extract_first("")
        next_url = ""
        match_re = re.match('.*href="(.*)">下一页.*', nav_urls)
        if match_re:
            next_url = match_re.group(1)
            if next_url:
                self.logger.info("--> spider url %s <--", next_url)
                yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)
            else:
                self.logger.error("get next url error!")    
        else:
            self.logger.info("===finish to parse www.hao6v.com===")


    def parse_detail(self, response):
        parse_index = 1
        title = response.xpath('//*[@id="main"]/div[1]/div/h1/text()').extract_first("").strip()
        cover_img = response.xpath('//*[@id="endText"]/p[1]/img/@src').extract_first("").strip()
        cover_content = response.xpath('//*[@id="endText"]/p[%s]' % parse_index).extract_first("").replace("\u3000", "").replace("\r\n", " ").replace("◎", "@").replace("\xa0", "")
        for index in range(10):
            match_re = re.match(".*(译\\s*?名|又\\s*?名|片\\s*名|年\\s*代|产\\s*地|导\\s*演|主\\s*演).*", cover_content)
            if not match_re:
                parse_index = parse_index + 1
                cover_content = response.xpath('//*[@id="endText"]/p[%s]' % parse_index).extract_first("").replace("\u3000", "").replace("\r\n", " ").replace("◎", "@").replace("⊙", "@").replace("\xa0", "")
            else:
                break
        if index + 1 == 10:
            logging.error("--> can't find resolvable content url %s <--" % response.url)
            return

        summary = ""
        match_re = re.match(".*简\\s*?介(.*?)(@|<img|</p|<a).*", cover_content)
        if match_re:
            summary = match_re.group(1)
            if not summary:
                parse_index = parse_index + 1
                summary = response.xpath('//*[@id="endText"]/p[%s]' % parse_index).extract_first("").strip().replace("◎", "").replace("\u3000", "").replace("<p>", "").replace("</p>", "").replace("&nbsp", "")    
        else:
            parse_index = parse_index + 1
            summary = response.xpath('//*[@id="endText"]/p[%s]' % parse_index).extract_first("").strip().replace("◎", "").replace("\u3000", "").replace("<p>", "").replace("</p>", "").replace("&nbsp", "")
            if re.findall("简\\s*?介", summary):
                summary = summary.replace("简\\s*?介", "")
                if (len(summary) < 10 or "译\\s*?名" in summary):
                    parse_index = parse_index + 1
                    summary = response.xpath('//*[@id="endText"]/p[%s]' % parse_index).extract_first("").strip().replace("◎", "")
            else:
                parse_index = parse_index + 1
                summary = response.xpath('//*[@id="endText"]/p[%s]' % parse_index).extract_first("").strip().replace("◎", "").replace("\u3000", "").replace("<p>", "").replace("</p>", "")
                if re.findall("简\\s*?介", summary):
                    summary = summary.replace("简\\s*?介", "").replace("<br>", "").replace("\r\n", "").replace("\xa0", "")
                    if len(summary) < 5:
                        parse_index = parse_index + 1
                        summary = response.xpath('//*[@id="endText"]/p[%s]' % parse_index).extract_first("").strip().replace("◎", "")

        summary = self.parse_summary(summary)

        download_links = ""
        tables = response.xpath('//table[@bgcolor="#0099cc"]').extract()
        if tables:
            for index in range(len(tables)):
                download_links = self.parse_download_links(tables[-(index+1)].strip())
                if download_links:
                    break
        else:
            tables = response.xpath('//table[@bgcolor="#9999ff"]').extract()
            if tables:
                for index in range(len(tables)):
                    download_links = self.parse_download_links(tables[-(index+1)].strip())
                    if download_links:
                        break
        if download_links:
            download_links = ",".join(download_links)

        cover_dict = self.parse_cover(cover_content)    
        parsed_dict = dict(cover_dict)
        parsed_dict["title"] = title
        parsed_dict["cover_img"] = cover_img
        parsed_dict["summary"] = summary
        parsed_dict["download_links"] = download_links
        #self.print_dict(response.url, parsed_dict)
        
        hao6vItem = Hao6vItem()
        hao6vItem["url"] = response.url
        hao6vItem["url_md5"] = getMd5(response.url)
        for (key, value) in parsed_dict.items():
            hao6vItem[key] = value
        
        logging.info("### spider sub url %s finish ###", response.url)
        yield hao6vItem

    def parse_cover(self, content):
        cover_dict = {}
        trans_name = video_name = year = origin = types = director = starring = ""
        imdb_score = douban_score = minutes = 0
        match_re = re.match(".*?(译\\s*?名|又\\s*?名)(</font>|】)*(.*?)(@|<|<br>).*", content)
        if match_re:
            trans_name = match_re.group(3).replace(":", "").replace("：", "").strip()
        match_re = re.match(".*?(片\\s*?名)(</font>|】)*(.*?)(@|<|<br>).*", content)
        if match_re:
            video_name = match_re.group(3).replace(":", "").replace("：", "").strip()
        match_re = re.match(".*?(年\\s*?代)(</font>|】)*(.*?)(@|<br>|\\().*", content)
        if match_re:
            year = match_re.group(3).replace(":", "").replace("：", "").strip()
        match_re = re.match(".*?(产\\s*?地|地\\s*?区|国\\s*?家)(</font>|】)*.*?>(.*?)(</a>|<br>|@).*", content)
        if match_re:
            origin = match_re.group(3).replace(":", "").replace("：", "").strip()
            if not origin:
                match_re = re.match(".*?(产\\s*?地|地\\s*?区|国\\s*?家)(</font>|】)*.*?>*?</a>.*?>(.*?)</a>.*", content)
                if match_re:
                    origin = match_re.group(3).replace(":", "").replace("：", "").strip()
        match_re = re.match(".*?(类\\s*?别|类\\s*?型)(</font>|】)*(.*?)(@|<br>|/a>).*", content)
        if match_re:
            types = match_re.group(3).replace(":", "").replace("：", "").strip()
            types = re.findall(">([\u4E00-\u9FA5]*)<", types)
            if types:
                types = ",".join(types)
            else:
                types = ""
        match_re = re.match(".*?(IMDb评分|异国评分)(</font>|】)*(.*?)/.*", content)
        if match_re:
            imdb_score = match_re.group(3).replace(":", "").replace("：", "").strip()
            imdb_score = float(imdb_score)
        match_re = re.match(".*?(豆瓣评分)(</font>|】)*(.*?)/.*", content)
        if match_re:
            douban_score = match_re.group(3).replace(":", "").replace("：", "").strip()
            douban_score = float(douban_score)
        match_re = re.match(".*?(片\\s*?长)(</font>|】)*?(\\d+).*", content)
        if match_re:
            minutes = match_re.group(3).replace(" ", ",").replace(":", "").replace("：", "").strip()
            minutes = int(minutes)
        match_re = re.match(".*?(导\\s*?演)(</font>|】)*(.*?)(@|<|<br>).*", content)
        if match_re:
            director = match_re.group(3).replace(":", "").replace("：", "")
        match_re = re.match(".*?(主\\s*?演)(</font>|】)*(.*?)(@|<|<br>).*", content)
        if match_re:
            starring = match_re.group(3).replace(":", "").replace("：", "")
        cover_dict = {'trans_name': trans_name, 'video_name': video_name, 'year': year, 'origin': origin, 
                        'types': types, 'imdb_score': imdb_score, 'douban_score': douban_score, 'minutes': minutes,
                        'director': director, 'starring': starring}
        return cover_dict


    def parse_summary(self, content):
        match_re = re.match(".*\u3000(.*?)(<br>|</p>).*", content)
        summary = content.replace("\xa0", "").strip()
        if match_re:
            summary = match_re.group(1)
        summary = summary.replace("</font>", "").replace("<br>", "").replace("\r\n", "").replace(":", "").replace(" ", "").replace("<p>", "")
        return summary


    def parse_download_links(self, content):
        download_links = re.findall("(磁力.*</a>|电驴.*</a>|网盘链接.*</td>|<a.*</a>)", content)
        if not download_links:
            download_links = ""
        return download_links


    def print_dict(self, url, dict):
        self.logger.info("===============================================")
        self.logger.info("[url] = %s", url)
        for (key, value) in dict.items():
            if value:
                self.logger.info("[%s] = %s", key, value)
            elif key == "types" or key == "director" or key == "title" or key == "cover_img" or key == "summary" or key == "download_links" or key == "origin":
                self.logger.warning("[%s] = %s", key, value)
        self.logger.info("===============================================")

