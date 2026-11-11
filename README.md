# 5S Audit & Kaizen Improvement Tracker

A command-line tool that runs a factory 5S audit program and tracks
kaizen (continuous-improvement) suggestions across production zones.
It scores the five 5S pillars — Sort, Set in Order, Shine,
Standardize, Sustain — flags red zones, and shows whether improvement
actions are actually moving the scores.

## Why this matters for process-technician roles

The Tesla NCM Process Technician posting (Buffalo, NY) and similar
process-technician roles at other manufacturers call out Lean
Manufacturing, continuous improvement, and 5S initiatives, plus
record-keeping and summarizing process data. This project is a working
version of that job: running weekly 5S audits, keeping the records,
spotting the zone that stays red, and tying kaizen actions to
measurable score changes and estimated savings.

It applies to any manufacturer, not just Tesla — 5S auditing and
kaizen tracking work the same way on any production floor.

| Job requirement | How this project shows it |
|---|---|
| Support Lean Manufacturing, continuous improvement, 5S | Full 12-week 5S audit program with pillar scores and red-zone flags |
| Summarize and analyze process data | Zone trends, pillar averages, kaizen impact summary, written report |
| Detail-oriented record-keeping | Every audit is a dated, auditor-signed checkpoint record in CSV/SQL-ready form |
| Data tools (Tableau, SQL) | Tidy `tableau_5s_audit_extract.csv` built for direct Tableau import |
| Small cross-functional projects | Kaizen log with owners, statuses, savings, and days to implement |

## Features

- Synthetic 5S audit data: 6 production zones x 12 weeks x 5 pillars x
  3 checkpoints per pillar (1,080 checkpoint scores), seeded and
  reproducible
- Zone and pillar scoring with a red-zone threshold (average below 3.0)
- Kaizen log: 40 suggestions with zone, pillar, estimated annual
  savings, owner, status, and days to implement
- Four charts: zone score trends, best-vs-worst zone radar, pillar
  averages, kaizen savings by zone
- Markdown audit report with zone tables, red flags, kaizen impact,
  and recommendations
- Tableau-ready tidy extract: one row per zone-week-pillar

## Tech stack

- Python 3.10+
- pandas, NumPy, matplotlib
- CSV data files, no database required

## Project structure

```text
5s-audit-kaizen-tracker/
├── five_s.py                 # the whole tool: generate, audit, kaizen
├── requirements.txt
├── README.md
├── data/
│   ├── audits.csv            # 1,080 checkpoint scores (generated)
│   └── kaizen_log.csv        # 40 kaizen suggestions (generated)
└── outputs/
    ├── zone_trends.png
    ├── radar_best_vs_worst.png
    ├── category_averages.png
    ├── kaizen_savings_by_zone.png
    ├── audit_report.md
    └── tableau_5s_audit_extract.csv
```

## How to run

```bash
pip install -r requirements.txt

# 1. Create the synthetic data
python five_s.py --generate

# 2. Score the audits, save charts, write the report
python five_s.py --audit

# 3. Print the kaizen summary table
python five_s.py --kaizen
```

Running `--audit` without data generates it first, so a fresh checkout
works with a single `python five_s.py --audit` command.

## Sample results

From the included run (seed 42, 12 weeks, 6 zones):

- **Overall 5S average: 3.29 / 5**; 5 of 6 zones at or above the 3.0
  threshold
- **Line 1 - Assembly improved the most: 2.99 in week 1 to 4.75 in
  week 12 (+1.76)**, after kaizen actions landed from week 6
- **Warehouse & Stores stayed red all 12 weeks: 2.45 overall**,
  weakest on Standardize and Sustain — the report's top action item
- **Weakest pillar program-wide: Sustain (3.10)**; strongest: Shine
  (3.54)
- **Kaizen: 16 of 40 ideas implemented, $67,850 estimated annual
  savings, 21.9 days average to implement**
- Largest single saving: tool crib re-layout at Quality Lab,
  $12,600/year

## Synthetic data disclaimer

All data in this repository is synthetic, generated with a fixed seed
for portfolio demonstration. It does not come from Tesla or any real
employer, and no real audit scores, employee names, or savings figures
are used.
