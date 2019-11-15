import re
import math
import requests
import urllib.parse
from bs4 import BeautifulSoup


def _get_urls_per_industry(keyword, industry):
    start_url = f'https://www.nikkei.com/pressrelease/?searchKeyword={keyword}&au={industry}'
    result = requests.get(start_url)
    assert result.status_code == 200, f'Status code error ({result.status_code})'
    soup = BeautifulSoup(result.content, features='html.parser')

    # get total number of items to calculate total pages
    n_items_text = soup.select('h2.m-headline_text span')[0].text
    n_items = int(re.findall(r'\d+', n_items_text)[0])
    n_pages = math.ceil(n_items/30)

    urls = []

    # get article items per page
    for i in range(0, n_pages):
        page_url = start_url + f'&hm={i+1}'
        result = requests.get(page_url)
        soup = BeautifulSoup(result.content, features='html.parser')
        items = soup.find_all('li', 'm-newsListDotBorder_item')

        for item in items:
            # get article urls
            href = item.find('a', 'm-newsListDotBorder_link').get('href')
            urls.append(urllib.parse.urljoin('https://www.nikkei.com/', href))

    return urls


def get_urls_from_search(keyword, industry):
    # start a search
    assert 0 <= int(industry) <= 14, f'Industry must between 0~14 ({industry})'

    urls = []
    if industry == 0:
        # get all entries by searching each industry
        for industry_idx in range(1, 15):
            urls += _get_urls_per_industry(keyword, industry_idx)
    else:
        # get entries for only one industry
        urls = _get_urls_per_industry(keyword, industry)

    print(f'items found: {len(urls)}')

    return urls
