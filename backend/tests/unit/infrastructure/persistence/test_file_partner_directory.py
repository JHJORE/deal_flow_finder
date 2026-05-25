import json
from pathlib import Path

import pytest

from deal_flow.infrastructure.persistence.file_partner_directory import (
    FilePartnerDirectory,
)

_REAL_DATA_DIR = Path(__file__).resolve().parents[4] / "data"


def test_maps_fixture_to_partner_entities(tmp_path):
    (tmp_path / "a16z_partners.json").write_text(
        json.dumps(
            {
                "partners": [
                    {
                        "name": "Alice",
                        "profile_url": "https://x.com/alice",
                        "linkedin_url": "https://linkedin.com/in/alice",
                        "education": ["Stanford"],
                    },
                    {"name": "Bob", "profile_url": "https://x.com/bob"},
                ]
            }
        )
    )

    partners = FilePartnerDirectory(data_dir=tmp_path).list_partners("a16z.com")

    assert [p.name for p in partners] == ["Alice", "Bob"]
    assert partners[0].linkedin_url == "https://linkedin.com/in/alice"
    assert partners[0].education == ("Stanford",)
    assert partners[1].linkedin_url is None


def test_raises_file_not_found_for_unknown_or_missing_firm(tmp_path):
    dir_ = FilePartnerDirectory(data_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        dir_.list_partners("not-a-firm.com")
    with pytest.raises(FileNotFoundError):
        dir_.list_partners("a16z.com")  # mapped but file absent


@pytest.mark.skipif(not _REAL_DATA_DIR.exists(), reason="real fixtures not present")
def test_real_fixtures_load_for_all_known_firms():
    dir_ = FilePartnerDirectory(data_dir=_REAL_DATA_DIR)
    for domain in ("a16z.com", "sequoiacap.com", "ycombinator.com"):
        partners = dir_.list_partners(domain)
        assert partners and any(p.linkedin_url for p in partners)
