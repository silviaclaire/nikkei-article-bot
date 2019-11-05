import re
import math
import requests
import urllib.parse
from bs4 import BeautifulSoup


def get_urls(out_file, keyword, industry):
    # start a search
    start_url = f'https://www.nikkei.com/pressrelease/?searchKeyword={keyword}&au={industry}'
    result = requests.get(start_url)
    assert result.status_code == 200
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

    print(f'items found: {len(urls)}')

    # save as csv
    with open(out_file, 'w') as f:
        f.writelines('\n'.join(urls))
