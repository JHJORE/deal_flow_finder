"""Phase 1: discovery crawl of firm sites."""

from __future__ import annotations

import logging

from pipeline.main import build_container, run_phase_1


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    counts = run_phase_1(build_container())
    print(f"phase 1 complete: {counts}")


if __name__ == "__main__":
    main()
