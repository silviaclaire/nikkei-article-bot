import pickle
import sqlite3
import traceback
import threading
import numpy as np
import pandas as pd

import MeCab
from sklearn.decomposition import NMF, LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from library.constants import *
from library.config import Config

# read config
cfg = Config()


class Analyzer(threading.Thread):
    def __init__(self,
                 n_components:int,
                 n_features:int,
                 stop_words:list,
                 n_top_words:int,
                 n_topic_words:int):
        super().__init__()
        # params used in threading/responding
        self.progress = 0
        self.status = AnalyzerStatus.IDLE
        self._stop = threading.Event()
        # params used in analyzing
        self.n_components = n_components
        self.n_features = n_features
        self.stop_words = stop_words
        self.n_top_words = n_top_words
        self.n_topic_words = n_topic_words

    def stop(self):
        # reset analyzer
        self.progress = 0
        self.status = AnalyzerStatus.IDLE
        # set event
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    @staticmethod
    def load_dataset(db_filepath, col='content'):
        with sqlite3.connect(db_filepath) as conn:
            df = pd.read_sql_query('SELECT id, title, content FROM articles', conn)
        data = df[col]
        return data

    def tokenize(self, text):
        text = str(text).lower()
        m = MeCab.Tagger(MECAB_DICTIONARY_PATH)
        words = m.parse(text)
        clean_tokens = []
        for row in words.split('\n'):
            word = row.split('\t')[0]
            if word == 'EOS':
                break
            else:
                if word in self.stop_words:
                    continue
                prop = row.split('\t')[1]
                if prop.split(',')[0] != '名詞':
                    continue
                elif prop.split(',')[1] in ['数', '非自立', '接続詞的', '接尾', '代名詞']:
                    continue
                elif prop.split(',')[2] in ['組織', '人名']:
                    continue
                else:
                    clean_tokens.append(word)
        return clean_tokens

    def vectorize(self, data):
        # Use tf-idf features for NMF.
        self.tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2,
                                           max_features=self.n_features,
                                           tokenizer=self.tokenize)
        self.tfidf = self.tfidf_vectorizer.fit_transform(data)
        # Use tf (raw term count) features for LDA.
        self.tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2,
                                        max_features=self.n_features,
                                        tokenizer=self.tokenize)
        self.tf = self.tf_vectorizer.fit_transform(data)

    def get_top_words(self):
        words = self.tf_vectorizer.get_feature_names()
        total_counts = np.zeros(len(words))
        for t in self.tf:
            total_counts += t.toarray()[0]
        top_words = sorted((zip(words, total_counts)), key=lambda x:x[1], reverse=True)[0:self.n_top_words]
        return top_words

    def get_topic_words(self, model, feature_names):
        topic_words = []
        for topic in model.components_:
            topic_words.append([feature_names[i] for i in topic.argsort()[:-self.n_topic_words-1:-1]])
        return topic_words

    def fit_model(self, model_type):
        assert model_type in ['nmf', 'lda'], f'Wrong model type ({model_type})'
        if model_type == 'nmf':
            # fit model
            nmf = NMF(n_components=self.n_components,
                      random_state=1,
                      alpha=.1,
                      l1_ratio=.5)
            nmf.fit(self.tfidf)
            # get top words per topic
            topic_words = self.get_topic_words(model=nmf, feature_names=self.tfidf_vectorizer.get_feature_names())
        elif model_type == 'lda':
            # fit model
            lda = LatentDirichletAllocation(n_components=self.n_components,
                                            max_iter=5,
                                            learning_method='online',
                                            learning_offset=50.,
                                            random_state=0)
            lda.fit(self.tf)
            # get top words per topic
            topic_words = self.get_topic_words(model=lda, feature_names=self.tf_vectorizer.get_feature_names())
        return topic_words

    def run(self):
        # run analyzer
        self.status = AnalyzerStatus.PROCESSING

        try:
            # load dataset
            data = self.load_dataset(cfg.db_filepath)
            print(f'n_samples:{len(data)}')
            if self.stopped():
                return

            # vectorize data
            self.vectorize(data)
            if self.stopped():
                return

            # get top words overall
            top_words = self.get_top_words()
            print(f'top words:\n{top_words}')
            if self.stopped():
                return

            # fit model to get topic words
            topic_words = {}
            for model_type in ['nmf', 'lda']:
                topic_words[model_type] = self.fit_model(model_type)
                print(f'topic words ({model_type}):\n{topic_words[model_type]}')
                if self.stopped():
                    return

        except Exception as err:
            print(traceback.format_exc())
            self.error = err
            self.status = AnalyzerStatus.ERROR

        else:
            self.result = dict(top_words=top_words, topic_words=topic_words)
            self.status = AnalyzerStatus.COMPLETE
