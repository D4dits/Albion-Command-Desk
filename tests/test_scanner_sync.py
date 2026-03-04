from __future__ import annotations

from albion_dps.qt.scanner import _parse_rev_list_counts


def test_parse_rev_list_counts_ok() -> None:
    assert _parse_rev_list_counts("3\t7") == (3, 7)
    assert _parse_rev_list_counts("0 0") == (0, 0)


def test_parse_rev_list_counts_invalid() -> None:
    assert _parse_rev_list_counts(None) is None
    assert _parse_rev_list_counts("") is None
    assert _parse_rev_list_counts("bad output") is None
    assert _parse_rev_list_counts("1") is None
