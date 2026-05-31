"""Unit tests for the terminal-listing ``removal_reason`` classifier.

These exercise the pure ``classify_removal_reason`` function (no browser /
network), locking the contract consumed by the brickshop-manager sourcing
pipeline: only ``'platform_deleted'`` routes a lead to fraud-dismiss; every
other value (and absent) keeps it on the archive path.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from libs.websites.kleinanzeigen import classify_removal_reason  # noqa: E402

SENTINEL = "[ERROR] Ad ID not found"


@pytest.mark.parametrize(
    "status, ad_id, banner, expected",
    [
        # Sentinel id → platform_deleted regardless of the (defaulted) status.
        ("active", SENTINEL, "", "platform_deleted"),
        ("deleted", SENTINEL, "", "platform_deleted"),
        # Explicit platform-removal banners on a resolving page.
        (
            "deleted",
            "123",
            "Diese Anzeige wurde von eBay Kleinanzeigen entfernt",
            "platform_deleted",
        ),
        (
            "deleted",
            "123",
            "Die Anzeige verstößt gegen unsere Nutzungsbedingungen",
            "platform_deleted",
        ),
        # Sold.
        ("sold", "123", "", "sold"),
        ("active", "123", "Diese Anzeige wurde verkauft", "sold"),
        # Seller-driven deletion.
        ("deleted", "123", "", "seller_deleted"),
        ("active", "123", "Diese Anzeige wurde gelöscht", "seller_deleted"),
        # Terminal but unreadable reason.
        ("active", "123", "Diese Anzeige ist nicht mehr verfügbar", "unknown"),
        # Active / reserved listings carry no removal reason.
        ("active", "123", "", None),
        ("reserved", "123", "", None),
        (None, None, "", None),
    ],
)
def test_classify_removal_reason(status, ad_id, banner, expected):
    assert classify_removal_reason(status, ad_id, banner) == expected


def test_platform_signal_takes_precedence_over_sold():
    # A sold page that also shows a policy-removal banner is platform_deleted.
    assert (
        classify_removal_reason(
            "sold", "123", "Diese Anzeige wurde von Kleinanzeigen entfernt"
        )
        == "platform_deleted"
    )


def test_case_insensitive_banner_match():
    # Real banners are sentence-cased ("Verstößt …"); the matcher lowercases.
    assert (
        classify_removal_reason("deleted", "123", "Verstößt gegen unsere Regeln")
        == "platform_deleted"
    )
