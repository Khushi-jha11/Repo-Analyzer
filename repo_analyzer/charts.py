"""
Optional chart generation for a RepoReport. Requires matplotlib.

Kept separate from report.py so the rest of the tool works fine even if
matplotlib isn't installed (charts are an opt-in --charts flag).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from .analyzer import RepoReport


def generate_charts(report: RepoReport, output_dir: str) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required for --charts. Install it with: pip install matplotlib"
        ) from exc

    os.makedirs(output_dir, exist_ok=True)
    saved_files = []

    # 1. Language breakdown pie chart
    if report.language_percentages:
        fig, ax = plt.subplots(figsize=(6, 6))
        langs = sorted(report.language_percentages.items(), key=lambda kv: kv[1], reverse=True)
        labels = [l for l, _ in langs]
        sizes = [p for _, p in langs]
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title(f"Language breakdown — {report.full_name}")
        path = os.path.join(output_dir, "languages.png")
        fig.savefig(path, bbox_inches="tight", dpi=150)
        plt.close(fig)
        saved_files.append(path)

    # 2. Weekly commit activity bar chart
    if report.commit_activity:
        weeks = [datetime.fromtimestamp(w["week"], tz=timezone.utc) for w in report.commit_activity]
        totals = [w.get("total", 0) for w in report.commit_activity]
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(weeks, totals, width=5, color="#3b82f6")
        ax.set_title(f"Weekly commit activity — {report.full_name}")
        ax.set_ylabel("Commits")
        fig.autofmt_xdate()
        path = os.path.join(output_dir, "commit_activity.png")
        fig.savefig(path, bbox_inches="tight", dpi=150)
        plt.close(fig)
        saved_files.append(path)

    # 3. Contributor leaderboard bar chart
    if report.contributors:
        names = [c["login"] for c in report.contributors]
        contributions = [c["contributions"] for c in report.contributors]
        fig, ax = plt.subplots(figsize=(8, max(3, len(names) * 0.4)))
        ax.barh(names[::-1], contributions[::-1], color="#22c55e")
        ax.set_title(f"Top contributors — {report.full_name}")
        ax.set_xlabel("Commits")
        path = os.path.join(output_dir, "contributors.png")
        fig.savefig(path, bbox_inches="tight", dpi=150)
        plt.close(fig)
        saved_files.append(path)

    return saved_files
