# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BlackPointItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class Hao6vItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    url_md5 = scrapy.Field()
    cover_img = scrapy.Field()
    trans_name = scrapy.Field()
    video_name = scrapy.Field()
    year = scrapy.Field()
    origin = scrapy.Field()
    types = scrapy.Field()
    imdb_score = scrapy.Field()
    douban_score = scrapy.Field()
    minutes = scrapy.Field()
    director = scrapy.Field()
    starring = scrapy.Field()
    summary = scrapy.Field()
    download_links = scrapy.Field()
