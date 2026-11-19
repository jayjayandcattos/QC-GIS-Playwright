"""A results table printed after every run: what each test checked, and whether it passed.

Rows are grouped by area (UI behaviour first, then GitHub issues) and by feature (the file),
so a red row says which part of the console broke. "What it checked" is the test's docstring
when it has one, otherwise its name in plain words, plus the parameter it ran with.
"""

import re

import pytest

AREAS = ["UI", "Issues"]
RESULT = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}
WORD = {"PASS": "passed", "FAIL": "failed", "SKIP": "skipped"}
MAX_CHECK = 64

_rows: list[dict] = []


def where(path: str) -> tuple[str, str]:
    """('UI', 'Map lock') for tests/ui/test_map_lock.py; ('Issues', '#95 remove worship layer') for an issue file."""
    name = re.sub(r"\.py$", "", path.replace("\\", "/").rsplit("/", 1)[-1]).removeprefix("test_")
    issue = re.match(r"issue_(\d+)_(.+)", name)
    if issue:
        return "Issues", f"#{issue[1]} {issue[2].replace('_', ' ')}"
    return "UI", name.replace("_", " ").capitalize()


def what(item: pytest.Item) -> str:
    """The test's docstring, or its name in words, with any parameter other than the browser."""
    doc = (getattr(getattr(item, "function", None), "__doc__", None) or "").strip().splitlines()
    text = doc[0] if doc else item.originalname.removeprefix("test_").replace("_", " ").capitalize()
    params = getattr(item, "callspec", None)
    extra = [str(v) for k, v in (params.params.items() if params else []) if k != "browser_name"]
    return f"{text} ({', '.join(extra)})" if extra else text


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    report = yield
    # One row per test: its call, or its setup when setup failed or skipped it.
    if report.when == "call" or (report.when == "setup" and not report.passed):
        area, feature = where(item.nodeid.split("::")[0])
        _rows.append({"area": area, "feature": feature, "check": what(item),
                      "result": RESULT.get(report.outcome, report.outcome.upper()), "seconds": report.duration})
    return report


def pytest_terminal_summary(terminalreporter):
    if not _rows:
        return

    def order(r: dict) -> tuple:
        number = re.match(r"#(\d+)", r["feature"])  # issues by number: #95 before #100
        return (AREAS.index(r["area"]) if r["area"] in AREAS else len(AREAS), int(number[1]) if number else 0, r["feature"])

    rows = sorted(_rows, key=order)
    for row in rows:
        if len(row["check"]) > MAX_CHECK:
            row["check"] = row["check"][: MAX_CHECK - 1] + "…"
    head = {"area": "Area", "feature": "Feature", "check": "What it checked", "result": "Result", "seconds": "Time"}
    width = {k: max(len(head[k]), *(len(str(r[k])) for r in rows)) for k in ("area", "feature", "check", "result")}

    def cells(r: dict) -> list[str]:
        return [str(r["area"]).ljust(width["area"]), str(r["feature"]).ljust(width["feature"]), str(r["check"]).ljust(width["check"])]

    tr = terminalreporter
    tr.section("What was tested")
    tr.write_line("  ".join(cells(head) + [head["result"].ljust(width["result"]), head["seconds"]]), bold=True)
    tr.write_line("-" * (sum(width.values()) + 2 * 4 + 6))
    last = None
    for r in rows:
        group = (r["area"], r["feature"])
        shown = cells(r) if group != last else ["".ljust(width["area"]), "".ljust(width["feature"]), cells(r)[2]]
        last = group
        tr.write("  ".join(shown) + "  ")
        tr.write(r["result"].ljust(width["result"]), green=r["result"] == "PASS", red=r["result"] == "FAIL", yellow=r["result"] == "SKIP", bold=True)
        tr.write(f"  {r['seconds']:5.1f}s\n")
    counts = {name: sum(r["result"] == name for r in rows) for name in RESULT.values()}
    tr.write_line(f"\n{len(rows)} checks: " + ", ".join(f"{n} {WORD[name]}" for name, n in counts.items() if n), bold=True)
