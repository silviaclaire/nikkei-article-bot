import sqlite3
import pandas as pd


class DatabaseClient:
    def __init__(self, db_filepath):
        self.db_filepath = db_filepath
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
                       industry TEXT,
                       content TEXT NOT NULL)
                      ''')
            conn.commit()

    def insert_record(self, article):
        with sqlite3.connect(self.db_filepath) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO articles VALUES (NULL,?,?,?,?,?)', tuple(article.values()))
            conn.commit()

    def load_dataset(self, sql_query):
        with sqlite3.connect(self.db_filepath) as conn:
            df = pd.read_sql_query(sql_query, conn)
        return df
