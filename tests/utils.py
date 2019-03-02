import builtins
import contextlib
import unittest.mock as mock
from typing import Any, Callable, Iterator

_orig_import = builtins.__import__


def _import_mock(module: str, mock_module: Any) -> Callable[..., Any]:
    def _tmp(name: str, *args: Any) -> Any:
        if name == module:
            return mock_module
        return _orig_import(name, *args)
    return _tmp


@contextlib.contextmanager
def patch_module(module: str, mock_module: Any) -> Iterator[Any]:
    with mock.patch('builtins.__import__', side_effect=_import_mock(module, mock_module)):
        yield
