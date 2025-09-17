import json
import os

def load_translations(lang='fr'):
    path = f'locales/{lang}.json'
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def t(key, translations):
    return translations.get(key, key)