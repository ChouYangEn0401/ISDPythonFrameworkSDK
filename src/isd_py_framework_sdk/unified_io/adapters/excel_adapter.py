"""
unified_io.adapters.excel_adapter
===================================
Excel read / write adapter backed by pandas + openpyxl.

Requires: ``openpyxl>=3.1``, ``pandas>=2.0``
(``pip install isd-py-framework-sdk[unified_io.excel]``)
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional
import pandas as pd

from ._interface import IIOAdapter

class ExcelIOAdapter(IIOAdapter):
