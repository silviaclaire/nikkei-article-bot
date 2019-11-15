import os
import re
import random
import requests
import traceback
from time import sleep
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from library.constants import *
from library.config import Config
from library.db import DatabaseClient
from library.utils import get_urls_from_search

# read config
cfg = Config()


class Bot:
    def __init__(self, keyword, industry):
        self.keyword = keyword
        self.industry = industry
        self.progress = 0

    @staticmethod
    def _clean_content(p_list):
        # remove first <p> element which contains only date
        p_list = p_list[1:]
        # remove <p> containing only url
        p_list = [p for p in p_list if not bool(re.search(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', p))]
        # remove stop words
        stop_words = ['参考画像', 'リリース']
        p_list = [p for p in p_list if not bool(re.search('|'.join(stop_words), p))]
        # join them all and return
        return ''.join(p_list)

    def _scrawl_page(self, url):
        # get article page
        headers = {'User-Agent': UserAgent().random}
        result = requests.get(url,headers=headers)

        # skip to next article if failed
        if result.status_code != 200:
            return None

        # parse page
        soup = BeautifulSoup(result.content, features='html.parser')

        # store information of article
        # NOTE: key must be initialized in the same order as the headers in DB
        try:
            article = {}
            # title
            article['title'] = soup.find('h1', 'cmn-article_title').find('span', 'JSID_key_fonthln').text.strip()
            # url
            article['link'] = url.split('?')[0]
            # date
            article['date'] = soup.find('dl', 'cmn-article_status').find('dd', 'cmnc-publish').text.strip()
            # industry
            if self.industry:
                article['industry'] = INDUSTRY_OPTIONS[self.industry]
            else:
                # use the first category description only
                ele = soup.find('dd', 'm-pressRelease_Product_category_description')
                if ele:
                    article['industry'] = [e.text.strip() for e in ele.find_all('a')][1]
                else:
                    article['industry'] = None
            # content
            p_list = [e.text.strip() for e in soup.find('div', 'cmn-article_text').find_all('p')]
            article['content'] = self._clean_content(p_list)
        except:
            print(traceback.format_exc())
            return None

        return article

    def run(self, urls=None, db_client=None):

        if db_client is None:
            # initialize db
            db_client = DatabaseClient(cfg.db_filepath)

        if urls is None:
            # get urls
            urls = get_urls_from_search(keyword=self.keyword, industry=self.industry)

        if len(urls) == 0:
            raise Exception('Urls not found')

        for i, url in enumerate(urls):

            # break if exceeding max_article
            if cfg.max_article and i >= cfg.max_article:
                break

            # set random request interval 0.5s~2s
            sleep(round(random.uniform(0.5, 2), 1))

            # scrawl article
            article = self._scrawl_page(url)

            # skip to next article if failed
            if article is None:
                print(f"fail: {i+1}/{len(urls)} ({url})")
                continue

            # insert a record
            db_client.insert_record(article)

            print(f"done: {i+1}/{len(urls)} ({article['title']})")

            # calculate current progress
            if cfg.max_article:
                self.progress = round((i+1)/cfg.max_article*100, 1)
            else:
                self.progress = round((i+1)/len(urls)*100, 1)

            yield self.progress
