from app import app

import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, make_response, flash, request, redirect, url_for

from library.bot import Bot
from library.constants import *


UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']

# glocal control thread for bot
bot_thread = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if request has the file part
        if 'file' not in request.files:
            flash('No file part in request', category='warning')
            return make_response(render_template('upload.html'), 400)

        # check if file selected
        f = request.files['file']
        if not f or f.filename == '':
            flash('No selected file', category='warning')
            return make_response(render_template('upload.html'), 400)

        # check file type
        if f.filename.split('.')[-1].lower() != 'csv':
            flash(f'Must be a csv file ({f.filename})', category='warning')
            return make_response(render_template('upload.html'), 400)

        # save file
        filename = secure_filename(f.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        f.save(filepath)
        flash(f'Uploaded ({filename})', category='success')

        return render_template('upload.html', filename=filename)

    else:
        return render_template('upload.html')


@app.route('/run', methods=['POST'])
def run():
    keyword = request.args.get('keyword')
    industry = request.args.get('industry')
    filename = request.args.get('filename')

    if not (filename or all([keyword, industry])):
        return render_template('error.html', error=f'Not enough args ({list(request.args)})')

    global bot_thread

    # if still processing
    if bot_thread and bot_thread.status == BotStatus.PROCESSING:
        return render_template('error.html', error=f'Still processing')

    if filename:
        # run urls in file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        bot_thread = Bot(keyword=None, industry=None, csv_filepath=filepath)
    else:
        # run urls via search
        bot_thread = Bot(keyword=keyword, industry=industry, csv_filepath=None)

    bot_thread.setDaemon(True)
    bot_thread.start()

    return redirect(url_for('result'))


@app.route('/stop')
def stop():
    if bot_thread:
        bot_thread.stop()
    return redirect(url_for('result', result=None))


@app.route('/status')
def status():
    if bot_thread:
        return make_response({'status': bot_thread.status, 'progress': bot_thread.progress})
    return redirect(url_for('result', result=None))


@app.route('/result')
def result():
    if bot_thread is None or bot_thread.status == BotStatus.IDLE:
        return render_template('result.html', result=None)
    elif bot_thread.status == BotStatus.PROCESSING:
        return render_template('processing.html')
    elif bot_thread.status == BotStatus.COMPLETE:
        return render_template('result.html', result=bot_thread.result)
    else:
        return render_template('error.html', error=bot_thread.error)
