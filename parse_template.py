#!/usr/bin/python
# -*- coding: utf-8 -*-

#***************************************************************************
#* 
#* Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#* 
#**************************************************************************/
"""
 * @This module is used to parse the arguments of the template, and then generate a Analytical report
 * @目前这个脚本只会提取一个页面中的第一个广告位信息，会忽略其他的。后续会增加上。
 * @author zhongzhiwei01(zhongzhiwei01@baidu.com)
 * @date 2014/08/19 15:13:28 
"""


import argparse
import codecs
import json
import logging
import re
import random
import os
import Queue
import subprocess
import string
import sys

import log
import html


def usage():
    """
    Usage function.
    """
    print "usage: parse_template.py [-h] [-v] [-c C]"


def init_log(log_path, level=logging.INFO, when="D", backup=7,
             format="%(levelname)s: %(asctime)s: %(filename)s:%(lineno)d * %(thread)d %(message)s",
             datefmt="%Y-%m-%d %H:%M:%S"):
    """
    init_log - initialize log module

    Args:
      log_path      - Log file path prefix.
                      Log data will go to two files: log_path.log and log_path.log.wf
                      Any non-exist parent directories will be created automatically
      level         - msg above the level will be displayed
                      DEBUG < INFO < WARNING < ERROR < CRITICAL
                      the default value is logging.INFO
      when          - how to split the log file by time interval
                      'S' : Seconds
                      'M' : Minutes
                      'H' : Hours
                      'D' : Days
                      'W' : Week day
                      default value: 'D'
      format        - format of the log
                      default format:
                      %(levelname)s: %(asctime)s: %(filename)s:%(lineno)d * %(thread)d %(message)s
                      INFO: 12-09 18:02:42: log.py:40 * 139814749787872 HELLO WORLD
      backup        - how many backup file to keep
                      default value: 7

    Return:
        logger: the log object.
    """
    formatter = logging.Formatter(format, datefmt)
    logger = logging.getLogger()
    logger.setLevel(level)

    dir = os.path.dirname(log_path)
    if not os.path.isdir(dir):
        os.makedirs(dir)

    handler = logging.handlers.TimedRotatingFileHandler(log_path + ".log",
                                                        when=when,
                                                        backupCount=backup)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = logging.handlers.TimedRotatingFileHandler(log_path + ".log.wf",
                                                        when=when,
                                                        backupCount=backup)
    handler.setLevel(logging.WARNING)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = init_log('./log/parse_page')


class Parser(object):
    """
    The main class to parse the template file.
    """
    def __init__(self, url_addr):
        self.url_addr = url_addr
        self.template_data = ""
        self.ad_info = {}
        self.url_queue = Queue.Queue()

    def run_phantomjs(self, tem_url):
        """
        Run the phantomJS program.
        Args:
            tem_url: The url of the template web page.
        """
        try:
            child = subprocess.Popen(['phantomjs', 'grap_page.js', tem_url], stdout=subprocess.PIPE)
            (output,errput)=child.communicate()
            child.wait()
            self.template_data = json.loads(output)
        except ValueError as e:
            logger.error(e)
            print 'hrere'
            print -1
            sys.exit(1)

    def parse_logo(self, logo_info):
        """
        Parse the logo of the template.
        """
        logo_tab = {
            "bd-logo": "logo位于右下角，大小为18*18px.",
            "bd-logo2": "logo位于左下角，大小为13*14px.",
            "bd-logo3": "logo位于左上角，大小为18*18px.",
            "bd-logo4": "logo位于左下角，大小为18*18px.",
            "bd-logo5": "logo位于右上角，大小为24*20px.",
            "logo": "logo位于右下角，大小为18*26px."
        }
        logo_title = logo_info['logo_title'].encode('utf-8')
        logo_style = logo_info['logo_style'].encode('utf-8')
        logo_href = logo_info['logo_href'].encode('utf-8')
        href_match = re.match(r"^http:/{2}wangmeng.baidu.com/?$", logo_href)
        if logo_style not in logo_tab:
            print "The logo style is wrong."
            logger.error('The logo style is not in the list.')
            return "logo类型不在当前类型池中，请检查。"
        elif not href_match:
            print "The href of the logo is wrong."
            logger.error('The href of the logo is wrong.')
            return "logo的点击链接不正确，请检查。"
        elif logo_title.strip(' /\n\r') is None:
            logoer.error('logo title is none.')
            return "logo中无title，请检查。"
        else:
            logger.info('The logo info is right, and the parse is complete.')
            logo_result = logo_tab[logo_style] + "logo可点击，点击链接为：" + logo_href + " logo上hover显示title为：" + logo_title.strip(' /\n\r')
            return logo_result

    def is_all_same(self, root_list, compare_element):
        """
        Judge if all the element in the root_list is same.
        Args:
            root_list: The root list.
            compare_element: The element that need to judge.
        """
        for i in range(len(root_list)):
            if (root_list[i][compare_element] is not None) and (root_list[0][compare_element] == root_list[i][compare_element]):
                continue
            else:
                return False
        return True

    def parse_toufang_items(self):
        """
        Parse the item of the template in toufang web page.
        """
        tm_logo_all = []
        tm_general_all = []
        ad_number_all = []
        tm_ads_all = []
        wn_info_all = []
        sync_info_all = []

        #得到页面中所有的winnotice请求信息
        winnotice_list = self.template_data['winnotice']
        if len(winnotice_list):
            for winnotice in winnotice_list:
                wn_info = {}
                wn_req = winnotice['winNoticeReq']
                wn_referer = winnotice['referer'].split('di=')[1]
                wn_info['wn_req'] = wn_req
                wn_info['wn_referer'] = wn_referer
                wn_info_all.append(wn_info)                

        #得到页面中所有的sync请求的信息
        sync_list = self.template_data['sync']
        if len(sync_list):
            for sync in sync_list:
                sync_info = {}
                sync_req = sync['syncReq']
                sync_referer = sync['referer']
                sync_info['sync_req'] = sync_req
                sync_info['sync_referer'] = sync_referer
                sync_info_all.append(sync_info)

        #得到页面中所有模板的iframe基本信息
        iframe_info_list = self.template_data['iframe_info']['iframe_information']
        if len(iframe_info_list):
            for iframe_info in iframe_info_list:
                tm_general_info = []
                iframe_height = iframe_info['iframe_height']
                iframe_weight = iframe_info['iframe_weight']
                iframe_first_link = iframe_info['iframe_first_link']
                iframe_second_link = iframe_info['iframe_second_link']
                ad_size = iframe_weight.encode('utf-8') + "*" + iframe_height.encode('utf-8')
                tm_general_info.append(u'模板广告位尺寸=' + ad_size)
                tm_general_info.append(u'一跳链接=' + iframe_first_link.replace('&', '&amp'))
                tm_general_info.append(u'二跳链接=' + iframe_second_link.replace('&', '&amp'))
                tm_general_all.append(tm_general_info)
        
        adframe_info_list = self.template_data['adframe_info']
        for adframe_info in adframe_info_list:
            logo_info_list = adframe_info['logo_information']
            #获取logo的信息
            if len(logo_info_list) > 0:
                logo_info = logo_info_list[0]
                ad_logo_info = self.parse_logo(logo_info)
                #得到页面中所有模板的logo信息
                tm_logo_all.append(ad_logo_info);
        
            #提取模板中广告的条数
            if adframe_info.has_key('floor_number') and adframe_info.has_key('room_number'):
                floor_number = adframe_info['floor_number']
                room_number = adframe_info['room_number']
                ad_number = room_number
            elif adframe_info.has_key('item_num'):
                ad_number = adframe_info['item_num']
            ad_number_all.append(ad_number)
        
            #提取每个模板每条广告中的item信息
            try:
                ad_number
            except NameError as e:
                print -1
                logger.error(e)
            else:
                if int(ad_number) > 0:
                    tm_ads_info = []    #模板中所有广告的信息
                    ads_info = adframe_info['items_information']
                    for (i, ad) in enumerate(ads_info):
                        tm_ad_info = [] #模板中每条广告的信息
                        ad_node = ad['item_node']  #iframe中的广告节点
                        if not self.is_all_same(ad_node, 'item_href') or not self.is_all_same(ad_node, 'item_target'):
                            print "模板数据不正确，请检查！！"
                            logger.error('The data of the template is wrong.')
                        else:
                            ad_general_info = []
                            ad_general_info.append(u'模板中item个数=' + str(len(ad_node)))
                            ad_general_info.append(u'广告点解链接=' + ad_node[0]['item_href'].encode('utf-8'))
                            ad_general_info.append(u'广告target=' + ad_node[0]['item_target'].encode('utf-8'))
                            tm_ad_info.append(ad_general_info)
                        #分析每条广告中的item元素
                        ad_item_info = []
                        for (j, ad_item) in enumerate(ad_node):
                            item_info = ad_item['item_info']
                            if item_info.find('<img') > -1:
                                ad_item_info.append(u'图片item=' + re.findall(r"src=(.+?)[ >]", item_info)[0].encode('utf-8'))
                            elif ad_item.has_key('item_class'):
                                item_style = self.parse_items_style(ad_item['item_class'])
                                ad_item_info.append(item_style.decode('utf-8') + '=' + item_info)
                        tm_ad_info.append(ad_item_info)
                        tm_ads_info.append(tm_ad_info)
                    tm_ads_all.append(tm_ads_info)
        self.produce_report(tm_general_all, tm_ads_all, ad_number_all, tm_logo_all, wn_info_all, sync_info_all)


    def produce_report(self, tm_general_all, tm_ads_all, ad_number_all, tm_logo_all, wn_info_all, sync_info_all):
        """
        Generate the web report for the template.
        Args:
            tm_general_all: The template's general information in the page.
            tm_ads_all: The ads's information in the template in the page.
            ad_number_all: The number of the ad in each template.
            tm_logo_all: The logo info of the template in the page.
        """
        total_report_table = html.XtsHtmlTable()

        total_report_table.add_head('页面整体统计项', '描述')
        tm_num_all = len(ad_number_all)
        wn_num = len(wn_info_all)
        sync_num = len(sync_info_all)
        total_item = "当前页面中共有模板广告位 " + str(tm_num_all) + "个；" + "发送winnotice请求 " + str(wn_num) + "条；" \
                + "发送sync请求共 " + str(sync_num) + "条。"
        total_report_table.add_body_line("综述：", total_item)

        wn_list = []
        for i in range(wn_num):
            wn_list.append(wn_info_all[i]['wn_req'])
        total_report_table.add_body_line("winnotice请求：", '\n'.join(wn_list))

        sync_list = []
        for i in range(sync_num):
            sync_list.append(sync_info_all[i]['sync_req'])
        total_report_table.add_body_line("sync请求：", '\n'.join(sync_list))

        for i in range(1):
      #  for i in range(tm_num_all):
            #加入模板的一跳与二跳整体信息
            if len(tm_general_all) > 0:
                for item in tm_general_all[i]:
                    item_list = item.split('=')
                    item1 = item_list[0]
                    item2 = item[item.index(item1) + len(item1) + 1:]
                    total_report_table.add_body_line(item1.encode('utf-8'), item2.encode('utf-8'))
            #加入logo统计信息
            total_report_table.add_body_line("logo信息", tm_logo_all[i])
            #加入模板广告item的统计信息
            if len(tm_ads_all[i]) != 0:
                ad_report_table = html.XtsHtmlTable()
                for ad in tm_ads_all[i]:
                    ad_report_table.add_head('广告信息统计', '描述')
                    for ad_info in ad:
                        for item in ad_info:
                            item_list = item.split('=')
                            item1 = item_list[0]
                            item2 = item[item.index(item1) + len(item1) + 1:]
                            ad_report_table.add_body_line(item1.encode('utf-8'), item2.encode('utf-8'))
            else:
                logger.error('The information of the ads in template is wrong.')

        #report_table.add_body_line(element, value)
        report_name = "template_report_" + ''.join(random.sample(string.digits * (6 / 10 + 1), 6))
        f = open('/home/users/zhongzhiwei01/nginx_pb/html/tm_report/' + report_name + ".html", 'w')
        f.write(str(total_report_table))
        f.write(str(ad_report_table))
        f.close()
        logger.info('The web report is complete.')
        print "http://cp01-rdqa-pool670.cp01.baidu.com:8045/tm_report/" + report_name + ".html"

    def parse_items_style(self, item_class):
        """
        Parse the style of the items.
        Args:
            item_class: The style of the item.
        """
        item_style = {
            "txt": "文字",
            "gra": "星级评定",
            "dow": "下载",
            "img": "图片",
            "tit": "广告标题",
            "cnt": "广告内容",
            "url": "广告url",
            "title": "广告标题",
            "desc": "广告描述",
            "imgHover": "广告图片"
        }
        item_class = item_class.split(' ')
        return item_style[item_class[0]]

    def start(self):
        """
        Start the program.
        """
        logger.info('Begin parsing ...')
        if self.url_addr is not None:
            self.run_phantomjs(self.url_addr)
            if self.template_data is not None:
                logger.info('The json string is get from the phantomJS program.')
                self.parse_toufang_items()
                logger.info('parse end.')


def main():
    """
    main    -The main function of the module.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", 
            help="display the version of the program", action="store_true")
    parser.add_argument("-l", help="read the url address")
    args = parser.parse_args()
    if args.version:
        print "version 1.0.0"
    elif args.l:
        url_addr = args.l
        parser = Parser(url_addr)
        parser.start()
    else:
        usage()
    

if __name__ == '__main__':
    main()
