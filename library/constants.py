INDUSTRY_OPTIONS = {
    0: 'すべて',
    1: '情報・通信',
    2: 'メディア',
    3: '電機',
    4: '金融・保険',
    5: '自動車',
    6: '輸送・レジャー',
    7: '食品',
    8: '流通・外食',
    9: '日用品',
    10: '医薬・医療',
    11: '建設・不動産',
    12: '機械',
    13: '素材・エネルギー',
    14: '商社・サービス',
}


INPUT_VAL_DESCRIPTION = {
    'keyword':'検索ワードを指定',
    'industry':'絞り込みたい産業を指定',
    'sql_query':'分析対象にする記事を指定',
    'stop_words':'分析の対象外とする語を指定',
    'n_components':'いくつのトピックに分けるか指定',
    'n_features':'出現頻度上位何語で分析するか指定',
    'n_top_words':'出現頻度上位何語を表示するか指定',
    'n_topic_words':'トピックごとの単語を何個表示するか指定',
}


class BotAnalyzerStatus:
    IDLE = 'IDLE'
    INITIALIZING = 'INITIALIZING'
    CRAWLING = 'CRAWLING'
    ANALYZING = 'ANALYZING'
    PROCESSING = [INITIALIZING, CRAWLING, ANALYZING]
    COMPLETE = 'COMPLETE'
    ERROR = 'ERROR'
