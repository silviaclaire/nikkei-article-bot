import os
import re
import random
import requests
import traceback
from time import sleep
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from library.config import Config
from library.db import DatabaseClient
from library.utils import save_dummy_csv

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

    # make a dummy if csv file doesn't exist
    if not os.path.exists(csv_filepath):
        save_dummy_csv(csv_filepath)

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

