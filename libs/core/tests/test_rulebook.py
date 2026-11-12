"""Rulebook finder: link parsing and the download safety checks. No network
(localhost and private IPs are refused before any request)."""

import asyncio
import os

import pytest

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")

from games_rule_core.ai.rulebook import (  # noqa: E402
    UnsafeUrl,
    download_pdf,
    extract_urls,
    public_address,
)


def test_extract_urls() -> None:
    text = (
        "1. https://example.com/rules.pdf.\n"
        "- <https://cdn.example.org/a%20b/rulebook.pdf>\n"
        "https://boardgamegeek.com/filepage/1/rules.pdf\n"
        "https://example.com/rules.pdf"
    )
    assert extract_urls(text) == [
        "https://example.com/rules.pdf",
        "https://cdn.example.org/a%20b/rulebook.pdf",
    ]
    assert extract_urls("NONE") == []


def test_public_address() -> None:
    assert public_address("8.8.8.8")
    assert public_address("2606:4700::1111")
    for addr in (
        "127.0.0.1",
        "192.168.0.200",
        "10.0.0.1",
        "100.101.1.1",
        "169.254.169.254",
        "::1",
        "fe80::1%en0",
    ):
        assert not public_address(addr), addr


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/r.pdf",
        "https://localhost/r.pdf",
        "https://127.0.0.1/r.pdf",
        "https://192.168.0.200:8720/r.pdf",
    ],
)
def test_download_refuses_unsafe_urls(url: str) -> None:
    with pytest.raises(UnsafeUrl):
        asyncio.run(download_pdf(url))
