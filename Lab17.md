# Lab 17 — Point-in-Time Audit

Was each number in your series knowable on the day you would have traded on it — and may Project 2 use it?

## Run

From the course workspace:

```sh
Lab15/.venv/bin/python -m streamlit run Lab17/asof_app.py
```

For a new environment, install `Lab17/requirements.txt` first.

## Method

Today's data comes from FRED's public CSV; historical data comes from ALFRED's CSV with an explicit `vintage_date`. Each series uses one request per endpoint on a cache miss. Requests are cached for one hour and keyed by download day. A missing `.` is not filled. Revisions compare nonmissing observations on identical measured dates, across the full downloaded history, with absolute tolerance 1e-9. Later observations count nonmissing current values after the historical last measured date. If no historical observations exist, all current observations count as later. A failed vintage request never falls back to current data.

The chart start date controls only the chart. The expandable comparison includes historical and current values on the same dates and can be downloaded. An observation's date labels its measurement period; it does not establish publication time. A daily ALFRED vintage cannot prove that a value was available before a particular trade within that day. Check release times or use a conservative earlier vintage for trading rules.

Sources: [FRED](https://fred.stlouisfed.org/), [ALFRED help](https://alfred.stlouisfed.org/help). ALFRED describes vintage data as values reported on historical dates; additions generally follow source releases within one business day.

## Validation evidence

See `verification.txt` for executed live checks. Expected answers belong in the verification script, never in app results.

## Your series data card — DGS10 (selected during Lab 17)

- Series ID and source link: [DGS10 — 10-year Treasury constant maturity yield](https://fred.stlouisfed.org/series/DGS10). Selected during this lab, not claimed as completed prework.
- Measure: market yield on U.S. Treasury securities at 10-year constant maturity, quoted on an investment basis. Source: Board of Governors of the Federal Reserve System, H.15 Selected Interest Rates.
- Units, seasonal adjustment, frequency: percent per annum; not seasonally adjusted; daily. A value of 5.28 means 5.28%, not 528% or a bond total return.
- Publication lag and supporting release evidence: short business-day lag. The [H.15 release](https://www.federalreserve.gov/releases/h15/) is posted on business days at 4:15 p.m.; its October 29, 2026 release lists observations through October 28. The FRED page shows the October 28 observation updated October 29 at 3:16 p.m. CDT. Do not assume the observation date is the availability date, or that it was available before market close.
- Revision behavior, tested vintage, and revised count: comparison downloaded October 29 against the October 5, 2026 vintage found **0 revised shared observations** across downloaded history. That is evidence for this comparison, not a guarantee that corrections never occur. The last known observation on October 5 was October 2, **5.28%**.
- Download date: **2026-10-29**; see `verification.txt`. That CSV snapshot ended October 27 at 4.99%; the FRED page checked later showed October 28 at 5.05%. Intraday updates and caching can explain different latest observations; refresh before recording final evidence.
- Last day of last month vs today: live app-function comparison downloaded 2026-10-29:

| As known on | Last measured date known | Value known | Later observations in current data | Revised shared observations |
|---|---|---:|---:|---:|
| 2026-09-30 | 2026-09-29 | 5.26% | 20 | 0 |
| 2026-10-29 | 2026-10-28 | 5.05% | 0 | 0 |

The 20 later observations were not available in the September 30 vintage. Zero revisions means the shared nonmissing values did not change in this comparison. The September 30 measured value of 5.29% is present in today's history but was not yet in the September 30 vintage, illustrating why measurement dates alone do not establish availability.

Latest-value update: the student reports today's displayed DGS10 value is **5.05%**, also confirmed by the fresh app-function download. The FRED page checked on 2026-10-29 labels this observation **2026-10-28**; October 29 is the viewing date, not the measured date.

Three selected values were checked with AI assistance, and the student subsequently confirmed that the FRED-page values match:

| Measured date | App value | FRED page value | Match / explanation |
|---|---|---|---|
| 2026-09-10 | 4.95% | 4.95% | Match — student confirmed |
| 2026-09-21 | 4.96% | 4.96% | Match — student confirmed |
| 2026-09-30 | 5.29% | 5.29% | Match — student confirmed |

FRED values above were retrieved with AI assistance from the [current DGS10 CSV](https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10) on 2026-10-29. A fresh request through the app's `read_csv` function reproduced all three values exactly. The student subsequently reported that all three values match the FRED page. This documents the student's confirmation separately from the automated parsing check.

## Fresh eyes — complete with your partner

Partner: **Max Puntill** (reported by the student). The student reports partner activity completed; the chosen least-trusted field is **revisions**.

Chosen challenge: **revisions**.

Answer accepted by the student: The app found zero revised shared DGS10 observations when comparing the October 5, 2026 vintage with the October 29 download. This supports low revision risk in that comparison, but it does not prove DGS10 can never be corrected, so Project 2 should still use historical vintages.

Partner's code question (reported by the student): **Why do we use ALFRED instead of filtering today's FRED data by date?**

AI-assisted explanation: Filtering today's FRED data only removes later measurement dates; it keeps revisions and values published after the historical trading decision. ALFRED's `vintage_date` requests what was available on the historical date: for example, the September 30 vintage ended with September 29 at 5.26%, even though today's data contains a September 30 observation of 5.29%.

The student reports the partner activity completed. The explanation above was documented with AI assistance; the student's exact unaided answer and line-by-line explanation are not transcribed here.

## Your call

**Admit — student-selected decision.** The tested DGS10 comparison showed zero revised shared observations, supporting use with a historical-availability rule. Use only the DGS10 ALFRED vintage from the calendar day before each trading decision, taking the latest nonmissing observation available in that vintage and retaining its measured date. Never use the same day's eventual vintage for a morning trade. Quarantine any decision with an unavailable vintage, or if release-timing checks show the chosen value was not available before trading; reconsider admission if material corrections or archive gaps appear.

## Learn and reflect — complete personally

1. What is a data card? A data card summarizes a dataset, including where it came from, what it contains, and any limitations.
2. Which fields stop a leak before it starts? Publication dates, timestamps, and data availability dates help prevent using information that wasn't available at the time.
3. Why is “cleaned the data” insufficient? It doesn't explain what was changed, why it was changed, or how those changes could affect the results.
4. How late is your series published, and what does the vintage show? The publication lag depends on the series. The vintage shows what data was actually available at a specific point in time, including any later revisions.
5. What would a backtest using today's values have overstated? It would have overstated the strategy's performance by using revised information that investors wouldn't have had at the time.

