from app import app

import os
import traceback
from flask import Flask, render_template, make_response, flash, request, redirect, url_for, Response

from library.constants import *
from library.config import Config
from library.db import DatabaseClient
from library.bot_analyzer import BotAnalyzer


# read config
cfg = Config()

# glocal control thread for bot
bot_analyzer = None


params = {
    'keyword': None,
    'industry': None,
    'sql_query': None,
    'n_components': None,
    'n_features': None,
    'stop_words': None,
    'n_top_words': None,
    'n_topic_words': None,
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings')
def settings():
    global params
    for name in params.keys():
        params[name] = getattr(cfg, name)
    return render_template('settings.html',
                           industry_options=INDUSTRY_OPTIONS,
                           default_values=params,
                           input_val_description=INPUT_VAL_DESCRIPTION)

@app.route('/run', methods=['POST'])
def run():
    global params
    global bot_analyzer

    # get params in string format
    for name in params.keys():
        params[name] = request.form.get(name, type=str)

    # if still processing
    if (bot_analyzer) and (bot_analyzer.status in BotAnalyzerStatus.PROCESSING):
        return render_template('error.html', error=bot_analyzer.status), 400

    # initialize and run bot_analyzer
    try:
        bot_analyzer = BotAnalyzer(**params)
    except Exception as err:
        flash(err, category='warning')
        return make_response(render_template('settings.html',
                                             industry_options=INDUSTRY_OPTIONS,
                                             default_values=params,
                                             input_val_description=INPUT_VAL_DESCRIPTION,
                                            ), 400)
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
    filename = request.args.get('filename')
    filepath = os.path.join('data', filename)
    with open(filepath, 'rb') as f:
        csv_data = f.read()
    return Response(csv_data, mimetype='text/csv',
                    headers={'Content-disposition':f'attachment;filename={filename}'})

@app.route('/database_table')
def database_table():
    sql_query = request.args.get('sql_query', default=cfg.sql_query, type=str)
    db_table = DatabaseClient(cfg.db_filepath)\
               .load_dataset(sql_query)\
               .drop(columns=['content'])\
               .to_dict(orient='split')
    return render_template('database_table.html',
                           sql_query=sql_query,
                           db_table=db_table)
