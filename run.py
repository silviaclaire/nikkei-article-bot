import sys

from app import app
from library.bot import Bot
from library.analyzer import Analyzer
from library.bot_analyzer import BotAnalyzer
from library.config import Config

cfg = Config()


def print_help():
    print(
        f'\nUsage:\n\n'
        f'$ python run.py app\n'
        f'$ python run.py bot\n'
        f'$ python run.py analyzer\n'
        f'$ python run.py bot_analyzer\n'
    )

if len(sys.argv) != 2:
    print_help()
    exit(-1)

# run app
if sys.argv[1] == 'app':
    app.run(host='0.0.0.0', port=cfg.port, debug=True)

# run bot
elif sys.argv[1] == 'bot':
    bot = Bot(keyword=cfg.keyword, industry=cfg.industry, csv_filepath=cfg.csv_filepath)
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
                               csv_filepath=cfg.csv_filepath,
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
