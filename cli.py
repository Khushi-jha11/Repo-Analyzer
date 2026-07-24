"""
Command-line interface for the GitHub Repository Analyzer.

Usage:
    python -m repo_analyzer facebook/react
    python -m repo_analyzer https://github.com/facebook/react --format markdown
    python -m repo_analyzer facebook/react --format json --output report.json
    python -m repo_analyzer facebook/react --charts --charts-dir ./charts
"""

from __future__ import annotations

import argparse
import sys

from .analyzer import GitHubAPIError, GitHubRepoAnalyzer, parse_repo_spec
from .report import render_console, render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-analyzer",
        description="Analyze a public (or accessible private) GitHub repository: "
        "stars, languages, contributors, commit activity, issues, and more.",
    )
    parser.add_argument(
        "repo",
        help="Repository as 'owner/name' or a full GitHub URL (e.g. facebook/react)",
    )
    parser.add_argument(
        "--format",
        choices=["console", "markdown", "json"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write the report to this file instead of stdout",
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (overrides GITHUB_TOKEN env var). "
        "Recommended to avoid low unauthenticated rate limits.",
    )
    parser.add_argument(
        "--charts",
        action="store_true",
        help="Also generate PNG charts (languages, commit activity, contributors). "
        "Requires matplotlib.",
    )
    parser.add_argument(
        "--charts-dir",
        default="./charts",
        help="Directory to save charts into (default: ./charts)",
    )
    parser.add_argument(
        "--skip-commit-activity",
        action="store_true",
        help="Skip the (sometimes slow) weekly commit activity fetch",
    )
    parser.add_argument(
        "--skip-code-frequency",
        action="store_true",
        help="Skip the (sometimes slow) code frequency fetch",
    )
    parser.add_argument(
        "--skip-issue-labels",
        action="store_true",
        help="Skip fetching top open-issue labels",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        owner, name = parse_repo_spec(args.repo)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    analyzer = GitHubRepoAnalyzer(owner=owner, name=name, token=args.token)

    try:
        print(f"Analyzing {owner}/{name}...", file=sys.stderr)
        report = analyzer.analyze(
            include_commit_activity=not args.skip_commit_activity,
            include_code_frequency=not args.skip_code_frequency,
            include_issue_labels=not args.skip_issue_labels,
        )
    except GitHubAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    renderers = {
        "console": render_console,
        "markdown": render_markdown,
        "json": render_json,
    }
    output_text = renderers[args.format](report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output_text)

    if args.charts:
        from .charts import generate_charts

        try:
            paths = generate_charts(report, args.charts_dir)
            print(f"Charts saved: {', '.join(paths)}", file=sys.stderr)
        except RuntimeError as exc:
            print(f"Warning: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
