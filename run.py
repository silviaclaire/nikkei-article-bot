import sys

from app import app
from library.bot import run
from library.config import Config

cfg = Config()


def print_help():
    print(
        f'\nUsage:\n\n'
        f'$ python run.py app\n'
        f'$ python run.py bot\n'
    )

if len(sys.argv) != 2:
    print_help()
    exit(-1)

# run app
if sys.argv[1] == 'app':
    app.run(host='0.0.0.0', port=cfg.port, debug=True)

# run bot
elif sys.argv[1] == 'bot':
    for current_progress in run(cfg.csv_filepath):
        pass

else:
    print_help()
    exit(-1)
