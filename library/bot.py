import os
import re
import random
import requests
import traceback
import threading
from time import sleep
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from library.constants import *
from library.config import Config
from library.db import DatabaseClient
from library.utils import get_urls

# read config
cfg = Config()


def get_articles_urls(csv_filepath):
    with open(csv_filepath, 'r') as f:
        urls = f.read().split()
    return urls


def clean_content(p_list):
    # remove first <p> element which contains only date
    p_list = p_list[1:]
    # remove <p> containing only url
    p_list = [p for p in p_list if not bool(re.search(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', p))]
    # remove stop words
    stop_words = ['参考画像', 'リリース']
    p_list = [p for p in p_list if not bool(re.search('|'.join(stop_words), p))]
    # join them all and return
    return ''.join(p_list)


def scrawl_page(url):
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
        article['link'] = url
        # date
        article['date'] = soup.find('dl', 'cmn-article_status').find('dd', 'cmnc-publish').text.strip()
        # company, industry
        # use the first category description only
        ele = soup.find('dd', 'm-pressRelease_Product_category_description')
        if ele:
            article['company'], article['industry'] = [e.text.strip() for e in ele.find_all('a')]
        else:
            article['company'], article['industry'] = [None, None]
        # content
        p_list = [e.text.strip() for e in soup.find('div', 'cmn-article_text').find_all('p')]
        article['content'] = clean_content(p_list)
    except:
        print(traceback.format_exc())
        return None

    return article


def run(csv_filepath, db_filepath=cfg.db_filepath, max_article=cfg.max_article):
    # initialize db
    db_client = DatabaseClient(db_filepath)

    # get urls if csv file doesn't exist
    if not os.path.exists(csv_filepath):
        get_urls(csv_filepath, keyword=cfg.keyword, industry=cfg.industry)

    # get urls from csv file
    urls = get_articles_urls(csv_filepath)

    for i, url in enumerate(urls):

        # break if exceeding max_article
        if max_article and i >= max_article:
            break

        # set random request interval 0.5s~2s
        sleep(round(random.uniform(0.5, 2), 1))

        # scrawl article
        article = scrawl_page(url)

        # skip to next article if failed
        if article is None:
            print(f"fail: {i+1}/{len(urls)} ({url})")
            continue

        # insert a record
        db_client.insert_record(article)

        print(f"done: {i+1}/{len(urls)} ({article['title']})")

        # calculate current progress
        if max_article:
            progress = round((i+1)/max_article*100, 1)
        else:
            progress = round((i+1)/len(urls)*100, 1)

        yield progress


class Bot(threading.Thread):
    def __init__(self, csv_filepath):
        super().__init__()
        self.progress = 0
        self.status = BotStatus.IDLE
        self.csv_filepath = csv_filepath
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        self.status = BotStatus.PROCESSING
        try:
            for current_progress in run(self.csv_filepath):
                # get current progress
                self.progress = current_progress
                # if stopped by user
                if self.stopped():
                    # reset bot
                    self.progress = 0
                    self.status = BotStatus.IDLE
                    return
        except Exception as err:
            self.error = err
            self.status = BotStatus.ERROR
        else:
            # ! dummy
            self.result = {
                '#0': ['最大化', '顧客', '体験', '価値'],
                '#1': ['農業', '環境', '栽培', '省資源'],
                '#2': ['最大化', '顧客', '体験', '価値'],
                '#3': ['農業', '環境', '栽培', '省資源'],
            }
            # ! dummy
            self.status = BotStatus.COMPLETE
