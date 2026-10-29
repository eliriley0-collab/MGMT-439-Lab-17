"""Live integration checks; expectations are separate from app data."""
from datetime import date
from pathlib import Path
from streamlit.testing.v1 import AppTest
import pandas as pd
from asof_app import download_today, download_asof, compare


def main():
    lines = [f"Downloaded / verified: {date.today()}"]
    passed = True
    expected = {
        "BAA": ("2026-09-01", 6.47),
        "FEDFUNDS": ("2026-09-01", 3.75),
        "DGS10": ("2026-10-02", 5.28),
        "MORTGAGE30US": ("2026-10-01", 7.28),
    }
    for sid, (last, value) in expected.items():
        try:
            historical = download_asof(sid, date(2026, 10, 5), date.today())
            current = download_today(sid, date.today())
            result = compare(current, historical)
            ok = result["Last measured date known then"] == pd.Timestamp(last) and result["Value known then"] == value
            passed &= ok
            lines.append(f"{'PASS' if ok else 'FAIL'} {sid}: {result}")
        except Exception as error:
            passed = False
            lines.append(f"ERROR {sid}: {error}")
    try:
        historical = download_asof("PAYEMS", date(2025, 1, 15), date.today())
        current = download_today("PAYEMS", date.today())
        result = compare(current, historical)
        old, new = historical.loc["2024-12-01"], current.loc["2024-12-01"]
        ok = old == 159536 and new < old and result["Revised shared observations"] > 10
        passed &= ok
        lines.append(f"{'PASS' if ok else 'FAIL'} PAYEMS December 2024 then={old}, today={new}; {result}")
    except Exception as error:
        passed = False
        lines.append(f"ERROR PAYEMS: {error}")
    app = AppTest.from_file(str(Path(__file__).with_name("asof_app.py"))).run(timeout=180)
    ok = not app.exception and not app.error and len(app.dataframe) >= 5
    passed &= ok
    lines.append(f"{'PASS' if ok else 'FAIL'} Streamlit render: exceptions={list(app.exception)}, errors={list(app.error)}, tables={len(app.dataframe)}")
    lines.append(f"Overall: {'PASS' if passed else 'FAIL — investigate; do not claim the known answer reproduced'}")
    report = "\n".join(lines) + "\n"
    Path(__file__).with_name("verification.txt").write_text(report)
    print(report)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
