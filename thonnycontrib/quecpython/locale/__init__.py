import json
from pathlib import Path
from thonny import get_workbench


LANGUAGE_NAME = get_workbench().get_option("general.language")
TRANSLATION_MAP = {}


def init_translation_map():
    global TRANSLATION_MAP
    language_file_path = Path(__file__).parent / (LANGUAGE_NAME + '.lag')
    if language_file_path.exists():
        with open(str(language_file_path), 'r', encoding='utf8') as f:
            TRANSLATION_MAP = json.load(f)


# load translation file to a dict
init_translation_map()


def tr(stringvar):
    temp = None
    if LANGUAGE_NAME == 'zh_CN':
        temp = TRANSLATION_MAP.get(stringvar, None)
    temp = temp or stringvar
    return temp
