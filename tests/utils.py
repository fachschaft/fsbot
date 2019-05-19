import builtins
import importlib
import random
import string
import unittest.mock as mock
from typing import Any, Callable

_orig_import = builtins.__import__


def _import_mock(modulename: str, mock_module: Any) -> Callable[..., Any]:
    def _tmp(name: str, *args: Any) -> Any:
        if name == modulename:
            return mock_module
        return _orig_import(name, *args)
    return _tmp


def patch_module(reloadmodule: Any, mock_modulename: str, mock_module: Any) -> None:
    with mock.patch('builtins.__import__', side_effect=_import_mock(mock_modulename, mock_module)):
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
