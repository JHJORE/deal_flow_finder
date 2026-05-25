import json
from datetime import date

from deal_flow.domain.entities.form_d_filing import FormDFiling
from deal_flow.domain.entities.partner_form_d_signal import PartnerFormDSignal
from deal_flow.domain.value_objects.date_range import DateRange
from deal_flow.domain.value_objects.form_d_related_person import FormDRelatedPerson
from deal_flow.infrastructure.persistence.file_board_seat_log import FileBoardSeatLog


def _signal(partner: str, accession: str, issuer: str) -> PartnerFormDSignal:
    return PartnerFormDSignal(
        partner_name=partner,
        date_range=DateRange(start=date(2024, 1, 1), end=date(2024, 12, 31)),
        filings=(
            FormDFiling(
                accession_number=accession,
                issuer_name=issuer,
                issuer_cik="0001587468",
                filed_at=date(2024, 6, 1),
                url=f"https://www.sec.gov/x/{accession}",
                total_offering_amount=1_000_000_000,
                total_amount_sold=900_000_000,
                related_persons=(
                    FormDRelatedPerson(
                        first_name="Ben",
                        last_name="Horowitz",
                        relationships=("Director",),
                        relationship_clarification=None,
                    ),
                ),
            ),
        ),
    )


def test_append_creates_file_with_curated_fields(tmp_path):
    path = tmp_path / "board_seats.json"
    log = FileBoardSeatLog(path=path)

    log.append(_signal("Ben Horowitz", "0001587468-24-000001", "Databricks, Inc."))

    rows = json.loads(path.read_text(encoding="utf-8"))
    (row,) = rows
    assert row["partner_name"] == "Ben Horowitz"
    assert row["accession_number"] == "0001587468-24-000001"
    assert row["issuer_name"] == "Databricks, Inc."
    assert row["url"].endswith("0001587468-24-000001")
    assert row["total_offering_amount"] == 1_000_000_000
    assert row["total_amount_sold"] == 900_000_000
    assert row["related_persons"][0]["last_name"] == "Horowitz"


def test_append_dedupes_on_partner_and_accession(tmp_path):
    path = tmp_path / "board_seats.json"
    log = FileBoardSeatLog(path=path)

    log.append(_signal("Ben Horowitz", "0001587468-24-000001", "Databricks, Inc."))
    log.append(_signal("Ben Horowitz", "0001587468-24-000001", "Databricks, Inc."))
    log.append(_signal("Ben Horowitz", "0001587468-24-000002", "Databricks, Inc."))
    log.append(_signal("Marc Andreessen", "0001587468-24-000001", "Databricks, Inc."))

    rows = json.loads(path.read_text(encoding="utf-8"))
    keys = {(r["partner_name"], r["accession_number"]) for r in rows}
    assert keys == {
        ("Ben Horowitz", "0001587468-24-000001"),
        ("Ben Horowitz", "0001587468-24-000002"),
        ("Marc Andreessen", "0001587468-24-000001"),
    }
