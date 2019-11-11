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

MECAB_DICTIONARY_PATH = ' -d /home/yan/projects/nikkei_article_bot/nikkei_article_bot/env/lib/mecab-ipadic-neologd/'

class BotStatus:
    IDLE = 'IDLE'
    PROCESSING = 'SCRAWLING'
    COMPLETE = 'COMPLETE'
    ERROR = 'ERROR'

class AnalyzerStatus:
    IDLE = 'IDLE'
    PROCESSING = 'ANALYZING'
    COMPLETE = 'COMPLETE'
    ERROR = 'ERROR'
