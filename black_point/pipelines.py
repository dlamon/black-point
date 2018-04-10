# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import sys, codecs, json, MySQLdb, MySQLdb.cursors, logging
from os import path
from twisted.enterprise import adbapi

class BlackPointPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonPipeline(object):
    def __init__(self):
        json_file_path = path.join(path.dirname(sys.path[0]), 'exports/export.json')
        self.file = codecs.open(json_file_path, 'w', encoding="utf-8")
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item
    def spider_closed(self, spider):
        self.file.close()


class MysqlPipeline(object):
    @classmethod
    def from_settings(cls, settings):
        return cls(settings)
    def __init__(self, settings):
        host = settings["MYSQL_HOST"]
        db = settings["MYSQL_DBNAME"]
        user = settings["MYSQL_USER"]
        passwd = settings["MYSQL_PASSWORD"]
        charset = settings["MYSQL_CHARSET"]
        self.conn = MySQLdb.connect(host, user, passwd, db, charset=charset, use_unicode=True)
        self.cursor = self.conn.cursor()
    def process_item(self, item, spider):
        insert_sql, params = item.get_insert_sql()
        self.cursor.execute(insert_sql, params)
        self.conn.commit()


class MysqlTwistedPipline(object):
    @classmethod
    def from_settings(cls, settings):
        conn_params = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset = settings["MYSQL_CHARSET"],
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **conn_params)
        return cls(dbpool)
    def __init__(self, dbpool):
        self.dbpool = dbpool
    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider) 
    def handle_error(self, failure, item, spider):
        spider.logger.error(failure)
    def do_insert(self, cursor, item):
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)