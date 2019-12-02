import threading
import configparser
import os


class Config:
    # シングルトンのためクラスの継承禁止
    __instance = None
    __lock = threading.Lock()

    def __new__(cls, _=None):
        with cls.__lock:
            if cls.__instance is None:
                cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self):
        # プログラムを終了するまで設定ファイルの再読み込みはできない
        if hasattr(self, 'parser'):
            return

        self.parser = configparser.ConfigParser()

        # 開発用configファイルが存在する場合そちらをロードする
        if os.path.exists('config.dev.ini'):
            self.parser.read('config.dev.ini', encoding='utf-8')
            print('using development config')
        else:
            self.parser.read('config.ini', encoding='utf-8')
            print('using production config')

    @property
    def keyword(self) -> str:
        return self.parser.get('bot', 'keyword')

    @property
    def industry(self) -> int:
        return self.parser.getint('bot', 'industry')

    @property
    def csv_filepath(self) -> str:
        return self.parser.get('bot', 'csv_filepath')

    @property
    def sql_query(self) -> str:
        return self.parser.get('analyzer', 'sql_query')

    @property
    def n_components(self) -> int:
        return self.parser.getint('analyzer', 'n_components')

    @property
    def n_features(self) -> int:
        return self.parser.getint('analyzer', 'n_features')

    @property
    def stop_words(self) -> str:
        return self.parser.get('analyzer', 'stop_words')

    @property
    def n_top_words(self) -> int:
        return self.parser.getint('analyzer', 'n_top_words')

    @property
    def n_topic_words(self) -> int:
        return self.parser.getint('analyzer', 'n_topic_words')

    @property
    def db_filepath(self) -> str:
        return os.path.join('./data', self.parser.get('developer', 'db_filename'))

    @property
    def max_article(self) -> int:
        return self.parser.getint('developer', 'max_article')

    @property
    def mecab_dictionary_path(self) -> str:
        return self.parser.get('developer', 'mecab_dictionary_path')
