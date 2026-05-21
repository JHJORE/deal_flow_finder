"""Phase 2: SEC EDGAR Form D query + portfolio reconciliation."""

from __future__ import annotations

import logging

from pipeline.main import build_container, run_phase_2


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    counts = run_phase_2(build_container())
    print(f"phase 2 complete: {counts}")


if __name__ == "__main__":
    main()
