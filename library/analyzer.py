#!/usr/bin/env python
# coding: utf-8

import pickle
import sqlite3
import numpy as np
import pandas as pd
from time import time

import MeCab
import pyLDAvis
from pyLDAvis import sklearn as sklearn_lda
from sklearn.decomposition import NMF, LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

n_components = 5  # number of topics
n_features = 1000
n_top_words = 20

stop_words = [
    'ai',
    'nec',
    'nec the wise',
    '提供',
    '実現',
    '業務',
    '分析',
    '可能',
    '当社',
    '今後',
    '活用',
    '技術',
    '開発',
    '開始',
    'サービス',
    'システム',
    'データ',
]


def load_dataset():
    print('Loading dataset...', end=' ')
    t0 = time()
    with sqlite3.connect('data/press_release.db') as conn:
        df = pd.read_sql_query('SELECT id, title, content FROM articles', conn)
    print('done in %0.3fs.' % (time() - t0))

    n_samples = len(df)
    data = df['content']

    return n_samples, data


def tokenize(text):

    text = text.lower()

    m = MeCab.Tagger(' -d /home/yan/projects/nikkei_article_bot/nikkei_article_bot/env/lib/mecab-ipadic-neologd/')
    words = m.parse(str(text))

    clean_tokens = []
    for row in words.split('\n'):

        word = row.split('\t')[0]

        if word == 'EOS':
            break
        else:
            if word in stop_words:
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


def vectorize(data, n_features):
    # Use tf-idf features for NMF.
    print('Extracting tf-idf features...', end=' ')
    tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2,
                                    max_features=n_features,
                                    tokenizer=tokenize)
    t0 = time()
    tfidf = tfidf_vectorizer.fit_transform(data)
    print('done in %0.3fs.' % (time() - t0))

    # Use tf (raw term count) features for LDA.
    print('Extracting tf features...', end=' ')
    tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2,
                                    max_features=n_features,
                                    tokenizer=tokenize)
    t0 = time()
    tf = tf_vectorizer.fit_transform(data)
    print('done in %0.3fs.' % (time() - t0))
    return tfidf, tfidf_vectorizer, tf, tf_vectorizer


def n_most_common_words(tf, tf_vectorizer, n=10):
    words = tf_vectorizer.get_feature_names()

    total_counts = np.zeros(len(words))
    for t in tf:
        total_counts+=t.toarray()[0]

    count_dict = (zip(words, total_counts))
    count_dict = sorted(count_dict, key=lambda x:x[1], reverse=True)[0:n]
    print(f'top words: {count_dict}')


def print_top_words(model, feature_names, n_top_words):
    for topic_idx, topic in enumerate(model.components_):
        message = 'Topic #%d: ' % topic_idx
        message += ' '.join([feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]])
        print(message)
    print()


def save_visualization(LDAvis_data):
    filepath = f'data/ldavis_{n_components}.pkl'
    with open(filepath, 'wb') as f:
        pickle.dump(LDAvis_data, f)

    filepath = f'data/ldavis_{n_components}.html'
    pyLDAvis.save_html(LDAvis_data, filepath)


def load_visualization(filepath):
    with open(filepath, 'rb') as f:
        LDAvis_data = pickle.load(f)
    return LDAvis_data


if __name__ == '__main__':

    print()
    n_samples, data = load_dataset()

    # vectorize data
    tfidf, tfidf_vectorizer, tf, tf_vectorizer = vectorize(data, n_features)
    print(f'stop words: {stop_words}')

    # print n most common words
    n_most_common_words(tf, tf_vectorizer, n=10)

    print()

    # Fit the NMF model
    print('Fitting the NMF model (Frobenius norm) with tf-idf features, '
        'n_samples=%d and n_features=%d...' % (n_samples, n_features), end=' ')
    t0 = time()
    nmf = NMF(n_components=n_components, random_state=1,
            alpha=.1, l1_ratio=.5).fit(tfidf)
    print('done in %0.3fs.' % (time() - t0))
    tfidf_feature_names = tfidf_vectorizer.get_feature_names()
    print_top_words(nmf, tfidf_feature_names, n_top_words)

    # Fit the LDA model
    print('Fitting LDA models with tf features, n_samples=%d and n_features=%d...'
        % (n_samples, n_features), end=' ')
    lda = LatentDirichletAllocation(n_components=n_components, max_iter=5,
                                    learning_method='online',
                                    learning_offset=50.,
                                    random_state=0)
    t0 = time()
    lda.fit(tf)
    print('done in %0.3fs.' % (time() - t0))
    tf_feature_names = tf_vectorizer.get_feature_names()
    print_top_words(lda, tf_feature_names, n_top_words)

    # visualization
    LDAvis_data = sklearn_lda.prepare(lda, tf, tf_vectorizer)
    save_visualization(LDAvis_data)
    print('\nVisualization saved')
