"""
unified_io.adapters.sql_adapter
================================
SQL read / write adapter backed by pandas + SQLAlchemy.

Requires: ``sqlalchemy>=2.0`` (``pip install isd-py-framework-sdk[unified_io.sql]``).
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from ._interface import IIOAdapter

_MISSING_MSG = (
    "SqlIOAdapter requires SQLAlchemy.  "
    "Install it with:  pip install isd-py-framework-sdk[unified_io.sql]"
)


class SqlIOAdapter(IIOAdapter):
    """
    Read / write SQL tables via ``pandas.read_sql`` / ``DataFrame.to_sql``.

    Parameters
    ----------
    engine
        A SQLAlchemy ``Engine`` (or ``Connection``) object.  May also be
        passed per-call via the ``engine`` keyword argument.
    """

    def __init__(self, engine: Any = None) -> None:
        self._engine = engine

    def _get_engine(self, kwargs: dict) -> Any:
        engine = kwargs.pop("engine", self._engine)
        if engine is None:
            raise ValueError(
                "No SQLAlchemy engine provided.  Pass it to the constructor "
                "or as the 'engine' keyword argument."
            )
        return engine

    def read(self, source: str, **kwargs) -> pd.DataFrame:
        """
        Parameters
        ----------
        source
            SQL query string or table name.
        engine : optional
            Override the adapter-level engine for this call.
        **kwargs
            Forwarded to :func:`pandas.read_sql`.
        """
        try:
            import sqlalchemy  # noqa: F401 (presence check)
        except ImportError:
            raise ImportError(_MISSING_MSG) from None
        engine = self._get_engine(kwargs)
        return pd.read_sql(source, con=engine, **kwargs)

    def write(
        self,
        df: pd.DataFrame,
        destination: str,
        **kwargs,
    ) -> None:
        """
        Parameters
        ----------
        destination
            Target table name.
        engine : optional
            Override the adapter-level engine for this call.
        **kwargs
            Forwarded to :meth:`pandas.DataFrame.to_sql`.
            ``if_exists`` defaults to ``"append"``.
            ``index`` defaults to ``False``.
        """
        try:
            import sqlalchemy  # noqa: F401
        except ImportError:
            raise ImportError(_MISSING_MSG) from None
        engine = self._get_engine(kwargs)
        kwargs.setdefault("if_exists", "append")
        kwargs.setdefault("index", False)
        df.to_sql(destination, con=engine, **kwargs)
