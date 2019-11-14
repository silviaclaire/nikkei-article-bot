from app import app

import os
import traceback
from flask import Flask, render_template, make_response, flash, request, redirect, url_for, send_file

from library.constants import *
from library.config import Config
from library.bot_analyzer import BotAnalyzer


# read config
cfg = Config()

# glocal control thread for bot
bot_analyzer = None


DEFAULT_VALUES = {
    'sql_query': cfg.sql_query,
    'n_components': cfg.n_components,
    'n_features': cfg.n_features,
    'stop_words': cfg.stop_words,
    'n_top_words': cfg.n_top_words,
    'n_topic_words': cfg.n_topic_words,
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings')
def settings():
    return render_template('settings.html',
                           industry_options=INDUSTRY_OPTIONS,
                           default_values=DEFAULT_VALUES)

@app.route('/run', methods=['POST'])
def run():
    try:
        keyword = request.form.get('keyword', default=cfg.keyword, type=str)
        industry = request.form.get('industry', default=cfg.industry, type=int)
        csv_filepath = None
        sql_query = request.form.get('sql_query', default=cfg.sql_query, type=str)
        n_components = request.form.get('n_components', default=cfg.n_components, type=int)
        n_features = request.form.get('n_features', default=cfg.n_features, type=int)
        stop_words = request.form.get('stop_words', default=cfg.stop_words, type=str)
        if type(stop_words) is str:
            stop_words = stop_words.split(',')
        n_top_words = request.form.get('n_top_words', default=cfg.n_top_words, type=int)
        n_topic_words = request.form.get('n_topic_words', default=cfg.n_topic_words, type=int)
        if n_components < 0:
            raise ValueError('less than zero')
    except Exception as err:
        flash(err, category='warning')
        return make_response(render_template('settings.html', industry_options=INDUSTRY_OPTIONS, default_values=DEFAULT_VALUES), 400)

    global bot_analyzer

    # if still processing
    if (bot_analyzer) and (bot_analyzer.status in BotAnalyzerStatus.PROCESSING):
        return render_template('error.html', error=bot_analyzer.status), 400

    # initialize and run bot_analyzer
    bot_analyzer = BotAnalyzer(keyword=keyword,
                               industry=industry,
                               csv_filepath=csv_filepath,
                               sql_query=sql_query,
                               n_components=n_components,
                               n_features=n_features,
                               stop_words=stop_words,
                               n_top_words=n_top_words,
                               n_topic_words=n_topic_words,
                               )
    bot_analyzer.setDaemon(True)
    bot_analyzer.start()

    return render_template('processing.html')


@app.route('/stop')
def stop():
    if bot_analyzer:
        bot_analyzer.stop()
    return redirect(url_for('result', result=None))


@app.route('/status')
def status():
    if bot_analyzer:
        return make_response({'status': bot_analyzer.status, 'progress': bot_analyzer.progress})
    return redirect(url_for('result', result=None))


@app.route('/result')
def result():
    if bot_analyzer is None or bot_analyzer.status == BotAnalyzerStatus.IDLE:
        return render_template('result.html', result=None)
    elif bot_analyzer.status in BotAnalyzerStatus.PROCESSING:
        return render_template('processing.html')
    elif bot_analyzer.status == BotAnalyzerStatus.COMPLETE:
        return render_template('result.html', result=bot_analyzer.result)
    elif bot_analyzer.status == BotAnalyzerStatus.ERROR:
        return render_template('error.html', error=bot_analyzer.error, traceback=bot_analyzer.traceback), 500
    else:
        return make_response(f'Unhandled status ({bot_analyzer.status})', 500)

@app.route('/download')
def download():
    data_type = request.args.get('data')

    if data_type == 'result':
        filepath = '../data/result.csv'
    else:
        return make_response(f'Bad request ({data_type})', 400)

    return send_file(filepath, mimetype='text/csv')
