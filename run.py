import sys

from app import app
from library.bot import Bot
from library.config import Config

cfg = Config()


def print_help():
    print(
        f'\nUsage:\n\n'
        f'$ python run.py app\n'
        f'$ python run.py bot_file\n'
        f'$ python run.py bot_keyword\n'
    )

if len(sys.argv) != 2:
    print_help()
    exit(-1)

# run app
if sys.argv[1] == 'app':
    app.run(host='0.0.0.0', port=cfg.port, debug=True)

# run bot from file
elif sys.argv[1] == 'bot_file':
    bot_thread = Bot(keyword=None, industry=None, csv_filepath=cfg.csv_filepath)
    bot_thread.run()

# run bot from keyword
elif sys.argv[1] == 'bot_keyword':
    bot_thread = Bot(keyword=cfg.keyword, industry=cfg.industry, csv_filepath=None)
    bot_thread.run()

else:
    print_help()
    exit(-1)