#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 执行爬虫, 并对对房源进行信息统计 """
import scrapydo
import time
import sys
import logging
import re
from lianjia_crawler.pipelines import MongoDBPipeline
from lianjia_crawler.spiders.item_spider import ItemSpider
from lianjia_crawler.spiders.link_spider import LinkSpider


reload(sys)
sys.setdefaultencoding('utf8')

scrapydo.setup()


def summarize():
    t0 = time.time()

    for link in mongo.get_links():
        _min = 9999999  # 每平米最低价格
        _max = 0        # 每平米最高价格
        total = 0      # 每平米总价格
        items = mongo.items.find({"link_id": link["_id"]})
        if items.count() == 0:
            continue
        for item in items:
            unit_price = int(re.sub("\D", "", item["unit_price"]))
            if _min > unit_price:
                _min = unit_price
            if _max < unit_price:
                _max = unit_price
            total += unit_price
        _avg = total / items.count()

        mongo.db["sum"].insert({
            "time": t0,
            "location": link["location"],
            "avg": _avg,
            "min": _min,
            "max": _max
        })
        print link["district"], link["location"], "均价:", _avg, "最低:", _min, "最高:", _max


if __name__ == "__main__":
    logging.basicConfig(
        filename='spider.log',
        format='%(levelname)s %(asctime)s: %(message)s',
        level=logging.DEBUG
    )
    # while True:
    mongo = MongoDBPipeline()
    t = time.time()
    # 1、爬取连接，并更新district
    scrapydo.run_spider(LinkSpider)

    # 2、爬取item
    while True:
        print "爬取房源中....."
        scrapydo.run_spider(ItemSpider)
        if mongo.get_failed_urls().count() == 0:
            break
        print "开始再次爬取房源...."

    print "爬取结束, 耗时%d秒" % (time.time() - t)

    # 3、根据location的名字进行统计
    print "开始统计..."
    summarize()

    # 4、清空items表和link表, 暂时不清空
    # mongo.db["items"].delete_many({})
    # mongo.db["links"].delete_many({})

    # print "统计完成!!歇5天!!"
    # time.sleep(5 * 24 * 3600)  # 五天之后再次运行
