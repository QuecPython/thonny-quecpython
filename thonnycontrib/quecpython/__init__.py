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

from thonny import get_workbench
from thonny.plugins.quecpython.backend.mp_front import (
    add_quecpython_backend,
    GenericBareMetalQuecPythonConfigPage,
    GenericBareMetalQuecPythonProxy
)


def create_view():
    from .view import QuecView, open_quecview
    from .locale import tr
    get_workbench().add_view(QuecView, tr("QuecPython Kits"), "s")
    get_workbench().add_command(
        'quecpython_kits',
        'tools',
        tr('QuecPython Kits'),
        open_quecview
    )


def load_plugin():
    add_quecpython_backend(
        "GenericQuecPython",
        GenericBareMetalQuecPythonProxy,
        "QuecPython (generic)",
        GenericBareMetalQuecPythonConfigPage,
        sort_key="51",
    )
    create_view()
