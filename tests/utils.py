import builtins
import importlib
import random
import string
import unittest.mock as mock
from typing import Any, Callable, Dict

_orig_import = builtins.__import__


def _import_mock(mock_modules: Dict[str, Any]) -> Callable[..., Any]:
    def _tmp(name: str, *args: Any) -> Any:
        if name in mock_modules:
            return mock_modules[name]
        return _orig_import(name, *args)
    return _tmp


def patch_module(reloadmodule: Any, mock_modules: Dict[str, Any]) -> None:
    with mock.patch('builtins.__import__', side_effect=_import_mock(mock_modules)):
        for mock_modulename, mock_module in mock_modules.items():
            try:
                # Try to load the mock
                module = builtins.__import__(mock_modulename)
                # If it is not the mock it was already loaded so we need a reload
                if mock_module != module:
                    importlib.reload(module)
            except (ImportError, TypeError):
                pass
        # The mock is in place. Reload the module which imports the mock so that the mock is actually used
        importlib.reload(reloadmodule)


def random_string(len_: int) -> str:
    return ''.join(random.choices(string.ascii_letters, k=len_))
