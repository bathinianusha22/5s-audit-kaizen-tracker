#!/usr/bin/env python3
"""5S Audit & Kaizen Improvement Tracker.

A command-line tool for running a factory 5S audit program and tracking
kaizen (continuous-improvement) suggestions across production zones.

The five 5S pillars scored in every audit are:
    Sort, Set in Order, Shine, Standardize, Sustain

Each audit scores three checkpoints per pillar on a 0-5 scale. Zone
averages below 3.0 are flagged as red zones. The kaizen log records
improvement suggestions, their owners, status, and estimated annual
savings, so the audit program can show whether improvement actions are
actually moving the scores.

All data is SYNTHETIC, generated with a fixed seed for reproducibility.
Nothing here comes from any real employer.

Usage:
    python five_s.py --generate   create the synthetic data in data/
    python five_s.py --audit      score audits, save charts, write the report
    python five_s.py --kaizen     print the kaizen summary table

Running --audit without data generates the data first, so a fresh
checkout works with a single command.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: save figures, never open a window
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEED = 42
BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
OUT_DIR = BASE / "outputs"

WEEKS = 12
START_DATE = pd.Timestamp("2026-08-24")  # a Monday; 12 audit weeks
RED_THRESHOLD = 3.0

CATEGORIES = ["Sort", "Set in Order", "Shine", "Standardize", "Sustain"]

# Three observable checkpoints per 5S pillar, as an auditor would score them.
CHECKPOINTS = {
    "Sort": [
        "Unneeded items removed from workstations",
        "Red-tag holding area maintained",
        "Obsolete materials dispositioned on time",
    ],
    "Set in Order": [
        "Tools shadow-boarded and labeled",
        "Materials have marked home locations",
        "Walkways clear and marked",
    ],
    "Shine": [
        "Floors and equipment cleaned per schedule",
        "Cleaning supplies stocked at point of use",
        "Leaks and spills addressed same shift",
    ],
    "Standardize": [
        "Visual standards posted at the line",
        "Checklists current and followed",
        "Shift handover log complete",
    ],
    "Sustain": [
        "Audit findings closed on time",
        "Team participates in weekly 5S huddles",
        "5S board updated weekly",
    ],
}

# Zone profiles: (base score, first week of the improvement ramp, ramp/week).
# Line 1 improves strongly after kaizen actions land in week 6, Line 2
# improves modestly, Warehouse & Stores stays red all 12 weeks.
ZONES = {
    "Line 1 - Assembly": (3.05, 6, 0.24),
    "Line 2 - Assembly": (3.30, 7, 0.10),
    "Line 3 - Packaging": (3.45, None, 0.00),
    "Quality Lab": (3.80, None, 0.00),
    "Warehouse & Stores": (2.55, None, -0.02),
    "Maintenance Bay": (3.10, 8, 0.08),
}

# Pillar offsets: Sustain is the hardest pillar to hold, Shine the easiest.
CATEGORY_OFFSET = {
    "Sort": -0.10,
    "Set in Order": 0.00,
    "Shine": 0.20,
    "Standardize": -0.05,
    "Sustain": -0.25,
}

# Warehouse & Stores is weak on the two pillars that need follow-through.
WEAK_ZONE_EXTRA = {"Standardize": -0.15, "Sustain": -0.15}

AUDITORS = ["A. Chen", "M. Ortiz", "J. Patel", "S. Novak"]
OWNERS = ["R. Diaz", "K. Meyer", "T. Brooks", "L. Fontaine", "D. Okafor",
          "P. Raman", "H. Schultz", "E. Vargas"]

# Kaizen idea templates per pillar: (title template, savings range in $).
KAIZEN_IDEAS = {
    "Sort": [
        ("Red-tag sweep and removal of obsolete fixtures at {zone}", (800, 6000)),
        ("Purge expired consumables from {zone} storage", (500, 3500)),
        ("Clear unmarked WIP staging at {zone}", (1000, 7000)),
        ("Remove duplicate tooling sets from {zone}", (1200, 8000)),
    ],
    "Set in Order": [
        ("Shadow boards for torque tools at {zone}", (1500, 9000)),
        ("Floor-mark home locations for pallets at {zone}", (1000, 6000)),
        ("Label all bins and racks at {zone} with QR codes", (2000, 12000)),
        ("Tool crib re-layout to cut walk time at {zone}", (3000, 15000)),
    ],
    "Shine": [
        ("Daily 10-minute clean-down rota for {zone}", (800, 5000)),
        ("Drip trays under hydraulic stations at {zone}", (1500, 8000)),
        ("Cleaning supply stations at point of use in {zone}", (600, 4000)),
        ("Dust extraction check added to {zone} shutdown list", (2000, 10000)),
    ],
    "Standardize": [
        ("Photo work instructions for changeover at {zone}", (2500, 14000)),
        ("Standardised shift handover sheet for {zone}", (1000, 6000)),
        ("Visual standard board at {zone} entrance", (1200, 7000)),
        ("Checklist revision for {zone} startup and shutdown", (800, 5000)),
    ],
    "Sustain": [
        ("Weekly 5S huddle with rotating lead at {zone}", (1000, 6000)),
        ("Audit-finding tracker with due-date alerts for {zone}", (1500, 9000)),
        ("Monthly 5S recognition for best zone crew at {zone}", (500, 3000)),
        ("Supervisor gemba walk schedule for {zone}", (2000, 10000)),
    ],
}


# --------------------------------------------------------------------------
# Data generation
# --------------------------------------------------------------------------
def generate_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate synthetic audit and kaizen data (seeded, reproducible)."""
    rng = np.random.default_rng(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    audit_rows = []
    audit_id = 0
    for zone, (base, ramp_week, ramp) in ZONES.items():
        for week in range(1, WEEKS + 1):
            date = START_DATE + pd.Timedelta(weeks=week - 1)
            auditor = str(rng.choice(AUDITORS))
            # Improvement ramp once kaizen actions start landing.
            level = base
            if ramp_week is not None and week >= ramp_week:
                level += ramp * (week - ramp_week + 1)
            for category in CATEGORIES:
                cat_level = level + CATEGORY_OFFSET[category]
                if zone == "Warehouse & Stores":
                    cat_level += WEAK_ZONE_EXTRA.get(category, 0.0)
                for checkpoint in CHECKPOINTS[category]:
                    score = float(np.clip(
                        cat_level + rng.normal(0, 0.25), 0, 5))
                    audit_id += 1
                    audit_rows.append({
                        "audit_id": audit_id,
                        "zone": zone,
                        "week": week,
                        "date": date.date().isoformat(),
                        "auditor": auditor,
                        "category": category,
                        "checkpoint": checkpoint,
                        "score": round(score, 1),
                    })
    audits = pd.DataFrame(audit_rows)
    audits.to_csv(DATA_DIR / "audits.csv", index=False)

    # Kaizen log: 40 suggestions spread across zones and pillars.
    kaizen_rows = []
    used_titles = set()
    statuses = (["implemented"] * 16 + ["approved"] * 8
                + ["proposed"] * 10 + ["rejected"] * 6)
    rng.shuffle(statuses)
    for i, status in enumerate(statuses, start=1):
        zone = str(rng.choice(list(ZONES)))
        category = str(rng.choice(CATEGORIES))
        title_template, (lo, hi) = KAIZEN_IDEAS[category][
            int(rng.integers(0, len(KAIZEN_IDEAS[category])))]
        title = title_template.format(zone=zone)
        # Keep titles unique so the log reads like real suggestions.
        while title in used_titles:
            title = title + " (phase 2)"
        used_titles.add(title)
        savings = int(round(rng.integers(lo, hi) / 50.0) * 50)
        submitted = START_DATE + pd.Timedelta(
            days=int(rng.integers(0, WEEKS * 7)))
        days = None
        if status == "implemented":
            days = int(rng.integers(5, 46))
        kaizen_rows.append({
            "kaizen_id": f"KZ-{i:03d}",
            "idea": title,
            "zone": zone,
            "category": category,
            "estimated_annual_savings_usd": savings,
            "owner": str(rng.choice(OWNERS)),
            "status": status,
            "days_to_implement": days,
            "date_submitted": submitted.date().isoformat(),
        })
    kaizen = pd.DataFrame(kaizen_rows)
    kaizen.to_csv(DATA_DIR / "kaizen_log.csv", index=False)
    return audits, kaizen


# --------------------------------------------------------------------------
# Loading and scoring
# --------------------------------------------------------------------------
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load audit and kaizen data, generating it first if it is missing."""
    audits_path = DATA_DIR / "audits.csv"
    kaizen_path = DATA_DIR / "kaizen_log.csv"
    if not audits_path.exists() or not kaizen_path.exists():
        print("Data files not found — generating synthetic data first.")
        return generate_data()
    audits = pd.read_csv(audits_path)
    kaizen = pd.read_csv(kaizen_path)
    return audits, kaizen


def zone_weekly_scores(audits: pd.DataFrame) -> pd.DataFrame:
    """Mean score per zone per week (average across all 5 pillars)."""
    weekly = (audits.groupby(["zone", "week"])["score"]
              .mean().reset_index()
              .rename(columns={"score": "avg_score"}))
    return weekly


def zone_scores(audits: pd.DataFrame) -> pd.DataFrame:
    """Overall mean score per zone, plus first- and last-week means."""
    weekly = zone_weekly_scores(audits)
    overall = weekly.groupby("zone")["avg_score"].mean()
    first = weekly[weekly["week"] == 1].set_index("zone")["avg_score"]
    last = weekly[weekly["week"] == WEEKS].set_index("zone")["avg_score"]
    summary = pd.DataFrame({
        "overall_avg": overall,
        "week_1_avg": first,
        f"week_{WEEKS}_avg": last,
    })
    summary["change"] = summary[f"week_{WEEKS}_avg"] - summary["week_1_avg"]
    return summary.sort_values("overall_avg")


def category_scores(audits: pd.DataFrame) -> pd.DataFrame:
    """Overall mean score per 5S pillar, in pillar order."""
    cat = (audits.groupby("category")["score"].mean()
           .reindex(CATEGORIES).reset_index()
           .rename(columns={"score": "avg_score"}))
    return cat


def red_flags(audits: pd.DataFrame) -> list[str]:
    """Human-readable red flags: any zone or pillar average below 3.0."""
    flags: list[str] = []
    zs = zone_scores(audits)
    for zone, row in zs.iterrows():
        if row["overall_avg"] < RED_THRESHOLD:
            flags.append(
                f"{zone}: 12-week average {row['overall_avg']:.2f} "
                f"(below {RED_THRESHOLD:.1f})")
    latest = zone_weekly_scores(audits)
    latest = latest[latest["week"] == WEEKS]
    for _, row in latest.iterrows():
        if row["avg_score"] < RED_THRESHOLD:
            flags.append(
                f"{row['zone']}: week {WEEKS} average "
                f"{row['avg_score']:.2f} (below {RED_THRESHOLD:.1f})")
    for _, row in category_scores(audits).iterrows():
        if row["avg_score"] < RED_THRESHOLD:
            flags.append(
                f"Pillar '{row['category']}': program average "
                f"{row['avg_score']:.2f} (below {RED_THRESHOLD:.1f})")
    return sorted(set(flags))


def kaizen_summary(kaizen: pd.DataFrame) -> dict:
    """Impact numbers for the kaizen log."""
    implemented = kaizen[kaizen["status"] == "implemented"]
    savings_by_zone = (implemented.groupby("zone")
                       ["estimated_annual_savings_usd"].sum()
                       .sort_values(ascending=False))
    return {
        "total": len(kaizen),
        "by_status": kaizen["status"].value_counts().to_dict(),
        "implemented": len(implemented),
        "total_savings": int(implemented["estimated_annual_savings_usd"].sum()),
        "avg_days": (float(implemented["days_to_implement"].mean())
                     if len(implemented) else 0.0),
        "savings_by_zone": savings_by_zone,
        "top_ideas": implemented.nlargest(
            5, "estimated_annual_savings_usd"),
    }


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------
def make_charts(audits: pd.DataFrame, kaizen: pd.DataFrame) -> list[str]:
    """Save the four program charts to outputs/ and return their paths."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    weekly = zone_weekly_scores(audits)
    paths: list[str] = []

    # 1. Zone score trends over the 12 weeks.
    fig, ax = plt.subplots(figsize=(11, 6))
    for zone in ZONES:
        series = weekly[weekly["zone"] == zone].sort_values("week")
        ax.plot(series["week"], series["avg_score"],
                marker="o", linewidth=2, label=zone)
    ax.axhline(RED_THRESHOLD, color="red", linestyle="--", linewidth=1.5,
               label=f"Red-zone threshold ({RED_THRESHOLD:.1f})")
    ax.set_xlabel("Audit week")
    ax.set_ylabel("Average 5S score (0-5)")
    ax.set_title("5S audit score by zone — 12-week trend")
    ax.set_xticks(range(1, WEEKS + 1))
    ax.set_ylim(0, 5)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    path = OUT_DIR / "zone_trends.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(str(path))

    # 2. Radar chart: best vs worst zone across the five pillars.
    zs = zone_scores(audits)
    best_zone = str(zs["overall_avg"].idxmax())
    worst_zone = str(zs["overall_avg"].idxmin())
    cat_avg = (audits.groupby(["zone", "category"])["score"].mean()
               .unstack().reindex(columns=CATEGORIES))
    angles = np.linspace(0, 2 * np.pi, len(CATEGORIES), endpoint=False)
    angles = np.concatenate([angles, [angles[0]]])
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    for zone, style in ((best_zone, "-"), (worst_zone, "--")):
        values = cat_avg.loc[zone].tolist()
        values = values + [values[0]]
        ax.plot(angles, values, style, linewidth=2,
                label=f"{zone} (avg {zs.loc[zone, 'overall_avg']:.2f})")
        ax.fill(angles, values, alpha=0.08)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(CATEGORIES)
    ax.set_ylim(0, 5)
    ax.set_title(f"5S pillar profile — best vs worst zone\n"
                 f"{best_zone} vs {worst_zone}", pad=24)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)
    fig.tight_layout()
    path = OUT_DIR / "radar_best_vs_worst.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(str(path))

    # 3. Category averages across all zones.
    cat = category_scores(audits)
    colors = ["#c0392b" if v < RED_THRESHOLD else "#2e86ab"
              for v in cat["avg_score"]]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(cat["category"], cat["avg_score"], color=colors)
    ax.axhline(RED_THRESHOLD, color="red", linestyle="--", linewidth=1.5,
               label=f"Red-zone threshold ({RED_THRESHOLD:.1f})")
    ax.set_ylabel("Average score (0-5)")
    ax.set_title("Average score by 5S pillar — all zones, 12 weeks")
    ax.set_ylim(0, 5)
    for bar, value in zip(ax.patches, cat["avg_score"]):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.12,
                f"{value:.2f}", ha="center", fontsize=10)
    ax.legend()
    fig.tight_layout()
    path = OUT_DIR / "category_averages.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(str(path))

    # 4. Kaizen savings from implemented ideas, by zone.
    summary = kaizen_summary(kaizen)
    savings = summary["savings_by_zone"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(savings.index, savings.values / 1000, color="#27ae60")
    ax.set_ylabel("Estimated annual savings ($ thousands)")
    ax.set_title("Estimated annual savings from implemented kaizen — by zone")
    for bar, value in zip(ax.patches, savings.values):
        ax.text(bar.get_x() + bar.get_width() / 2, value / 1000 + 0.4,
                f"${value:,.0f}", ha="center", fontsize=9)
    ax.tick_params(axis="x", labelrotation=20)
    fig.tight_layout()
    path = OUT_DIR / "kaizen_savings_by_zone.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(str(path))
    return paths


# --------------------------------------------------------------------------
# Tableau extract and report
# --------------------------------------------------------------------------
def write_tableau_extract(audits: pd.DataFrame) -> str:
    """Tidy zone-week-pillar extract, ready to import into Tableau."""
    extract = (audits.groupby(["zone", "week", "date", "category", "auditor"])
               .agg(avg_score=("score", "mean"),
                    checkpoints=("score", "size"))
               .reset_index())
    extract["avg_score"] = extract["avg_score"].round(2)
    extract["red_flag"] = extract["avg_score"] < RED_THRESHOLD
    extract = extract.sort_values(["week", "zone", "category"])
    path = OUT_DIR / "tableau_5s_audit_extract.csv"
    extract.to_csv(path, index=False)
    return str(path)


def write_report(audits: pd.DataFrame, kaizen: pd.DataFrame,
                 chart_paths: list[str], extract_path: str) -> str:
    """Write the audit summary report to outputs/audit_report.md."""
    zs = zone_scores(audits)
    cat = category_scores(audits)
    flags = red_flags(audits)
    summary = kaizen_summary(kaizen)
    overall = float(audits["score"].mean())

    lines = [
        "# 5S Audit & Kaizen Report — 12-Week Program",
        "",
        "Synthetic data (seed 42). 6 production zones, 12 weekly audits, "
        "3 checkpoints per 5S pillar scored 0-5, plus a 40-item kaizen log.",
        "",
        "## Program summary",
        "",
        f"- Audits completed: {len(audits) // (len(CATEGORIES) * 3)} "
        f"zone-weeks ({len(audits)} checkpoint scores)",
        f"- Overall average score: **{overall:.2f} / 5**",
        f"- Zones at or above {RED_THRESHOLD:.1f}: "
        f"{int((zs['overall_avg'] >= RED_THRESHOLD).sum())} of {len(zs)}",
        f"- Kaizen ideas logged: {summary['total']} "
        f"({summary['implemented']} implemented)",
        "",
        "## Zone averages (12-week overall)",
        "",
        "| Zone | Overall | Week 1 | Week 12 | Change |",
        "|---|---:|---:|---:|---:|",
    ]
    for zone, row in zs.sort_values("overall_avg", ascending=False).iterrows():
        lines.append(
            f"| {zone} | {row['overall_avg']:.2f} | {row['week_1_avg']:.2f} | "
            f"{row[f'week_{WEEKS}_avg']:.2f} | {row['change']:+.2f} |")
    lines += [
        "",
        "## Red-zone flags (average below 3.0)",
        "",
    ]
    if flags:
        lines += [f"- {flag}" for flag in flags]
    else:
        lines.append("- None — every zone and pillar is at or above 3.0.")
    lines += [
        "",
        "## Pillar averages (all zones)",
        "",
        "| Pillar | Average |",
        "|---|---:|",
    ]
    for _, row in cat.iterrows():
        lines.append(f"| {row['category']} | {row['avg_score']:.2f} |")
    lines += [
        "",
        "## Kaizen impact",
        "",
        f"- Implemented: **{summary['implemented']} of {summary['total']}** "
        f"ideas",
        f"- Total estimated annual savings (implemented): "
        f"**${summary['total_savings']:,}**",
        f"- Average days to implement: **{summary['avg_days']:.1f} days**",
        "",
        "### Savings by zone (implemented ideas)",
        "",
        "| Zone | Estimated annual savings |",
        "|---|---:|",
    ]
    for zone, value in summary["savings_by_zone"].items():
        lines.append(f"| {zone} | ${value:,} |")
    lines += [
        "",
        "### Top 5 implemented ideas by savings",
        "",
        "| Idea | Zone | Savings | Days to implement |",
        "|---|---|---:|---:|",
    ]
    for _, row in summary["top_ideas"].iterrows():
        lines.append(
            f"| {row['idea']} | {row['zone']} | "
            f"${row['estimated_annual_savings_usd']:,} | "
            f"{int(row['days_to_implement'])} |")
    lines += [
        "",
        "## Recommendations",
        "",
        "1. Focus the next audit cycle on Warehouse & Stores: it is the "
        "only zone below 3.0, weakest on Standardize and Sustain. Pair a "
        "supervisor gemba walk with the open Standardize kaizen actions.",
        "2. Protect the gains on Line 1 - Assembly: its improvement "
        "followed implemented kaizen actions. Keep the weekly huddle and "
        "re-audit the new shadow boards before the next cycle.",
        "3. Sustain is the weakest pillar program-wide. Make the weekly "
        "5S huddle and the audit-finding tracker standard work in every "
        "zone, not just the improving ones.",
        "4. Convert the "
        f"{summary['by_status'].get('approved', 0)} approved ideas into "
        "implementation plans with owners and due dates before logging "
        "new suggestions, so the log does not grow faster than the team "
        "can implement.",
        "",
        "## Files",
        "",
        *[f"- {Path(p).name}" for p in chart_paths],
        f"- {Path(extract_path).name} — tidy extract for Tableau "
        "(one row per zone-week-pillar)",
        "",
        "_All data in this report is synthetic and was generated for "
        "portfolio demonstration only._",
        "",
    ]
    path = OUT_DIR / "audit_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def print_kaizen_table(kaizen: pd.DataFrame) -> None:
    """Print the kaizen summary table to stdout."""
    summary = kaizen_summary(kaizen)
    print("Kaizen improvement log — summary")
    print(f"Total ideas logged: {summary['total']}")
    print("By status:")
    for status in ["implemented", "approved", "proposed", "rejected"]:
        print(f"  {status:<12} {summary['by_status'].get(status, 0)}")
    print(f"Implemented: {summary['implemented']}")
    print(f"Total estimated annual savings (implemented): "
          f"${summary['total_savings']:,}")
    print(f"Average days to implement: {summary['avg_days']:.1f}")
    print("\nEstimated savings by zone (implemented ideas):")
    print(f"{'Zone':<24} {'Savings':>12}")
    for zone, value in summary["savings_by_zone"].items():
        print(f"{zone:<24} ${value:>11,}")
    print("\nTop 5 implemented ideas:")
    for _, row in summary["top_ideas"].iterrows():
        print(f"  - {row['idea']} [{row['zone']}] "
              f"${row['estimated_annual_savings_usd']:,} "
              f"({int(row['days_to_implement'])} days)")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="5S Audit & Kaizen Improvement Tracker "
                    "(synthetic factory data)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--generate", action="store_true",
                       help="create the synthetic data in data/")
    group.add_argument("--audit", action="store_true",
                       help="score audits, save charts, write the report")
    group.add_argument("--kaizen", action="store_true",
                       help="print the kaizen summary table")
    args = parser.parse_args(argv)

    if args.generate:
        audits, kaizen = generate_data()
        print(f"Generated {len(audits)} checkpoint scores "
              f"({len(audits) // (len(CATEGORIES) * 3)} zone-weeks) "
              f"in {DATA_DIR / 'audits.csv'}")
        print(f"Generated {len(kaizen)} kaizen suggestions "
              f"in {DATA_DIR / 'kaizen_log.csv'}")
        return 0

    audits, kaizen = load_data()

    if args.audit:
        chart_paths = make_charts(audits, kaizen)
        extract_path = write_tableau_extract(audits)
        report_path = write_report(audits, kaizen, chart_paths, extract_path)
        zs = zone_scores(audits)
        summary = kaizen_summary(kaizen)
        print(f"Overall 5S average: {audits['score'].mean():.2f} / 5")
        print(f"Best zone: {zs['overall_avg'].idxmax()} "
              f"({zs['overall_avg'].max():.2f})")
        print(f"Worst zone: {zs['overall_avg'].idxmin()} "
              f"({zs['overall_avg'].min():.2f})")
        print(f"Red flags: {len(red_flags(audits))}")
        print(f"Kaizen implemented: {summary['implemented']} of "
              f"{summary['total']} "
              f"(${summary['total_savings']:,} estimated savings)")
        for path in chart_paths:
            print(f"  chart: {path}")
        print(f"  tableau extract: {extract_path}")
        print(f"  report: {report_path}")
        return 0

    if args.kaizen:
        print_kaizen_table(kaizen)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
