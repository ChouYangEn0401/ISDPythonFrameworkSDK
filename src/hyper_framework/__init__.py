"""
ISD Python Framework — Public API
"""
from ._version import __version__
from .Singleton import SingletonMetaclass

__all__ = [
    "__version__",
    "SingletonMetaclass",
]
