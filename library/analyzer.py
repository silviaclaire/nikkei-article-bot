import pickle
import numpy as np

import MeCab
import pyLDAvis
from pyLDAvis import sklearn as sklearn_lda
from sklearn.decomposition import NMF, LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from library.constants import *
from library.config import Config
from library.db import DatabaseClient

# read config
cfg = Config()


class Analyzer:
    def __init__(self,
                 sql_query:str,
                 n_components:int,
                 n_features:int,
                 stop_words:list,
                 n_top_words:int,
                 n_topic_words:int):
        self.sql_query = sql_query
        self.n_components = n_components
        self.n_features = n_features
        self.stop_words = stop_words
        self.n_top_words = n_top_words
        self.n_topic_words = n_topic_words

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
            model = NMF(n_components=self.n_components,
                        random_state=1,
                        alpha=.1,
                        l1_ratio=.5)
            model.fit(self.tfidf)
            # get top words per topic
            topic_words = self.get_topic_words(model=model,
                                               feature_names=self.tfidf_vectorizer.get_feature_names())
        elif model_type == 'lda':
            # fit model
            model = LatentDirichletAllocation(n_components=self.n_components,
                                              max_iter=5,
                                              learning_method='online',
                                              learning_offset=50.,
                                              random_state=0)
            model.fit(self.tf)
            # get top words per topic
            topic_words = self.get_topic_words(model=model,
                                               feature_names=self.tf_vectorizer.get_feature_names())
        return model, topic_words

    def save_visualization(self, model, model_type):
        if model_type == 'lda':
            ldavis_result = sklearn_lda.prepare(model, self.tf, self.tf_vectorizer)
            html_filepath = f'data/ldavis_result.html'
            pyLDAvis.save_html(ldavis_result, html_filepath)
        else:
            # TODO: create visualization for nmf model
            html_filepath = 'data/hoge.html'
        return html_filepath

    def run(self, db_client=None):

        # initialize db
        if db_client is None:
            db_client = DatabaseClient(cfg.db_filepath)

        # load dataset
        data = db_client.load_dataset(sql_query=self.sql_query)
        print(f'n_samples:{len(data)}')

        # vectorize data
        self.vectorize(data)

        # get top words overall
        top_words = self.get_top_words()
        print(f'top words:\n{top_words}')

        models = {}
        topic_words = {}

        for model_type in ['nmf', 'lda']:
            # fit model
            models[model_type], topic_words[model_type] = self.fit_model(model_type)
            # print top words per topic
            print(f'topic words ({model_type}):')
            for idx, topic_str in enumerate([' '.join(a_topic) for a_topic in topic_words[model_type]]):
                print(f'#{idx}: {topic_str}')
            # save visualization
            html_filepath = self.save_visualization(models[model_type], model_type)
            print(f'visualization saved to {html_filepath}')

        return top_words, topic_words, html_filepath
