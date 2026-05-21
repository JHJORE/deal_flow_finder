"""Phase 3: per-entity data collection (X, LinkedIn, blogs)."""

from __future__ import annotations

import logging

from pipeline.main import build_container, run_phase_3


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    counts = run_phase_3(build_container())
    print(f"phase 3 complete: {counts}")


if __name__ == "__main__":
    main()
