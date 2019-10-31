import os
import sqlite3


class DatabaseClient:
    def __init__(self, db_filepath):
        self.db_filepath = db_filepath
        # remove old db file if exists
        if os.path.exists(self.db_filepath):
            os.remove(self.db_filepath)
        # create articles table
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_filepath) as conn:
            c = conn.cursor()
            c.execute('''
                      CREATE TABLE IF NOT EXISTS articles
                      (id INTEGER PRIMARY KEY,
                       title TEXT NOT NULL,
                       link TEXT NOT NULL,
                       date TEXT,
                       company TEXT,
                       industry TEXT,
                       content TEXT NOT NULL)
                      ''')
            conn.commit()

    def insert_record(self, article):
        with sqlite3.connect(self.db_filepath) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO articles VALUES (NULL,?,?,?,?,?,?)', tuple(article.values()))
            conn.commit()
