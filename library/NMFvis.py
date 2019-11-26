import pandas as pd

from sklearn.manifold import TSNE
import plotly.graph_objects as go


def prepare_tsne_groups(nmf_model, tfidf, data_df, topics_dict=None):
    # scale nmf embeddings
    nmf_embedding = nmf_model.transform(tfidf)
    nmf_embedding = (nmf_embedding-nmf_embedding.mean(axis=0)) / nmf_embedding.std(axis=0)

    # fit tsne
    tsne = TSNE(random_state=1)
    tsne_embedding = tsne.fit_transform(nmf_embedding)

    # prepare result
    tsne_embedding = pd.DataFrame(tsne_embedding, columns=['x','y'])
    tsne_embedding['title'] = data_df['title']
    tsne_embedding['link'] = data_df['link']
    tsne_embedding['topic'] = nmf_embedding.argmax(axis=1)
    if topics_dict:
        tsne_embedding['topic'] = tsne_embedding['topic'].replace(topics_dict)
    tsne_groups = tsne_embedding.groupby('topic')

    return tsne_groups


def save_html(groups, filepath):
    layout = go.Layout(
        title='NMF Topic Extraction (2D-embedding with t-SNE)',
        xaxis=dict(title='x'),
        yaxis=dict(title='y'),
        hovermode='closest',
    )
    data = [
        go.Scatter(
            name=idx,
            x=val['x'],
            y=val['y'],
            text=val['title'],
            textposition='top center',
            customdata=val['link'],
            mode='markers',
            marker=dict(
                size=10,
                symbol='circle',
            ),
        ) for idx, val in groups
    ]

    fig = go.Figure(data=data, layout=layout)
    fig.write_html(filepath, auto_open=True)
