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
    def __init__(self, **kwargs):
        super().__init__()
        # params used in threading/responding
        self.progress = 0
        self.status = BotAnalyzerStatus.IDLE
        self._stopper = threading.Event()
        # get and validate params
        self._get_params(**kwargs)
        # initialize db
        self.db_client = DatabaseClient(cfg.db_filepath)
        # validate sql_query
        self._validate_sql_query()

    def _get_params(self, **kwargs):
        params = {
            'keyword': str,
            'industry': int,
            'sql_query': str,
            'n_components': int,
            'n_features': int,
            'stop_words': list,
            'n_top_words': int,
            'n_topic_words': int,
        }

        # set params to self
        try:
            for name, val in kwargs.items():
                if params[name] is str:
                    setattr(self, name, str(val).strip())
                elif params[name] is int:
                    setattr(self, name, int(val))
                elif params[name] is list:
                    try:
                        setattr(self, name, [str(s).strip() for s in val.split(',')])
                    except:
                        # if not specified (ex. None)
                        setattr(self, name, [])
        except ValueError:
            raise ValueError(f'invalid {name}: "{val}"')
        except KeyError as err_key:
            raise KeyError(f'invalid param: "{err_key}"')

        # check if all params are assigned
        for name in params.keys():
            val = getattr(self, name)
            assert val is not None, f'param not found: "{name}"'

        # check ranges of numeric params
        numeric_params = {
            'industry': [0, 14],
            'n_components': [1, None],
            'n_features': [1, None],
            'n_top_words': [1, self.n_features],
            'n_topic_words': [1, self.n_features],
        }
        for name, req in numeric_params.items():
            val = getattr(self, name)
            if req[0] is not None:
                assert val >= req[0], f'{name} must be an integer >={req[0]}: "{val}"'
            if req[1] is not None:
                assert val <= req[1], f'{name} must be an integer <={req[1]}: "{val}"'

    def _validate_sql_query(self):
        if not self.sql_query:
            raise ValueError(f'Please enter an SQL query.')
        self.db_client.load_dataset(self.sql_query)

    def stop(self):
        # reset
        self.progress = 0
        self.status = BotAnalyzerStatus.IDLE
        # set event
        self._stopper.set()

    def run(self):
        try:
            # run initialization
            self.status = BotAnalyzerStatus.INITIALIZING

            # get urls
            if all([self.keyword, self.industry]):
                urls = get_urls_from_search(keyword=self.keyword, industry=self.industry)
            else:
                # skip running bot
                urls = None
            if self._stopper.isSet():
                return

            if urls is not None:
                # run bot
                self.status = BotAnalyzerStatus.CRAWLING
                bot = Bot(keyword=self.keyword, industry=self.industry)
                for progress in bot.run(urls, self.db_client):
                    self.progress = progress
                    if self._stopper.isSet():
                        return

            # run analyzer
            self.status = BotAnalyzerStatus.ANALYZING
            analyzer = Analyzer(sql_query=self.sql_query,
                                n_components=self.n_components,
                                n_features=self.n_features,
                                stop_words=self.stop_words,
                                n_top_words=self.n_top_words,
                                n_topic_words=self.n_topic_words)
            result = analyzer.run(self.db_client)

        except Exception as err:
            self.error = err
            self.traceback = traceback.format_exc()
            self.status = BotAnalyzerStatus.ERROR

        else:
            self.result = result
            self.status = BotAnalyzerStatus.COMPLETE
