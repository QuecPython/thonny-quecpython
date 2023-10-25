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
