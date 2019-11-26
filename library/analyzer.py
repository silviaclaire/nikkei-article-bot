import os
import pickle
import numpy as np
import pandas as pd

import MeCab
import pyLDAvis
from pyLDAvis import sklearn as sklearn_lda
from sklearn.decomposition import NMF, LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from library.constants import *
from library.config import Config
from library.db import DatabaseClient
from library import NMFvis

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
        m = MeCab.Tagger(cfg.mecab_dictionary_path)
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
            # get topic ratios per article
            topic_ratios = model.transform(self.tfidf)

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
            # get topic ratios per article
            topic_ratios = model.transform(self.tf)

        return model, topic_words, topic_ratios

    def create_topic_ratios_df(self, topic_ratios):
        df = pd.DataFrame(columns=[f'topic #{i+1}' for i in range(len(topic_ratios[0]))])
        for i, ratios in enumerate(topic_ratios):
            df.loc[i] = list(ratios)
        df = pd.concat([self.data_df.loc[:, ['id', 'title', 'link']], df], axis=1)
        return df

    def save_topic_words(self, topic_words, model_type):
        filename = f'{model_type}_topic_words.csv'
        df = pd.DataFrame(columns=['topic'] + [f'word #{i+1}' for i in range(len(topic_words[0]))])
        for i, words in enumerate(topic_words):
            df.loc[i] = [i] + list(words)
        df.to_csv(os.path.join('data', filename), index=False, encoding='sjis')
        return filename

    def save_topic_ratios(self, topic_ratios_df, model_type):
        filename = f'{model_type}_topic_ratios.csv'
        # Open file to ignore UnicodeEncodeError.
        with open(os.path.join('data', filename), mode='w', encoding='shift-jis', errors='ignore') as f:
            topic_ratios_df.to_csv(f, index=False)
        return filename

    def save_visualization(self, model, model_type):
        if model_type == 'lda':
            ldavis_result = sklearn_lda.prepare(model, self.tf, self.tf_vectorizer)
            filename = 'lda_visualization.html'
            pyLDAvis.save_html(ldavis_result, os.path.join('app/static/', filename))
        elif model_type == 'nmf':
            tsne_groups = NMFvis.prepare_tsne_groups(model, self.tfidf, self.data_df)
            filename = 'nmf_visualization.html'
            NMFvis.save_html(tsne_groups, os.path.join('app/static/', filename))
        return filename

    def run(self, db_client=None):

        # initialize db
        if db_client is None:
            db_client = DatabaseClient(cfg.db_filepath)

        # load dataset
        self.data_df = db_client.load_dataset(sql_query=self.sql_query)
        print(f'n_samples:{len(self.data_df)}')

        # vectorize data
        self.vectorize(self.data_df['content'])

        # initialize result
        result = {
            'top_words': None,
            'models': {
                'nmf': {},
                'lda': {},
            },
        }

        # get top words overall
        result['top_words'] = self.get_top_words()
        print(f"top words:\n{result['top_words']}")

        for model_type in result['models'].keys():

            # fit model
            model, topic_words, topic_ratios = self.fit_model(model_type)

            # create topic_ratio_df for topic ratio table
            topic_ratios_df = self.create_topic_ratios_df(topic_ratios)

            # save as csv
            topic_words_filename = self.save_topic_words(topic_words, model_type)
            topic_ratios_filename = self.save_topic_ratios(topic_ratios_df, model_type)

            # print top words per topic
            print(f'topic words ({model_type}):')
            for idx, topic_str in enumerate([' '.join(a_topic) for a_topic in topic_words]):
                print(f'#{idx}: {topic_str}')

            # save visualization
            visualization_filename = self.save_visualization(model, model_type)
            print(f'visualization saved')

            # update result
            result['models'][model_type]['model'] = model
            result['models'][model_type]['topic_words'] = topic_words
            result['models'][model_type]['topic_ratios'] = topic_ratios_df.to_dict(orient='records')
            result['models'][model_type]['topic_words_filename'] = topic_words_filename
            result['models'][model_type]['topic_ratios_filename'] = topic_ratios_filename
            result['models'][model_type]['visualization_filename'] = visualization_filename

        return result
