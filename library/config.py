import threading
import configparser


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
        self.parser.read('config.ini', encoding='utf-8')

    @property
    def csv_filepath(self) -> str:
        return self.parser.get('bot', 'csv_filepath')

    @property
    def db_filepath(self) -> str:
        return self.parser.get('bot', 'db_filepath')

    @property
    def max_article(self) -> int:
        return self.parser.getint('bot', 'max_article')
