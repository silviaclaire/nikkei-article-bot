from library.bot import run
from library.config import Config

cfg = Config()

run(cfg.csv_filepath)
