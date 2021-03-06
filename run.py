import sys
import os

from app import app
from library.bot import Bot
from library.analyzer import Analyzer
from library.bot_analyzer import BotAnalyzer
from library.config import Config

cfg = Config()

# dataディレクトリを作成する
os.makedirs('./data', exist_ok=True)

def print_help():
    print(
        f'\nUsage:\n\n'
        f'$ python run.py app [PORT]\n'
        f'$ python run.py bot\n'
        f'$ python run.py analyzer\n'
        f'$ python run.py bot_analyzer\n'
    )

if len(sys.argv) < 2:
    print_help()
    exit(-1)

# run app
if sys.argv[1] == 'app':
    try:
        app.run(host='0.0.0.0', port=int(sys.argv[2]), debug=True)
    except (IndexError, ValueError):
        print_help()
        exit(-1)

# run bot
elif sys.argv[1] == 'bot':
    bot = Bot(keyword=cfg.keyword, industry=cfg.industry)
    for progress in bot.run():
        pass

# run analyzer
elif sys.argv[1] == 'analyzer':
    analyzer = Analyzer(sql_query=cfg.sql_query,
                        n_components=cfg.n_components,
                        n_features=cfg.n_features,
                        stop_words=cfg.stop_words,
                        n_top_words=cfg.n_top_words,
                        n_topic_words=cfg.n_topic_words)
    analyzer.run()

# run bot then analyzer
elif sys.argv[1] == 'bot_analyzer':
    bot_analyzer = BotAnalyzer(keyword=cfg.keyword,
                               industry=cfg.industry,
                               sql_query=cfg.sql_query,
                               n_components=cfg.n_components,
                               n_features=cfg.n_features,
                               stop_words=cfg.stop_words,
                               n_top_words=cfg.n_top_words,
                               n_topic_words=cfg.n_topic_words)
    bot_analyzer.run()

else:
    print_help()
    exit(-1)
