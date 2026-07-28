"""Tests of the boundary checks themselves.

A check that has never been observed to fail is indistinguishable from a check
that cannot fail. These fixtures build small violating module trees on disk and
assert each check reports them — which is also the only way to keep the four
checks honest as the spec grows.
"""
