# Nikkei Article Bot

業界ニーズ調査用、日本経済新聞のプレスリリース文書を取得・解析するアプリです。


## Installation

**Linux環境が必要**


### 仮想環境作成・パッケージインストール

```bash
$ git clone http://172.16.127.102:8080/git/nikkei_article/nikkei_article_bot.git
$ cd nikkei_article_bot
$ python -m venv env
$ . env/bin/activate
$ pip install -r requirements.txt
```


### MeCab辞書(mecab-ipadic-neologd)のインストール

GitHub Repo: https://github.com/neologd/mecab-ipadic-neologd

```bash
$ git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
$ cd mecab-ipadic-neologd/
$ ./bin/install-mecab-ipadic-neologd -n -a -u

# インストール先を指定したい場合
$ mkdir -p ~/path/to/mecab-ipadic-neologd/
$ ./bin/install-mecab-ipadic-neologd -n -a -u -p ~/path/to/mecab-ipadic-neologd/

# テスト
$ python
>>>import MeCab
>>>m = MeCab.Tagger(' -d /home/<user>/path/to/mecab-ipadic-neologd/')
>>>m.parse('お試し')
```


## Usage
```bash
$ cd nikkei_article_bot
$ . env/bin/activate

# (for developers) create config.dev.ini to use your own settings
$ cp config.ini config.dev.ini
$ vi config.dev.ini

# show help
$ python run.py

# run app
$ python run.py app [PORT]

# run bot only
$ python run.py bot

# run analyzer only
$ python run.py analyzer

# run bot then analyzer
$ python run.py bot_analyzer
```
