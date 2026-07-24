from __future__ import annotations

from pathlib import Path

from full_loop_runner import build_parser, run_full_loop
from registry_loader import load_registries


def main(argv=None):
    args = build_parser().parse_args(argv)
    source = Path(__file__).resolve().parent
    result = run_full_loop(
        load_registries(source),
        source,
        args.output,
        stage=args.stage,
        review_receipt=args.review_receipt,
    )
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
