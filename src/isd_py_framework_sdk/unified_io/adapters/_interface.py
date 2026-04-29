from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
import pandas as pd

class IReader(ABC):
    """Anything that can produce a DataFrame from a source."""

    @abstractmethod
    def read(self, source: str | Path | Any, **kwargs) -> pd.DataFrame:
        """
        Load data and return it as a :class:`pandas.DataFrame`.

        Parameters
        ----------
        source
            File path, SQL query string, URL, or any adapter-specific
            source identifier.
        """
        ...

class IWriter(ABC):
    """Anything that can persist a DataFrame to a destination."""

    @abstractmethod
    def write(self, df: pd.DataFrame, destination: str | Path | Any, **kwargs) -> None:
        """
        Persist *df* to *destination*.

        Parameters
        ----------
        df
            Data to write.
        destination
            File path, table name, URL, or any adapter-specific target.
        """
        ...

class IIOAdapter(IReader, IWriter, ABC):
    """Combined read + write adapter interface."""
