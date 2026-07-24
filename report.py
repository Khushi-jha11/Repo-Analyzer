"""
Rendering of RepoReport objects into console output, Markdown, or JSON.
"""

from __future__ import annotations

import json
from datetime import datetime

from .analyzer import RepoReport

BAR_WIDTH = 30


def _bar(pct: float, width: int = BAR_WIDTH) -> str:
    filled = round(width * pct / 100)
    return "#" * filled + "-" * (width - filled)


def _fmt_date(iso_str: str | None) -> str:
    if not iso_str:
        return "unknown"
    try:
        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return iso_str


def render_console(report: RepoReport) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append(f" {report.full_name} ")
    if report.description:
        lines.append(f" {report.description}")
    lines.append("=" * 60)

    lines.append(
        f"Stars: {report.stars:,}   Forks: {report.forks:,}   "
        f"Watchers: {report.watchers:,}   Open issues: {report.open_issues:,}   "
        f"Open PRs: {report.open_pull_requests:,}"
    )
    lines.append(
        f"License: {report.license or 'none'}   Default branch: {report.default_branch}   "
        f"Size: {report.size_kb:,} KB   Archived: {report.is_archived}"
    )
    lines.append(
        f"Created: {_fmt_date(report.created_at)}   "
        f"Last push: {_fmt_date(report.pushed_at)}"
    )

    lines.append("\nLanguages:")
    for lang, pct in sorted(report.language_percentages.items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"  {lang:<18} {_bar(pct)} {pct:>5.1f}%")

    if report.contributors:
        lines.append("\nTop contributors:")
        for c in report.contributors:
            lines.append(f"  {c['login']:<20} {c['contributions']:,} commits")

    if report.commit_activity:
        lines.append(
            f"\nActivity (last ~52 weeks): {report.total_commits_last_year():,} commits, "
            f"+{report.total_additions_last_year():,} / -{report.total_deletions_last_year():,} lines"
        )

    if report.top_issue_labels:
        lines.append("\nTop open-issue labels:")
        for label, count in report.top_issue_labels.items():
            lines.append(f"  {label:<20} {count}")

    if report.recent_commits:
        lines.append("\nRecent commits:")
        for c in report.recent_commits:
            lines.append(f"  {c['sha']}  {c['message']}  ({c['author']}, {_fmt_date(c['date'])})")

    lines.append("=" * 60)
    return "\n".join(lines)


def render_markdown(report: RepoReport) -> str:
    lines = []
    lines.append(f"# {report.full_name}")
    if report.description:
        lines.append(f"\n> {report.description}\n")

    lines.append("## Overview\n")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Stars | {report.stars:,} |")
    lines.append(f"| Forks | {report.forks:,} |")
    lines.append(f"| Watchers | {report.watchers:,} |")
    lines.append(f"| Open issues | {report.open_issues:,} |")
    lines.append(f"| Open pull requests | {report.open_pull_requests:,} |")
    lines.append(f"| License | {report.license or 'none'} |")
    lines.append(f"| Default branch | {report.default_branch} |")
    lines.append(f"| Size | {report.size_kb:,} KB |")
    lines.append(f"| Created | {_fmt_date(report.created_at)} |")
    lines.append(f"| Last push | {_fmt_date(report.pushed_at)} |")
    lines.append(f"| Archived | {report.is_archived} |")

    if report.language_percentages:
        lines.append("\n## Languages\n")
        lines.append("| Language | Share |")
        lines.append("|---|---|")
        for lang, pct in sorted(report.language_percentages.items(), key=lambda kv: kv[1], reverse=True):
            lines.append(f"| {lang} | {pct:.1f}% |")

    if report.contributors:
        lines.append("\n## Top contributors\n")
        lines.append("| Contributor | Commits |")
        lines.append("|---|---|")
        for c in report.contributors:
            lines.append(f"| {c['login']} | {c['contributions']:,} |")

    if report.commit_activity:
        lines.append("\n## Activity (last ~52 weeks)\n")
        lines.append(f"- Total commits: {report.total_commits_last_year():,}")
        lines.append(f"- Lines added: {report.total_additions_last_year():,}")
        lines.append(f"- Lines deleted: {report.total_deletions_last_year():,}")

    if report.top_issue_labels:
        lines.append("\n## Top open-issue labels\n")
        lines.append("| Label | Count |")
        lines.append("|---|---|")
        for label, count in report.top_issue_labels.items():
            lines.append(f"| {label} | {count} |")

    if report.recent_commits:
        lines.append("\n## Recent commits\n")
        for c in report.recent_commits:
            lines.append(f"- `{c['sha']}` {c['message']} — *{c['author']}, {_fmt_date(c['date'])}*")

    return "\n".join(lines)


def render_json(report: RepoReport) -> str:
    return json.dumps(report.to_dict(), indent=2, default=str)
