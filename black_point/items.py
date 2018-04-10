# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy, datetime
from black_point.utils.sysutils import get_md5, extract_numbers
from black_point.settings import SQL_DATETIME_FORMAT


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

    def get_insert_sql(self):
        insert_sql = """
            INSERT INTO spider_hao6v
            (title, url, url_md5, cover_img, trans_name, video_name, `year`, origin, types, imdb_score, douban_score, minutes, director, starring, summary, download_links)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            ON DUPLICATE KEY UPDATE download_links=VALUES(download_links)
        """
        params = (self["title"], self["url"], self["url_md5"], self["cover_img"], self["trans_name"], self["video_name"], 
                self["year"], self["origin"], self["types"], self["imdb_score"], self["douban_score"], self["minutes"], 
                self["director"], self["starring"], self["summary"], self["download_links"])
        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    question_id = scrapy.Field()
    url = scrapy.Field()
    url_md5 = scrapy.Field()
    topics = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answers_num = scrapy.Field()
    followers_num = scrapy.Field()
    browsed_num = scrapy.Field()
    comments_num = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into spider_zhihu_question(question_id, url, url_md5, topics, title, content, answers_num,
              followers_num, browsed_num, comments_num
              )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), answers_num=VALUES(answers_num), followers_num=VALUES(followers_num),
              browsed_num=VALUES(browsed_num), comments_num=VALUES(comments_num)
        """
        question_id = self["question_id"]
        url = ",".join(self["url"])
        url_md5 = get_md5(url)
        topics = ",".join(self["topics"])
        title = "".join(self["title"])
        content = "".join(self["content"] if "content" in self else (""))
        answers_num = extract_numbers("".join(self["answers_num"]).replace(",", ""))
        followers_num = extract_numbers("".join(self["followers_num"]).replace(",", ""))
        browsed_num = extract_numbers("".join(self["browsed_num"]).replace(",", ""))
        comments_num = extract_numbers("".join(self["comments_num"]).replace(",", ""))
        params = (question_id, url, url_md5, topics, title, content, answers_num, followers_num, browsed_num, comments_num)
        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    answer_id = scrapy.Field()
    url = scrapy.Field()
    url_md5 = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    author_name = scrapy.Field()
    author_type = scrapy.Field()
    author_token = scrapy.Field()
    create_time = scrapy.Field()
    updated_time = scrapy.Field()
    voteup_count = scrapy.Field()
    comment_count = scrapy.Field()
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into spider_zhihu_answer(answer_id, url, url_md5, question_id, author_id, author_name, author_type,
              author_token, create_time, updated_time, voteup_count, comment_count, content
              )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE updated_time=VALUES(updated_time), voteup_count=VALUES(voteup_count), comment_count=VALUES(comment_count),
              content=VALUES(content)
        """
        url_md5 = get_md5(self["url"])
        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        updated_time = datetime.datetime.fromtimestamp(self["updated_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (self["answer_id"], self["url"], url_md5, self["question_id"], self["author_id"], self["author_name"], self["author_type"],
                    self["author_token"], create_time, updated_time, self["voteup_count"], self["comment_count"], self["content"])
        print(params)
        return insert_sql, params