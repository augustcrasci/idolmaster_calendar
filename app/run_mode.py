from __future__ import annotations

import sys

from app.refresh_all import main as refresh_all_main
from app.viewer import main as viewer_main


VALID_MODES = {"update", "viewer", "update_and_viewer"}


def main() -> int:
    mode = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""

    if mode not in VALID_MODES:
        print("Usage: python -m app.run_mode [update|viewer|update_and_viewer]")
        return 1

    if mode == "update":
        refresh_all_main()
        return 0

    if mode == "viewer":
        viewer_main()
        return 0

    refresh_all_main()
    viewer_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
