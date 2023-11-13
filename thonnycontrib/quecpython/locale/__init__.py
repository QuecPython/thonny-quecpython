# Copyright (c) Quectel Wireless Solution, Co., Ltd.All Rights Reserved.
#  
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  
#     http://www.apache.org/licenses/LICENSE-2.0
#  
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
