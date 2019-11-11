import pickle
import sqlite3
import numpy as np
import pandas as pd

import MeCab
from sklearn.decomposition import NMF, LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

n_components = 5  # number of topics
n_features = 1000
n_top_words = 20
n_topic_words = 20

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
    with sqlite3.connect('data/press_release.db') as conn:
        df = pd.read_sql_query('SELECT id, title, content FROM articles', conn)

    n_samples = len(df)
    data = df['content']

    return n_samples, data


def tokenize(text):
    text = str(text).lower()

    m = MeCab.Tagger(' -d /home/yan/projects/nikkei_article_bot/nikkei_article_bot/env/lib/mecab-ipadic-neologd/')
    words = m.parse(text)

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
    tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2,
                                       max_features=n_features,
                                       tokenizer=tokenize)
    tfidf = tfidf_vectorizer.fit_transform(data)

    # Use tf (raw term count) features for LDA.
    tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2,
                                    max_features=n_features,
                                    tokenizer=tokenize)
    tf = tf_vectorizer.fit_transform(data)
    return tfidf, tfidf_vectorizer, tf, tf_vectorizer


def get_top_words(tf, tf_vectorizer, n_top_words):
    words = tf_vectorizer.get_feature_names()
    total_counts = np.zeros(len(words))
    for t in tf:
        total_counts+=t.toarray()[0]
    top_words = sorted((zip(words, total_counts)), key=lambda x:x[1], reverse=True)[0:n_top_words]
    return top_words


def get_topic_words(model, feature_names, n_topic_words):
    df = pd.DataFrame(columns=['topic_words'])
    for idx, topic in enumerate(model.components_):
        topic_words = ';'.join([feature_names[i] for i in topic.argsort()[:-n_topic_words-1:-1]])
        df.loc[idx] = topic_words
    return df


def save_as_pickle(model, filepath):
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)


def load_pickle(filepath):
    with open(filepath, 'rb') as f:
        model = pickle.load(f)
    return model


def run():
    # load dataset
    n_samples, data = load_dataset()

    # vectorize data
    tfidf, tfidf_vectorizer, tf, tf_vectorizer = vectorize(data, n_features)

    # get top words overall
    top_words = get_top_words(tf, tf_vectorizer, n_top_words)

    # Fit the NMF model
    nmf = NMF(n_components=n_components,
              random_state=1,
              alpha=.1,
              l1_ratio=.5)
    nmf.fit(tfidf)
    # save
    save_as_pickle(tfidf_vectorizer, 'data/nmf_tfidf_vectorizer.pkl')
    save_as_pickle(nmf, 'data/nmf_model.pkl')
    # load
    tfidf_vectorizer = load_pickle('data/nmf_tfidf_vectorizer.pkl')
    nmf = load_pickle('data/nmf_model.pkl')
    # get top words per topic
    tfidf_feature_names = tfidf_vectorizer.get_feature_names()
    nmf_topic_words = get_topic_words(nmf, tfidf_feature_names, n_topic_words)

    # Fit the LDA model
    lda = LatentDirichletAllocation(n_components=n_components,
                                    max_iter=5,
                                    learning_method='online',
                                    learning_offset=50.,
                                    random_state=0)
    lda.fit(tf)
    # save
    save_as_pickle(tf_vectorizer, 'data/lda_tf_vectorizer.pkl')
    save_as_pickle(lda, 'data/lda_model.pkl')
    # load
    tf_vectorizer = load_pickle('data/lda_tf_vectorizer.pkl')
    lda = load_pickle('data/lda_model.pkl')
    # get top words per topic
    tf_feature_names = tf_vectorizer.get_feature_names()
    lda_topic_words = get_topic_words(lda, tf_feature_names, n_topic_words)

    return top_words, nmf_topic_words, lda_topic_words
