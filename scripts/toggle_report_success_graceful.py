import argparse
import sys
from pathlib import Path

REPORT_PATH = Path(__file__).resolve().parent.parent / "src" / "report" / "report.py"

SAFE_CALL = "            self._safe_create_success_issue(firewatch_config, job, rule, date, labels)"
RAW_CALL = "            self._create_success_issue(firewatch_config, job, rule, date, labels)"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "action",
        choices=("strip", "restore"),
        help="strip calls _create_success_issue (raises); restore calls _safe_create_success_issue (catches JIRAError)",
    )
    p.add_argument("--path", type=Path, default=REPORT_PATH)
    args = p.parse_args()
    text = args.path.read_text()
    if args.action == "strip":
        if SAFE_CALL not in text:
            print("already stripped", file=sys.stderr)
            sys.exit(0)
        args.path.write_text(text.replace(SAFE_CALL, RAW_CALL, 1))
    else:
        if SAFE_CALL in text:
            print("already has graceful handler", file=sys.stderr)
            sys.exit(0)
        if RAW_CALL not in text:
            print("expected _create_success_issue call in report_success not found in report.py", file=sys.stderr)
            sys.exit(1)
        args.path.write_text(text.replace(RAW_CALL, SAFE_CALL, 1))


if __name__ == "__main__":
    main()
