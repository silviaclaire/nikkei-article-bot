import requests
import urllib.parse
from bs4 import BeautifulSoup


def save_dummy_csv(out_file, keyword='ai'):
    # start a search
    result = requests.get(f'https://www.nikkei.com/pressrelease/?searchKeyword={KEYWORD}&au=0')
    assert result.status_code == 200

    # find all article items in page
    soup = BeautifulSoup(result.content, features='html.parser')
    items = soup.find_all('li', 'm-newsListDotBorder_item')
    print(f'items found: {len(items)}')

    # get article urls
    urls = []
    for item in items:
        href = item.find('a', 'm-newsListDotBorder_link').get('href')
        urls.append(urllib.parse.urljoin('https://www.nikkei.com/', href))

    # save as csv
    with open(out_file, 'w') as f:
        f.writelines('\n'.join(urls))
