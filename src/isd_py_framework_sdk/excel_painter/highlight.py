"""
excel_painter.highlight
=======================
Build colour-highlighted :class:`~openpyxl.cell.rich_text.CellRichText` values
that mark which parts of a string match another string.

Two diff strategies (consolidated from the project painters):

* **LCS** (longest common subsequence) — order-aware; highlights the longest
  in-order overlap, per character or per word.
* **Common words** (Jaccard-style set intersection) — order-agnostic;
  highlights any word that also appears in the comparison string.

These functions are pure — they return a ``CellRichText`` you can assign to
``cell.value`` (or hand to :meth:`ExcelPainter.highlight_*`).  Nothing here
touches a workbook.
"""
from __future__ import annotations

import re
from typing import Iterable, Literal

from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont

HighlightMode = Literal["letter", "word"]

_TOKEN_RE = re.compile(r"\b[\w&]+\b")


# ── Diff primitives ─────────────────────────────────────────────────────────

def char_lcs(s1: str, s2: str) -> str:
    """Longest common subsequence of two strings, character-wise."""
    m, n = len(s1), len(s2)
    dp = [["" for _ in range(n + 1)] for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if s1[i] == s2[j]:
                dp[i + 1][j + 1] = dp[i][j] + s1[i]
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j], key=len)
    return dp[m][n]


def word_lcs(s1: str, s2: str, *, case_sensitive: bool = False) -> list[str]:
    """Longest common subsequence of two strings, word (token) wise."""
    def tokens(text: str) -> list[str]:
        return _TOKEN_RE.findall(text if case_sensitive else text.upper())

    a, b = tokens(s1), tokens(s2)
    n, m = len(a), len(b)
    dp = [[""] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            if a[i] == b[j]:
                dp[i + 1][j + 1] = dp[i][j] + " " + a[i]
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j], key=len)
    return dp[n][m].strip().split()


def common_words(s1: str, s2: str, *, case_sensitive: bool = False) -> set[str]:
    """Words appearing in *both* strings (set intersection)."""
    if not case_sensitive:
        s1, s2 = s1.lower(), s2.lower()
    return set(s1.split()) & set(s2.split())


# ── Rich-text builders ──────────────────────────────────────────────────────

def _runs_by_word(
    text: str, highlight: set[str], highlight_color: str, default_color: str
) -> list[TextBlock]:
    out: list[TextBlock] = []
    for word in text.split(" "):
        color = highlight_color if word in highlight else default_color
        out.append(TextBlock(InlineFont(color=color), word + " "))
    return out


def lcs_rich_text(
    text: str,
    compare_to: str,
    *,
    mode: HighlightMode = "word",
    highlight_color: str = "00AA00",
    default_color: str = "000000",
    case_sensitive: bool = False,
) -> CellRichText:
    """Highlight the LCS of *text* vs *compare_to* inside *text*.

    ``mode="word"`` highlights whole matching words (order-aware); ``"letter"``
    highlights the matching character subsequence.
    """
    blocks: list[TextBlock] = []

    if mode == "letter":
        remaining = list(char_lcs(text, compare_to))
        for ch in text:
            if remaining and ch == remaining[0]:
                blocks.append(TextBlock(InlineFont(color=highlight_color, b=True), ch))
                remaining.pop(0)
            else:
                blocks.append(TextBlock(InlineFont(color=default_color, i=True), ch))
    elif mode == "word":
        hl = set(word_lcs(text, compare_to, case_sensitive=case_sensitive))
        if not case_sensitive:
            # word_lcs upper-cases tokens; compare case-insensitively
            blocks = []
            for word in text.split(" "):
                color = highlight_color if word.upper() in hl else default_color
                blocks.append(TextBlock(InlineFont(color=color), word + " "))
        else:
            blocks = _runs_by_word(text, hl, highlight_color, default_color)
    else:
        raise ValueError(f"Unknown mode {mode!r}; use 'word' or 'letter'.")

    return CellRichText(blocks)


def common_words_rich_text(
    text: str,
    compare_to: str,
    *,
    highlight_color: str = "00AA00",
    default_color: str = "000000",
    case_sensitive: bool = False,
) -> CellRichText:
    """Highlight every word of *text* that also appears in *compare_to*."""
    shared = common_words(text, compare_to, case_sensitive=case_sensitive)
    if not case_sensitive:
        blocks = []
        for word in text.split(" "):
            color = highlight_color if word.lower() in shared else default_color
            blocks.append(TextBlock(InlineFont(color=color), word + " "))
        return CellRichText(blocks)
    return CellRichText(_runs_by_word(text, shared, highlight_color, default_color))


def words_rich_text(
    text: str,
    highlight_words: Iterable[str],
    *,
    highlight_color: str = "00AA00",
    default_color: str = "000000",
    case_sensitive: bool = False,
) -> CellRichText:
    """Highlight an explicit set of *highlight_words* within *text*."""
    hl = set(highlight_words if case_sensitive else (w.lower() for w in highlight_words))
    blocks = []
    for word in text.split(" "):
        probe = word if case_sensitive else word.lower()
        color = highlight_color if probe in hl else default_color
        blocks.append(TextBlock(InlineFont(color=color), word + " "))
    return CellRichText(blocks)
