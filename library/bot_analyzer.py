import traceback
import threading

from library.constants import *
from library.config import Config
from library.bot import Bot
from library.analyzer import Analyzer
from library.db import DatabaseClient
from library.utils import get_urls_from_search

# read config
cfg = Config()


class BotAnalyzer(threading.Thread):
    def __init__(self,
                 keyword:str,
                 industry:int,
                 sql_query:str,
                 n_components:int,
                 n_features:int,
                 stop_words:list,
                 n_top_words:int,
                 n_topic_words:int):

        super().__init__()
        # params used in threading/responding
        self.progress = 0
        self.status = BotAnalyzerStatus.IDLE
        self._stop = threading.Event()
        # params
        self.keyword = keyword
        self.industry = industry
        self.sql_query = sql_query
        self.n_components = n_components
        self.n_features = n_features
        self.stop_words = stop_words
        self.n_top_words = n_top_words
        self.n_topic_words = n_topic_words

    def stop(self):
        # reset
        self.progress = 0
        self.status = BotAnalyzerStatus.IDLE
        # set event
        self._stop.set()

    def run(self):
        try:
            # run initialization
            self.status = BotAnalyzerStatus.INITIALIZING

            # initialize db
            db_client = DatabaseClient(cfg.db_filepath)
            if self._stop.isSet():
                return

            # get urls
            if all([self.keyword, self.industry]):
                urls = get_urls_from_search(keyword=self.keyword, industry=self.industry)
            else:
                # skip running bot
                urls = None
            if self._stop.isSet():
                return

            if urls is not None:
                # run bot
                self.status = BotAnalyzerStatus.SCRAWLING
                bot = Bot(keyword=self.keyword, industry=self.industry)
                for progress in bot.run(urls, db_client):
                    self.progress = progress
                    if self._stop.isSet():
                        return

            # run analyzer
            self.status = BotAnalyzerStatus.ANALYZING
            analyzer = Analyzer(sql_query=self.sql_query,
                                n_components=self.n_components,
                                n_features=self.n_features,
                                stop_words=self.stop_words,
                                n_top_words=self.n_top_words,
                                n_topic_words=self.n_topic_words)
            result = analyzer.run(db_client)

        except Exception as err:
            self.error = err
            self.traceback = traceback.format_exc()
            self.status = BotAnalyzerStatus.ERROR

        else:
            self.result = result
            self.status = BotAnalyzerStatus.COMPLETE
